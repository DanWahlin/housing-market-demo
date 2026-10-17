# Agent instructions

This repo is a live demo for a GitHub Copilot app talk. Several agent sessions run at the same time. Each session builds one output from the same public housing data.

## Data

- Read `data/README.md` first. It describes every file and column.
- Do not change files in `data/`. Read them only.
- Use only the data in `data/`. Do not invent numbers. Show the latest period and the source (FHFA HPI, CFPB HMDA) next to every chart.
- Use these standard metrics so that every output shows the same numbers:
  - **Latest period:** the latest complete quarter in `hpi_state_quarterly.csv`.
  - **U.S. year-over-year change:** average the three monthly U.S. `index_nsa` values for the latest complete quarter, then compare with the same quarter one year earlier.
  - **Change since 2019 Q4:** the latest quarter compared with 2019 Q4 (the last quarter before the pandemic).
  - **State and metro year-over-year change:** `index_nsa` for the latest quarter compared with the same quarter one year earlier.
- Report facts from the data. Do not make forecasts, give investment advice, or say anything about Fannie Mae's views. Add this footer to each output: "Built from public FHFA and CFPB data. Not an official Fannie Mae, FHFA, or CFPB product."

## Output folders

| Output | Folder |
| --- | --- |
| Website | `site/` |
| Excel workbook | `analysis/` |
| PowerPoint briefing | `briefings/` |
| WorkIQ session brief | `talk/` |

Keep each session in its own folder so the sessions do not conflict.

## Tools on this machine

- Node.js 24 and npm
- Python 3 (create a virtual environment in `.venv/` before you `pip install`)
- Azure CLI (`az`), already signed in
- Microsoft Excel and PowerPoint, and LibreOffice (`soffice`) for headless rendering
- `templates/github-dark-template.pptx`: the dark GitHub slide template for decks

## Style

- Keep code small and readable. Prefer a few clear files over many small ones.
- Charts must have titles, axis labels, readable fonts, and color-blind-safe colors.
- Work fast. This runs live on stage with a time limit. Do not ask questions unless you are blocked.
