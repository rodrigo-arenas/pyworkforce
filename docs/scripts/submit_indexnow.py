"""Notify IndexNow of changes since the last accepted stable build."""

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

HOST = "pyworkforce.rodrigo-arenas.com"
SITE = f"https://{HOST}"
KEY_FILE = "indexnow-key.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"
SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def stable_path(url):
    parsed = urlsplit(url)
    relative = unquote(parsed.path.removeprefix("/stable/"))
    if (
        parsed.scheme != "https"
        or parsed.netloc != HOST
        or not parsed.path.startswith("/stable/")
        or parsed.query
        or parsed.fragment
        or relative.startswith("/")
        or "\\" in relative
        or any(part in (".", "..") for part in relative.split("/"))
    ):
        raise ValueError(f"Invalid stable documentation URL: {url}")
    return relative + ("index.html" if parsed.path.endswith("/") else ".html")


def sitemap_hashes(site):
    sitemap = ET.parse(site / "sitemap.xml").getroot()
    if sitemap.tag != f"{SITEMAP_NS}urlset":
        raise ValueError(f"Expected a sitemap urlset in {site}")
    hashes = {}
    for loc in sitemap.findall(f"{SITEMAP_NS}url/{SITEMAP_NS}loc"):
        url = (loc.text or "").strip()
        page = (site / stable_path(url)).resolve()
        if not page.is_relative_to(site.resolve()):
            raise ValueError(f"Stable documentation URL escapes the build: {url}")
        hashes[url] = hashlib.sha256(page.read_bytes()).hexdigest()
    if not hashes:
        raise ValueError(f"Refusing to use an empty sitemap in {site}")
    return hashes


def submit(site, root, state, *, dry_run=False):
    key = (root / KEY_FILE).read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[a-zA-Z0-9-]{8,128}", key):
        raise ValueError("Invalid IndexNow key")

    current = sitemap_hashes(site)
    previous = json.loads(state.read_text(encoding="utf-8")) if state.exists() else {}
    if not isinstance(previous, dict):
        raise ValueError("Expected an IndexNow state object")
    for url, digest in previous.items():
        stable_path(url)
        if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError(f"Invalid IndexNow state hash: {url}")
    changed = sorted(url for url in current.keys() | previous.keys() if current.get(url) != previous.get(url))
    if not changed:
        print("IndexNow: no changed stable URLs.")
        return
    if len(changed) > 10_000:
        raise ValueError("IndexNow allows at most 10,000 URLs per batch")

    key_location = f"{SITE}/{KEY_FILE}"
    payload = {"host": HOST, "key": key, "keyLocation": key_location, "urlList": changed}
    if dry_run:
        print(json.dumps(payload, indent=2))
        return

    proof = Request(key_location, headers={"Cache-Control": "no-cache"})
    with urlopen(proof, timeout=30) as response:
        if (
            response.status != 200
            or response.geturl() != key_location
            or response.read().decode("utf-8").strip() != key
        ):
            raise ValueError("Published IndexNow key does not match the deployed build")

    request = Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        if response.status not in (200, 202):
            raise ValueError(f"Unexpected IndexNow response: HTTP {response.status}")
        status = "accepted" if response.status == 200 else "received, key validation pending"
        print(f"IndexNow: {len(changed)} stable URL(s) {status} (HTTP {response.status}).")
    state.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--submit", action="store_true", help="Verify the public key and notify IndexNow")
    args = parser.parse_args()
    submit(args.site, args.root, args.state, dry_run=not args.submit)
