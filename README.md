# Night City meta

Public copy of the Cyberpunk TCG world dashboard (Night City Showdowns). Plotly and legend art are inside the page, so this repo is a single HTML file.

Live page: https://nikiva-dev.github.io/night-city-meta/

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
