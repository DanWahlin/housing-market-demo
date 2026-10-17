# U.S. Housing Market Explorer

Static site (Vite, TypeScript, D3) built from the public FHFA HPI and CFPB HMDA data in `../data/`.

Live: <https://calm-rock-09895ae0f.5.azurestaticapps.net/> (QR code: `qr-code.png`)

```bash
npm install
npm test        # Vitest tests for year-over-year change and rankings
npm run dev     # local dev server
npm run build   # converts ../data/*.csv to public/data/*.json, then builds dist/
```

- `scripts/build-data.ts`: reads the CSV files (read only) and writes small JSON files.
- `src/metrics.ts`: metric math (year-over-year change, change since 2019 Q4, U.S. quarterly average from monthly values, rankings).
- `src/map.ts`, `src/statePanel.ts`, `src/metroChart.ts`: charts.

Deploy: `swa deploy ./dist --deployment-token <token> --env production` (Azure Static Web App `swa-housing-market-demo`).

Built from public FHFA and CFPB data. Not an official Fannie Mae, FHFA, or CFPB product.
