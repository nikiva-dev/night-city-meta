#!/usr/bin/env python3
"""Publish the world meta dashboard into this GitHub Pages repo.

PowerShell 5.1 chokes on dated week folders (WTNC_w2_2026-11-21) when scripts
use Split-Path -LiteralPath / advanced param binding. This Python entry point
owns path resolution, copy, SEO, and optional git commit/push.

Usage (from night-city-meta root):
  python tools\\publish.py --week w2
  python tools\\publish.py --week-dir C:\\...\\WTNC_w2_2026-11-21
  python tools\\publish.py --dashboard C:\\...\\cumulative\\dashboard.html
  python tools\\publish.py --week w2 --dry-run
  python tools\\publish.py --self-test
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENSURE_SEO = Path(__file__).resolve().parent / "ensure_seo.py"
SIBLING_NAMES = ("assets", "data", "panels")
LIVE_URL = "https://nikiva-dev.github.io/night-city-meta/"
DEFAULT_TCG_ROOT = Path.home() / "Desktop" / "CyberpunkTCG"


def _tcg_root() -> Path:
    env = os.environ.get("CYBERPUNKTCG_ROOT", "").strip()
    if env:
        return Path(env)
    return DEFAULT_TCG_ROOT


def resolve_week_dir(week: str, tcg_root: Path | None = None) -> Path:
    """Resolve 'w2', '2', or a full WTNC_* folder name under WTNC/."""
    root = tcg_root or _tcg_root()
    wtnc = root / "WTNC"
    raw = week.strip()
    if not raw:
        raise SystemExit("--week is empty")

    candidate = Path(raw)
    if candidate.is_absolute() and candidate.is_dir():
        return candidate.resolve()

    # Bare folder name already under WTNC.
    named = wtnc / raw
    if named.is_dir():
        return named.resolve()

    # w2 / W2 / 2 → WTNC_w2_*
    key = raw.lower()
    if key.startswith("w") and key[1:].isdigit():
        prefix = f"WTNC_w{key[1:]}_"
    elif key.isdigit():
        prefix = f"WTNC_w{key}_"
    else:
        raise SystemExit(
            f"Cannot resolve --week {week!r}. Use w2, 2, or a WTNC folder name."
        )

    matches = sorted(p for p in wtnc.glob(prefix + "*") if p.is_dir())
    if not matches:
        raise SystemExit(f"No week folder matching {prefix}* under {wtnc}")
    if len(matches) > 1:
        names = ", ".join(p.name for p in matches)
        raise SystemExit(f"Ambiguous --week {week!r}: {names}")
    return matches[0].resolve()


def resolve_dashboard(
    *,
    week: str | None,
    week_dir: Path | None,
    dashboard: Path | None,
) -> tuple[Path, Path]:
    """Return (dashboard.html, cumulative_dir)."""
    if dashboard is not None:
        dash = dashboard.resolve()
    elif week_dir is not None:
        dash = (week_dir / "world_meta" / "cumulative" / "dashboard.html").resolve()
    elif week:
        dash = (
            resolve_week_dir(week) / "world_meta" / "cumulative" / "dashboard.html"
        ).resolve()
    else:
        raise SystemExit("Pass --week, --week-dir, or --dashboard.")

    if not dash.is_file():
        raise SystemExit(f"Dashboard not found: {dash}")
    return dash, dash.parent


def mirror_site(dashboard: Path, cum_dir: Path, dest_root: Path) -> list[str]:
    """Copy shell + sibling folders into dest_root. Returns log lines."""
    notes: list[str] = []
    dest_index = dest_root / "index.html"
    shutil.copy2(dashboard, dest_index)
    notes.append(f"copied dashboard -> {dest_index.name}")

    for name in SIBLING_NAMES:
        src = cum_dir / name
        dst = dest_root / name
        if dst.exists():
            shutil.rmtree(dst)
        if src.is_dir():
            shutil.copytree(src, dst)
            notes.append(f"copied {name}/")
        else:
            notes.append(f"skip {name}/ (missing at source)")
    return notes


def run_ensure_seo() -> None:
    """Full SEO pass on the live repo index (also robots/sitemap)."""
    proc = subprocess.run(
        [sys.executable, str(ENSURE_SEO)],
        cwd=str(REPO_ROOT),
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(f"ensure_seo.py failed with exit {proc.returncode}")


def apply_seo_html_only(index_path: Path) -> None:
    """Inject SEO into one HTML file without touching robots/sitemap."""
    # Import alongside this file (tools/).
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import ensure_seo as seo  # noqa: WPS433

    fragment = seo._load_fragment()
    html = index_path.read_text(encoding="utf-8")
    html = seo.inject_head(html, fragment)
    html = seo.fix_page_title_h1(html)
    html = seo.fix_overall_view_title(html)
    index_path.write_text(html, encoding="utf-8")


def git_publish(*, skip_commit: bool, skip_push: bool) -> None:
    if skip_commit:
        print("Done (copy + SEO). Skipped commit.")
        return

    paths = ["index.html", "robots.txt", "sitemap.xml", *SIBLING_NAMES]
    subprocess.run(["git", "add", "--", *paths], cwd=str(REPO_ROOT), check=True)
    status = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=str(REPO_ROOT),
        check=True,
        capture_output=True,
        text=True,
    )
    if not status.stdout.strip():
        print("No file changes to commit.")
        return

    subprocess.run(
        ["git", "commit", "-m", "Update world dashboard (SEO preserved)"],
        cwd=str(REPO_ROOT),
        check=True,
    )
    if skip_push:
        print("Committed. Skipped push.")
        return

    subprocess.run(["git", "push"], cwd=str(REPO_ROOT), check=True)
    print(f"Pushed. Live: {LIVE_URL}")


def dry_run(dashboard: Path, cum_dir: Path) -> int:
    print(f"dashboard: {dashboard}")
    print(f"cumulative: {cum_dir}")
    for name in SIBLING_NAMES:
        src = cum_dir / name
        state = "ok" if src.is_dir() else "MISSING"
        print(f"  {name}/: {state}")

    with tempfile.TemporaryDirectory(prefix="ncm-publish-dry-") as tmp:
        dest = Path(tmp)
        for line in mirror_site(dashboard, cum_dir, dest):
            print(f"dry: {line}")
        apply_seo_html_only(dest / "index.html")
        index_text = (dest / "index.html").read_text(encoding="utf-8")
        if "Cyberpunk TCG Meta" not in index_text:
            raise SystemExit("dry-run: SEO title missing from staged index.html")
        if "night-city-meta:seo-start" not in index_text:
            raise SystemExit("dry-run: SEO fragment markers missing")
        for name in SIBLING_NAMES:
            if (cum_dir / name).is_dir() and not (dest / name).is_dir():
                raise SystemExit(f"dry-run: failed to stage {name}/")
    print("dry-run ok (temp stage + SEO)")
    return 0


def self_test() -> int:
    """Prove dated week folder names do not break resolve/copy/SEO."""
    with tempfile.TemporaryDirectory(prefix="ncm-publish-self-") as tmp:
        root = Path(tmp)
        # Deliberate ISO date segment — the PS 5.1 Split-Path -LiteralPath trap.
        week = root / "WTNC" / "WTNC_w9_2099-12-31"
        cum = week / "world_meta" / "cumulative"
        for name in SIBLING_NAMES:
            (cum / name).mkdir(parents=True)
            (cum / name / "probe.txt").write_text(name, encoding="utf-8")
        dash = cum / "dashboard.html"
        dash.write_text(
            """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>World meta — all weeks</title>
</head><body>
<h1 id="page-title">World meta — all weeks</h1>
<script>
const VIEWS = {"overall": {"title": "World meta — all weeks", "subtitle": "x"}};
</script>
</body></html>
""",
            encoding="utf-8",
        )

        resolved = resolve_week_dir("w9", tcg_root=root)
        assert resolved == week.resolve(), resolved
        got_dash, got_cum = resolve_dashboard(
            week=None, week_dir=week, dashboard=None
        )
        assert got_dash == dash.resolve()
        assert got_cum == cum.resolve()
        got_dash2, _ = resolve_dashboard(
            week=None, week_dir=None, dashboard=dash
        )
        assert got_dash2 == dash.resolve()

        dest = root / "pages"
        dest.mkdir()
        mirror_site(got_dash, got_cum, dest)
        assert (dest / "index.html").is_file()
        for name in SIBLING_NAMES:
            assert (dest / name / "probe.txt").read_text(encoding="utf-8") == name

        apply_seo_html_only(dest / "index.html")
        text = (dest / "index.html").read_text(encoding="utf-8")
        assert "Cyberpunk TCG Meta" in text
        assert "night-city-meta:seo-start" in text

        # Pathlib parent of a dated path must work (the old PS failure mode).
        assert Path(
            str(dash)
        ).parent.name == "cumulative", "dated path parent resolution failed"

    # ensure_seo's own self-test
    proc = subprocess.run(
        [sys.executable, str(ENSURE_SEO), "--self-test"],
        cwd=str(REPO_ROOT),
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit("ensure_seo --self-test failed")

    print("publish self-test ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--week", help="Short week id: w2, 2, or WTNC_w2_YYYY-MM-DD")
    p.add_argument("--week-dir", type=Path, help="Full path to WTNC week folder")
    p.add_argument("--dashboard", type=Path, help="Path to cumulative/dashboard.html")
    p.add_argument("--dry-run", action="store_true", help="Stage to temp + SEO; no writes to repo")
    p.add_argument("--skip-commit", action="store_true")
    p.add_argument("--skip-push", action="store_true")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)

    if args.self_test:
        return self_test()

    dashboard, cum_dir = resolve_dashboard(
        week=args.week,
        week_dir=args.week_dir,
        dashboard=args.dashboard,
    )

    if args.dry_run:
        return dry_run(dashboard, cum_dir)

    print(f"Publishing from {dashboard}")
    for line in mirror_site(dashboard, cum_dir, REPO_ROOT):
        print(line)
    print("Ensuring SEO head / H1 / overall title")
    run_ensure_seo()
    git_publish(skip_commit=args.skip_commit, skip_push=args.skip_push)
    return 0


if __name__ == "__main__":
    sys.exit(main())
