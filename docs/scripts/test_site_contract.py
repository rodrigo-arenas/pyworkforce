"""Validate generated stable/development documentation and the root Pages artifact.

Build each mode into PYWORKFORCE_BUILD_ROOT/{stable,development}, and generate
the root deployment artifact there before running these focused checks.
"""

import os
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
