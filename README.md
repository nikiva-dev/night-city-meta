# Cyberpunk TCG meta — Night City Showdowns

Public **Cyberpunk TCG meta** dashboard for Night City Showdowns: tier list, matchups, conversion, and Melee decklists. Plotly charts and legend art are inlined, so this repo is essentially a single HTML page.

**Live site:** https://nikiva-dev.github.io/night-city-meta/

Local clone (canonical): `C:\Users\Nikola\Desktop\night-city-meta`

## Weekly refresh (SEO-safe)

The generator writes a fresh `dashboard.html` without the published SEO head. **Always publish through `tools/publish.ps1`**, which copies the file and re-applies SEO before commit/push.

From this folder:

```powershell
.\tools\publish.ps1 -WeekDir "C:\Users\Nikola\Desktop\CyberpunkTCG\WTNC\<week>"
```

Replace `<week>` with the current folder, for example `WTNC_w2_2026-11-21`.

Or pass the dashboard path directly:

```powershell
.\tools\publish.ps1 -Dashboard "C:\Users\Nikola\Desktop\CyberpunkTCG\WTNC\<week>\world_meta\cumulative\dashboard.html"
```

Useful flags: `-SkipCommit`, `-SkipPush`.

### What protects the SEO

1. **`seo/head.fragment.html`** — canonical title, description, canonical URL, Open Graph, Twitter, JSON-LD.
2. **`tools/ensure_seo.py`** — injects that fragment into `index.html`, sets `#page-title` / overall view title to `Cyberpunk TCG Meta`, and keeps `robots.txt` / `sitemap.xml`.
3. **`tools/publish.ps1`** — copy dashboard → run ensure_seo → commit/push.
4. **GitHub Action** `.github/workflows/ensure-seo.yml` — if someone copies `dashboard.html` over `index.html` and pushes without the script, CI restores SEO on `main` automatically.

Do **not** use a bare `Copy-Item … dashboard.html .\index.html` + push anymore; that is what wiped the head before.

Manual one-off restore:

```powershell
python tools\ensure_seo.py
```
