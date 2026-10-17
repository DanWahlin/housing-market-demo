# Data dictionary

All files are public U.S. government data. To download them again, run `python3 scripts/fetch_data.py`.

| File | Source | Grain | Columns |
| --- | --- | --- | --- |
| `states.csv` | Census Bureau | 50 states + DC | `state_code`, `state_name`, `fips`, `region`, `division` |
| `hpi_state_quarterly.csv` | FHFA House Price Index, purchase-only | state × quarter, 1991 Q1 to latest | `state_code`, `state_name`, `year`, `quarter`, `index_nsa`, `index_sa` |
| `hpi_metro_quarterly.csv` | FHFA House Price Index, purchase-only | 100 largest metros × quarter | `cbsa_code`, `metro_name`, `year`, `quarter`, `index_nsa`, `index_sa` |
| `hpi_us_division_monthly.csv` | FHFA House Price Index, purchase-only | USA and 9 census divisions × month | `place_id`, `place_name`, `year`, `month`, `index_nsa`, `index_sa` |
| `hmda_state_originations.csv` | CFPB HMDA Data Browser | state × year × loan purpose, 2018 to 2025 | `state_code`, `year`, `loan_purpose`, `loans`, `dollar_volume` |

## Notes

- **HPI** is an index, not a price. 1991 Q1 = 100. Year-over-year change for a quarter = index ÷ same quarter one year earlier − 1. Use `index_sa` (seasonally adjusted) for trend charts and `index_nsa` for year-over-year math.
- `place_id` `USA` in the monthly file is the national series.
- **HMDA** rows count originated loans (`action_taken = 1`) for home purchase, refinance, and cash-out refinance. `dollar_volume` is the sum of loan amounts in U.S. dollars. Average loan size = `dollar_volume` ÷ `loans`.
- Sources: [FHFA HPI datasets](https://www.fhfa.gov/data/hpi/datasets) and [CFPB HMDA Data Browser API](https://ffiec.cfpb.gov/documentation/api/data-browser/).
