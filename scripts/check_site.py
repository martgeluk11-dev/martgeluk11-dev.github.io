from html.parser import HTMLParser
from pathlib import Path
import json
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "index.html", "about.html", "security.html", "privacy.html",
    "contact.html", "downloads.html", "docs.html", "status.html",
    "robots.txt", "sitemap.xml", "llms.txt", ".well-known/security.txt",
]

class JsonLdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_jsonld = False
        self.parts = []
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self.in_jsonld = True
            self.parts = []

    def handle_data(self, data):
        if self.in_jsonld:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.in_jsonld:
            self.blocks.append("".join(self.parts))
            self.in_jsonld = False

errors = []
for name in REQUIRED:
    if not (ROOT / name).is_file():
        errors.append(f"Missing required file: {name}")

index_path = ROOT / "index.html"
if index_path.exists():
    parser = JsonLdParser()
    parser.feed(index_path.read_text(encoding="utf-8"))
    if not parser.blocks:
        errors.append("Homepage is missing JSON-LD structured data.")
    for block in parser.blocks:
        try:
            json.loads(block)
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid JSON-LD: {exc}")

sitemap_path = ROOT / "sitemap.xml"
if sitemap_path.exists():
    try:
        root = ET.parse(sitemap_path).getroot()
        locs = [node.text or "" for node in root.iter() if node.tag.endswith("loc")]
        for loc in locs:
            path = loc.removeprefix("https://martgeluk11-dev.github.io/") or "index.html"
            if not (ROOT / path).is_file():
                errors.append(f"Sitemap points to missing file: {path}")
        if any("changelog.html" in loc for loc in locs):
            errors.append("Removed changelog is still listed in the sitemap.")
    except ET.ParseError as exc:
        errors.append(f"Invalid sitemap XML: {exc}")

robots = ROOT / "robots.txt"
if robots.exists() and "https://martgeluk11-dev.github.io/sitemap.xml" not in robots.read_text(encoding="utf-8"):
    errors.append("robots.txt does not reference the sitemap.")

if (ROOT / "changelog.html").exists():
    errors.append("changelog.html should have been removed.")

if errors:
    print("\n".join(f"ERROR: {item}" for item in errors))
    sys.exit(1)

print(f"EXEcify site checks passed ({len(REQUIRED)} required files, sitemap and JSON-LD).")
