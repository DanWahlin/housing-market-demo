# Agent instructions

This repo is a live demo for a GitHub Copilot app talk. Several agent sessions run at the same time. Each session builds one output from the same public housing data.

## Data

The first session (the data session) downloads the data into `data/`. All other sessions only read `data/`. They must not change it.

### Files the data session creates

| File | Source and filter | Columns |
| --- | --- | --- |
| `states.csv` | 50 states and DC with Census regions and divisions | `state_code`, `state_name`, `fips`, `region`, `division` |
| `hpi_state_quarterly.csv` | FHFA HPI master file: `traditional`, `purchase-only`, `quarterly`, level `State` (50 states and DC only) | `state_code`, `state_name`, `year`, `quarter`, `index_nsa`, `index_sa` |
| `hpi_metro_quarterly.csv` | FHFA HPI master file: `traditional`, `purchase-only`, `quarterly`, level `MSA` | `cbsa_code`, `metro_name`, `year`, `quarter`, `index_nsa`, `index_sa` |
| `hpi_us_division_monthly.csv` | FHFA HPI master file: `traditional`, `purchase-only`, `monthly`, level `USA or Census Division` | `place_id`, `place_name`, `year`, `month`, `index_nsa`, `index_sa` |
| `hmda_state_originations.csv` | CFPB HMDA API: originated loans for each state and year, 2018 to 2025 | `state_code`, `year`, `loan_purpose`, `loans`, `dollar_volume` |

### Source details

- **FHFA HPI master file:** `https://www.fhfa.gov/hpi/download/monthly/hpi_master.csv` (one CSV file, about 17 MB). Columns: `hpi_type`, `hpi_flavor`, `frequency`, `level`, `place_name`, `place_id`, `yr`, `period`, `index_nsa`, `index_sa`. Some place names have commas and are in quotes, so use a real CSV parser.
- **CFPB HMDA API:** `https://ffiec.cfpb.gov/v2/data-browser-api/view/aggregations?years=2024&states=VA&actions_taken=1&loan_purposes=1,31,32`. The JSON has one `aggregations` item for each loan purpose with `count` (loans) and `sum` (dollar volume). Loan purposes: `1` = Home purchase, `31` = Refinance, `32` = Cash-out refinance. A query with many states returns one combined total, so send one request for each state and year.
- The HMDA API returns HTTP 403 for some `User-Agent` values. Send `User-Agent: curl/8.7.1`, and send no more than 4 requests at a time.
- No API keys are necessary.

### Rules for all sessions

- Read `data/README.md` before you use the data.
- HPI is an index, not a price. 1991 Q1 = 100.
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
| Data and download script | `data/` and `scripts/` |
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

## Excel tips

- In an Excel table, write calculated columns as plain values, not formulas. Table formulas often cause a repair message.
- If Excel shows a repair message, first read the newest `Repair Result*.xml` file in `~/Library/Containers/com.microsoft.Excel/Data/tmp/`. It names the broken part.

## Style

- Keep code small and readable. Prefer a few clear files over many small ones.
- Charts must have titles, axis labels, readable fonts, and color-blind-safe colors.
- Work fast. This runs live on stage with a time limit. Do not ask questions unless you are blocked.
