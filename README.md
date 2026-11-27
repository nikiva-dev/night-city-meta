# Cyberpunk TCG meta — Night City Showdowns

Public **Cyberpunk TCG meta** dashboard for Night City Showdowns: tier list, matchups, conversion, and Melee decklists.

**Live site:** https://nikiva-dev.github.io/night-city-meta/

Local clone (canonical): `C:\Users\Nikola\Desktop\night-city-meta`

## Weekly refresh (SEO-safe)

The generator writes a fresh multi-file `dashboard.html` (plus `assets/`, `data/`, `panels/`) without the published SEO head. **Always publish through `tools/publish.ps1` / `tools/publish.py`**, which copies the site and re-applies SEO before commit/push.

From this folder (preferred — short week id, no dated paths in the shell):

```powershell
git pull
.\tools\publish.ps1 -Week w2
```

Or:

```powershell
python tools\publish.py --week w2
```

Full week folder / dashboard path still work:

```powershell
.\tools\publish.ps1 -WeekDir "C:\Users\Nikola\Desktop\CyberpunkTCG\WTNC\WTNC_w2_2026-11-21"
.\tools\publish.ps1 -Dashboard "C:\Users\Nikola\Desktop\CyberpunkTCG\WTNC\WTNC_w2_2026-11-21\world_meta\cumulative\dashboard.html"
```

Useful flags: `-DryRun` (temp stage + SEO, no repo writes), `-SkipCommit`, `-SkipPush`, `-SelfTest`.

Set `CYBERPUNKTCG_ROOT` if the CyberpunkTCG checkout is not at `Desktop\CyberpunkTCG`.

### Preflight (no deploy)

```powershell
.\tools\publish.ps1 -SelfTest
.\tools\publish.ps1 -Week w2 -DryRun
python tools\ensure_seo.py --self-test
```

### What protects the SEO

1. **`seo/head.fragment.html`** — canonical title, description, canonical URL, Open Graph, Twitter, JSON-LD.
2. **`tools/ensure_seo.py`** — injects that fragment into `index.html`, sets `#page-title` / overall view title to `Cyberpunk TCG Meta`, and keeps `robots.txt` / `sitemap.xml`.
3. **`tools/publish.py`** (via `publish.ps1`) — resolve week → copy shell + `assets/` `data/` `panels/` → ensure_seo → commit/push.
4. **GitHub Action** `.github/workflows/ensure-seo.yml` — if someone copies `dashboard.html` over `index.html` and pushes without the script, CI restores SEO on `main` automatically.

Do **not** use a bare `Copy-Item … dashboard.html .\index.html` + push; that wiped the head before.

### PS 5.1 note

Week folders look like `WTNC_w2_2026-11-21`. PowerShell’s `Split-Path -LiteralPath` (and some advanced param binding) throws `AmbiguousParameterSet` on those paths. Publishing is implemented in Python so agents and humans can use `-Week w2` safely.

Manual one-off SEO restore:

```powershell
python tools\ensure_seo.py
```
