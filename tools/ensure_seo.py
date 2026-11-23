#!/usr/bin/env python3
"""Re-apply Cyberpunk TCG meta SEO into index.html after a dashboard publish.

Idempotent: safe to run on an already-SEO'd file or a fresh dashboard.html copy.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FRAGMENT_PATH = REPO_ROOT / "seo" / "head.fragment.html"
INDEX_PATH = REPO_ROOT / "index.html"
ROBOTS_PATH = REPO_ROOT / "robots.txt"
SITEMAP_PATH = REPO_ROOT / "sitemap.xml"

PAGE_TITLE = "Cyberpunk TCG Meta"
DOC_TITLE = "Cyberpunk TCG Meta — Night City Showdowns Tier List & Matchups"
CANONICAL = "https://nikiva-dev.github.io/night-city-meta/"

SEO_START = "<!-- night-city-meta:seo-start -->"
SEO_END = "<!-- night-city-meta:seo-end -->"

# Titles the generator commonly emits for the overall view / document title.
WIPE_TITLES = (
    "World meta — all weeks",
    "World meta - all weeks",
    "World meta",
)

ROBOTS_TXT = f"""User-agent: *
Allow: /

Sitemap: {CANONICAL}sitemap.xml
"""

SITEMAP_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{CANONICAL}</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
"""


def _load_fragment() -> str:
    text = FRAGMENT_PATH.read_text(encoding="utf-8").strip() + "\n"
    if SEO_START not in text or SEO_END not in text:
        raise SystemExit(f"SEO fragment missing markers: {FRAGMENT_PATH}")
    return text


def _strip_existing_seo_tags(head: str) -> str:
    """Remove prior SEO tags so a fresh dashboard copy can be re-tagged cleanly."""
    patterns = [
        r"<title\b[^>]*>[\s\S]*?</title>\s*",
        r'<meta\s+name="description"[^>]*>\s*',
        r'<meta\s+name="robots"[^>]*>\s*',
        r'<link\s+rel="canonical"[^>]*>\s*',
        r'<meta\s+property="og:[^"]+"[^>]*>\s*',
        r'<meta\s+name="twitter:[^"]+"[^>]*>\s*',
        r'<script\s+type="application/ld\+json">[\s\S]*?</script>\s*',
    ]
    for pat in patterns:
        head = re.sub(pat, "", head, flags=re.I)
    # Drop a previous marked block if somehow nested oddly.
    head = re.sub(
        re.escape(SEO_START) + r"[\s\S]*?" + re.escape(SEO_END) + r"\s*",
        "",
        head,
    )
    return head


def inject_head(html: str, fragment: str) -> str:
    if SEO_START in html and SEO_END in html:
        html = re.sub(
            re.escape(SEO_START) + r"[\s\S]*?" + re.escape(SEO_END) + r"\n?",
            fragment,
            html,
            count=1,
        )
        return html

    m = re.search(r"<head\b[^>]*>", html, flags=re.I)
    if not m:
        raise SystemExit("index.html has no <head>")

    head_open_end = m.end()
    head_close = re.search(r"</head>", html[head_open_end:], flags=re.I)
    if not head_close:
        raise SystemExit("index.html has no </head>")

    head_inner_start = head_open_end
    head_inner_end = head_open_end + head_close.start()
    head_inner = html[head_inner_start:head_inner_end]
    cleaned = _strip_existing_seo_tags(head_inner)

    # Prefer inserting after charset + viewport when present.
    insert_at = 0
    for pat in (
        r'<meta\s+charset="[^"]*"\s*/?>\s*',
        r'<meta\s+name="viewport"[^>]*>\s*',
    ):
        mm = re.match(pat, cleaned[insert_at:], flags=re.I)
        if mm:
            insert_at += mm.end()

    new_inner = cleaned[:insert_at] + fragment + cleaned[insert_at:]
    return html[:head_inner_start] + new_inner + html[head_inner_end:]


def fix_page_title_h1(html: str) -> str:
    updated, n = re.subn(
        r'(<h1\b[^>]*\bid=["\']page-title["\'][^>]*>)(.*?)(</h1>)',
        lambda m: f"{m.group(1)}{PAGE_TITLE}{m.group(3)}",
        html,
        count=1,
        flags=re.I | re.S,
    )
    if n:
        return updated

    # Fallback: first h1 only when it still carries a wipe title.
    def h1_repl(m: re.Match[str]) -> str:
        inner = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if inner in WIPE_TITLES or inner.startswith("World meta"):
            return f"{m.group(1)}{PAGE_TITLE}{m.group(3)}"
        return m.group(0)

    return re.sub(r"(<h1\b[^>]*>)(.*?)(</h1>)", h1_repl, html, count=1, flags=re.I | re.S)


def fix_overall_view_title(html: str) -> str:
    """Keep VIEWS.overall.title on the SEO H1 after generator republish."""
    # "overall": {"title": "World meta — all weeks", ...
    pattern = (
        r'("overall"\s*:\s*\{\s*"title"\s*:\s*")'
        r'(?:World meta(?:\s*[—\-]\s*all weeks)?|Welcome to Night City,?\s*all weeks?)'
        r'(")'
    )
    html, n = re.subn(pattern, rf"\1{PAGE_TITLE}\2", html, count=1)
    if n:
        return html

    # Broader: if overall title is not already PAGE_TITLE, force it when it looks like a wipe.
    def overall_repl(m: re.Match[str]) -> str:
        current = m.group(2)
        if current == PAGE_TITLE:
            return m.group(0)
        if current in WIPE_TITLES or current.startswith("World meta"):
            return f"{m.group(1)}{PAGE_TITLE}{m.group(3)}"
        return m.group(0)

    return re.sub(
        r'("overall"\s*:\s*\{\s*"title"\s*:\s*")([^"]+)(")',
        overall_repl,
        html,
        count=1,
    )


def ensure_robots_and_sitemap() -> list[str]:
    changed: list[str] = []
    if (not ROBOTS_PATH.exists()) or ROBOTS_PATH.read_text(encoding="utf-8") != ROBOTS_TXT:
        ROBOTS_PATH.write_text(ROBOTS_TXT, encoding="utf-8")
        changed.append(str(ROBOTS_PATH.relative_to(REPO_ROOT)))
    if (not SITEMAP_PATH.exists()) or SITEMAP_PATH.read_text(encoding="utf-8") != SITEMAP_XML:
        SITEMAP_PATH.write_text(SITEMAP_XML, encoding="utf-8")
        changed.append(str(SITEMAP_PATH.relative_to(REPO_ROOT)))
    return changed


def ensure_seo(index_path: Path = INDEX_PATH, *, dry_run: bool = False) -> bool:
    if not index_path.exists():
        raise SystemExit(f"missing {index_path}")

    fragment = _load_fragment()
    original = index_path.read_text(encoding="utf-8")
    html = original
    html = inject_head(html, fragment)
    html = fix_page_title_h1(html)
    html = fix_overall_view_title(html)

    changed = html != original
    if changed and not dry_run:
        index_path.write_text(html, encoding="utf-8")

    side = ensure_robots_and_sitemap() if not dry_run else []
    return changed or bool(side)


def _self_test() -> None:
    fragment = _load_fragment()
    wiped = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>World meta — all weeks</title>
<script>/* plotly */</script>
</head>
<body>
<div class="brand">
  <div class="eyebrow">Cyberpunk TCG</div>
  <h1 id="page-title">World meta — all weeks</h1>
</div>
<script>
const VIEWS = {"overall": {"title": "World meta — all weeks", "subtitle": "x"}, "w1": {"title": "Welcome to Night City, week 1"}};
</script>
</body>
</html>
"""
    out = inject_head(wiped, fragment)
    out = fix_page_title_h1(out)
    out = fix_overall_view_title(out)
    assert DOC_TITLE.replace("—", "—") in out.replace("&amp;", "&") or "Tier List" in out
    assert SEO_START in out and SEO_END in out
    assert f'<h1 id="page-title">{PAGE_TITLE}</h1>' in out
    assert f'"overall": {{"title": "{PAGE_TITLE}"' in out
    assert "Welcome to Night City, week 1" in out  # week titles preserved
    # second pass idempotent for head markers / h1 / overall
    out2 = inject_head(out, fragment)
    out2 = fix_page_title_h1(out2)
    out2 = fix_overall_view_title(out2)
    assert out2.count(SEO_START) == 1
    assert out2.count(f'<h1 id="page-title">{PAGE_TITLE}</h1>') == 1
    print("self-test ok")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--index", type=Path, default=INDEX_PATH)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)

    if args.self_test:
        _self_test()
        return 0

    changed = ensure_seo(args.index, dry_run=args.dry_run)
    if args.dry_run:
        print("SEO would change" if changed else "SEO already applied")
        return 0 if not changed else 2
    print("SEO updated" if changed else "SEO already applied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
