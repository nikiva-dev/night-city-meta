# Cyberpunk TCG meta — Night City Showdowns

Public **Cyberpunk TCG meta** dashboard for Night City Showdowns: tier list, matchups, conversion, and Melee decklists. Plotly charts and legend art are inlined, so this repo is essentially a single HTML page.

**Live site:** https://nikiva-dev.github.io/night-city-meta/

Local clone (canonical): `C:\Users\Nikola\Desktop\night-city-meta`

## Weekly refresh

After the week's dashboard is rebuilt, from this folder:

```powershell
Copy-Item -Force "C:\Users\Nikola\Desktop\CyberpunkTCG\WTNC\<week>\world_meta\cumulative\dashboard.html" .\index.html
git add index.html
git commit -m "Update world dashboard"
git push
```

Replace `<week>` with the current folder, for example `WTNC_w2_2026-11-21`. The Pages URL stays the same.

After copying a fresh `dashboard.html`, re-apply the SEO `<head>` / H1 / overall title strings from this repo (or merge carefully) so the Cyberpunk TCG meta title and meta tags are not overwritten.
