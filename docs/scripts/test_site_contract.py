"""Validate generated stable/development documentation and the root Pages artifact.

Build each mode into PYWORKFORCE_BUILD_ROOT/{stable,development}, and generate
the root deployment artifact there before running these focused checks.
"""

import json
import os
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import pytest

DOCS = Path(__file__).resolve().parents[1]
BUILD = Path(os.environ["PYWORKFORCE_BUILD_ROOT"])
SITE = "https://pyworkforce.rodrigo-arenas.com"
PAGES = sorted(
    path.relative_to(DOCS)
    for path in DOCS.rglob("*.md")
    if "node_modules" not in path.parts and ".vitepress" not in path.parts and path.name != "README.md"
)


class Head(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.canonicals = []
        self.robots = []
        self.refresh = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonicals.append(attrs.get("href"))
        if tag == "meta" and attrs.get("name") == "robots":
            self.robots.append(attrs.get("content"))
        if tag == "meta" and attrs.get("http-equiv") == "refresh":
            self.refresh.append(attrs.get("content"))


def page_path(source):
    relative = source.as_posix()
    return relative[:-8] if relative.endswith("index.md") else relative[:-3]


@pytest.mark.parametrize("version", ["stable", "development"])
def test_every_documentation_page_declares_its_own_host_and_version(version):
    for source in PAGES:
        html = (BUILD / version / source.with_suffix(".html")).read_text(encoding="utf-8")
        head = Head(html)
        assert head.canonicals == [f"{SITE}/{version}/{page_path(source)}"], source
        if version == "stable":
            assert not any("noindex" in robots for robots in head.robots), source


def test_development_is_crawlable_but_not_indexable():
    for source in PAGES:
        html = (BUILD / "development" / source.with_suffix(".html")).read_text(encoding="utf-8")
        assert Head(html).robots == ["noindex,follow"], source


def test_stable_home_describes_scheduling_and_links_to_first_example():
    homepage = (BUILD / "stable" / "index.html").read_text(encoding="utf-8")
    assert "<title>PyWorkforce: Shift Scheduling and Workforce Planning in Python</title>" in homepage
    assert 'name="description" content="Use PyWorkforce' in homepage
    assert re.search(r'<a\b[^>]*href="/stable/guide/quickstart"[^>]*>Run the Python quickstart</a>', homepage)


@pytest.mark.parametrize(
    ("page", "title", "summary", "original_anchor", "example_anchor"),
    [
        ("erlangc", "Erlang C in Python for Call Center Staffing", "20 scheduled agents", "erlang-c", "basic-usage"),
        ("scheduling", "Shift Scheduling in Python with OR-Tools", "Compare minimum staffing", "scheduling", "example"),
    ],
)
def test_planning_guides_advertise_their_worked_examples(page, title, summary, original_anchor, example_anchor):
    html = (BUILD / "stable" / "guide" / f"{page}.html").read_text(encoding="utf-8")
    assert f"<title>{title} | pyworkforce</title>" in html
    assert re.search(rf'<h1[^>]*id="{original_anchor}"[^>]*>{re.escape(title)}\b', html)
    description = re.search(r'name="description" content="([^"]+)"', html).group(1)
    assert summary in description
    opening = html.split("<h1", 1)[1].split("<h2", 1)[0]
    assert re.search(rf'<a\b[^>]*href="#{example_anchor}"[^>]*>[^<]+</a>', opening)
    assert f'<h2 id="{example_anchor}"' in html
    assert 'property="og:type" content="website"' in html
    assert f'property="og:title" content="{title}"' in html
    assert f'property="og:description" content="{description}"' in html
    assert f'property="og:image" content="{SITE}/stable/brand/social-preview.png"' in html
    assert (BUILD / "stable" / "brand" / "social-preview.png").is_file()


def test_sitemap_contains_stable_canonical_pages_only():
    sitemap = ET.parse(BUILD / "stable" / "sitemap.xml")
    urls = {node.text for node in sitemap.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")}
    assert urls == {f"{SITE}/stable/{page_path(source)}" for source in PAGES}
    assert not (BUILD / "development" / "sitemap.xml").exists()
    for version in ["stable", "development"]:
        assert not (BUILD / version / "README.html").exists()
        assert "noindex" in Head((BUILD / version / "404.html").read_text(encoding="utf-8")).robots[0]


def test_root_alias_advertises_absolute_stable_canonical_and_sitemap():
    root = BUILD / "root"
    head = Head((root / "index.html").read_text(encoding="utf-8"))
    assert head.canonicals == [f"{SITE}/stable/"]
    assert head.robots == ["noindex,follow"]
    robots = (root / "robots.txt").read_text(encoding="utf-8")
    assert f"Sitemap: {SITE}/stable/sitemap.xml" in robots
    rules = RobotFileParser()
    rules.parse(robots.splitlines())
    for version in ["stable", "development"]:
        for source in PAGES:
            assert rules.can_fetch("Googlebot", f"{SITE}/{version}/{page_path(source)}")


def test_legacy_scheduling_reference_reaches_the_stable_api_page():
    head = Head((BUILD / "root" / "api" / "scheduling" / "index.html").read_text(encoding="utf-8"))
    target = f"{SITE}/stable/api/scheduling"
    assert head.canonicals == [target]
    assert head.refresh == [f"0; url={target}"]
    assert head.robots == ["noindex,follow"]
    assert (BUILD / "stable" / (urlparse(target).path.removeprefix("/stable/") + ".html")).is_file()


def test_indexnow_uses_stable_sitemap_and_published_root_key(tmp_path, monkeypatch):
    import submit_indexnow

    key = (BUILD / "root" / "indexnow-key.txt").read_text(encoding="utf-8").strip()
    assert len(key) == 32 and key.isalnum()
    assert not (BUILD / "development" / "indexnow-key.txt").exists()
    submitted = []

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            pass

        def read(self):
            return key.encode()

        def geturl(self):
            return f"{SITE}/indexnow-key.txt"

    def request(request, *, timeout):
        if request.get_method() == "GET":
            assert request.full_url == f"{SITE}/indexnow-key.txt"
        else:
            assert request.full_url == "https://api.indexnow.org/indexnow"
            submitted.append(json.loads(request.data))
        return Response()

    monkeypatch.setattr(submit_indexnow, "urlopen", request)
    stable = BUILD / "stable"
    state = tmp_path / "state.json"
    submit_indexnow.submit(stable, BUILD / "root", state)
    assert submitted == [
        {
            "host": urlparse(SITE).hostname,
            "key": key,
            "keyLocation": f"{SITE}/indexnow-key.txt",
            "urlList": sorted(f"{SITE}/stable/{page_path(source)}" for source in PAGES),
        }
    ]
    initial = json.loads(state.read_text(encoding="utf-8"))
    assert sorted(initial) == submitted[0]["urlList"]
    submit_indexnow.submit(stable, BUILD / "root", state)
    assert len(submitted) == 1

    state.write_text(
        json.dumps(
            {
                **initial,
                f"{SITE}/stable/api/scheduling": "0" * 64,
                f"{SITE}/stable/removed": "1" * 64,
            }
        ),
        encoding="utf-8",
    )
    submit_indexnow.submit(stable, BUILD / "root", state)
    assert submitted[1]["urlList"] == [f"{SITE}/stable/api/scheduling", f"{SITE}/stable/removed"]
    assert json.loads(state.read_text(encoding="utf-8")) == initial


@pytest.mark.parametrize("failure", ["wrong-key", "rejected-post", "dry-run"])
def test_indexnow_preserves_state_if_no_batch_is_accepted(tmp_path, monkeypatch, failure):
    import submit_indexnow

    stable = BUILD / "stable"
    root = BUILD / "root"
    key = (root / "indexnow-key.txt").read_text(encoding="utf-8")
    state = tmp_path / "state.json"
    removed = f"{SITE}/stable/removed"
    previous = json.dumps({removed: "1" * 64})
    state.write_text(previous, encoding="utf-8")
    requests = []

    class Response:
        def __init__(self, request):
            self.url = request.full_url
            self.status = 200 if request.get_method() == "GET" else 403

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            pass

        def read(self):
            return ("mismatch" if failure == "wrong-key" else key).encode()

        def geturl(self):
            return self.url

    def request(request, *, timeout):
        requests.append(request.get_method())
        if request.get_method() == "POST":
            assert removed in json.loads(request.data)["urlList"]
        return Response(request)

    monkeypatch.setattr(submit_indexnow, "urlopen", request)
    if failure == "dry-run":
        submit_indexnow.submit(stable, root, state, dry_run=True)
        assert not requests
    else:
        with pytest.raises(ValueError, match="Published IndexNow key" if failure == "wrong-key" else "HTTP 403"):
            submit_indexnow.submit(stable, root, state)
        assert requests == (["GET"] if failure == "wrong-key" else ["GET", "POST"])
    assert state.read_text(encoding="utf-8") == previous


@pytest.mark.parametrize(
    "bad_url", ["https://example.org/stable/", f"{SITE}/development/", f"{SITE}/stable/../development/"]
)
def test_indexnow_rejects_urls_outside_stable_docs(tmp_path, monkeypatch, bad_url):
    import submit_indexnow

    sitemap = tmp_path / "sitemap.xml"
    sitemap.write_text(
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{bad_url}</loc></url></urlset>',
        encoding="utf-8",
    )
    monkeypatch.setattr(submit_indexnow, "urlopen", lambda *args, **kwargs: pytest.fail("Unexpected network request"))
    with pytest.raises(ValueError, match="Invalid stable documentation URL"):
        submit_indexnow.submit(tmp_path, BUILD / "root", tmp_path / "previous")
