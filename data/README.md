# Data

Public housing data for the demo. Regenerate with `node scripts/fetch-data.mjs` (Node 18+, no npm packages, no API keys).

Snapshot pulled 2026-10-17. Latest complete quarter in `hpi_state_quarterly.csv`: **2026 Q2**. Monthly U.S./division data runs through 2026-07.

## Sources

- **FHFA House Price Index (HPI)**, master file: <https://www.fhfa.gov/hpi/download/monthly/hpi_master.csv> ([about the HPI](https://www.fhfa.gov/data/hpi)). Filtered to `hpi_type = traditional`, `hpi_flavor = purchase-only`.
- **CFPB HMDA Data Browser API**: <https://ffiec.cfpb.gov/v2/data-browser-api/view/aggregations> ([docs](https://ffiec.cfpb.gov/documentation/api/data-browser/)). Originated loans only (`actions_taken=1`), one request per state and year.

HPI is an **index, not a price**: 1991 Q1 = 100. `index_nsa` = not seasonally adjusted, `index_sa` = seasonally adjusted.

## Files

| File | Rows | Coverage | Columns |
| --- | --- | --- | --- |
| `states.csv` | 51 | 50 states + DC | `state_code` (USPS), `state_name`, `fips`, `region`, `division` (Census) |
| `hpi_state_quarterly.csv` | 7,242 | 51 states, 1991 Q1 – 2026 Q2 | `state_code`, `state_name`, `year`, `quarter` (1–4), `index_nsa`, `index_sa` |
| `hpi_metro_quarterly.csv` | 14,200 | 100 largest metros (CBSA), 1991 Q1 – 2026 Q2 | `cbsa_code`, `metro_name`, `year`, `quarter`, `index_nsa`, `index_sa` |
| `hpi_us_division_monthly.csv` | 4,270 | U.S. (`USA`) + 9 Census divisions (`DV_*`), 1991-01 – 2026-07 | `place_id`, `place_name`, `year`, `month` (1–12), `index_nsa`, `index_sa` |
| `hmda_state_originations.csv` | 1,224 | 51 states × 2018–2025 × 3 purposes | `state_code`, `year`, `loan_purpose`, `loans`, `dollar_volume` (USD) |

`loan_purpose` values: `Home purchase` (HMDA code 1), `Refinance` (31), `Cash-out refinance` (32).

## Standard metrics (use these everywhere)

- **Latest period:** latest complete quarter in `hpi_state_quarterly.csv`.
- **U.S. year-over-year:** average the three monthly `USA` `index_nsa` values for the latest quarter; compare with the same quarter a year earlier.
- **Change since 2019 Q4:** latest quarter vs. 2019 Q4.
- **State / metro year-over-year:** `index_nsa` latest quarter vs. same quarter a year earlier.

## Notes

- The HMDA API returns `dollar_volume` rounded to about 7 significant digits.
- Some metro names contain commas and are quoted; use a real CSV parser.
- Cite "FHFA HPI" and/or "CFPB HMDA" with the latest period next to every chart.

Built from public FHFA and CFPB data. Not an official Fannie Mae, FHFA, or CFPB product.
