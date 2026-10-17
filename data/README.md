# Housing data dictionary

Public data for the housing market demo. Do not edit these files by hand. To refresh them, run:

```bash
node scripts/fetch-data.mjs
```

The script uses Node.js 18 or later and no npm packages. It takes about 15 seconds.

## Sources

| Source | Link | Used for |
| --- | --- | --- |
| FHFA House Price Index (HPI) master file | <https://www.fhfa.gov/hpi/download/monthly/hpi_master.csv> ([about the HPI](https://www.fhfa.gov/data/hpi)) | All `hpi_*.csv` files |
| CFPB HMDA Data Browser API | <https://ffiec.cfpb.gov/v2/data-browser-api/view/aggregations> ([documentation](https://ffiec.cfpb.gov/documentation/api/data-browser/)) | `hmda_state_originations.csv` |
| U.S. Census Bureau regions and divisions | <https://www2.census.gov/geo/pdfs/maps-data/maps/reference/us_regdiv.pdf> | `states.csv` |

## Important notes

- **HPI is an index, not a price.** 1991 Q1 = 100 (January 1991 = 100 for monthly data). It shows the change in prices, not dollar values.
- All HPI files use the **traditional, purchase-only** index.
- `index_nsa` = not seasonally adjusted. `index_sa` = seasonally adjusted. Use `index_nsa` for year-over-year change.
- HMDA rows are **originated loans** only (`actions_taken=1`). One API request for each state and year.
- **Latest complete quarter** in this snapshot: **2026 Q2**. The monthly file goes to July 2026.

## Files

### `states.csv` (51 rows: 50 states and DC)

| Column | Description |
| --- | --- |
| `state_code` | Two-letter USPS code, for example `VA` |
| `state_name` | Full state name |
| `fips` | Two-digit state FIPS code (text, with a leading zero) |
| `region` | Census region: Northeast, Midwest, South, West |
| `division` | Census division, for example South Atlantic |

### `hpi_state_quarterly.csv` (7,242 rows: 51 states, 1991 Q1 to 2026 Q2)

| Column | Description |
| --- | --- |
| `state_code` | Two-letter USPS code |
| `state_name` | Full state name |
| `year` | Year |
| `quarter` | Quarter, 1 to 4 |
| `index_nsa` | HPI, not seasonally adjusted |
| `index_sa` | HPI, seasonally adjusted |

### `hpi_metro_quarterly.csv` (14,200 rows: 100 largest metros, 1991 Q1 to 2026 Q2)

| Column | Description |
| --- | --- |
| `cbsa_code` | Core-based statistical area (CBSA) code. Some are metro divisions (MSAD). |
| `metro_name` | Metro name, for example `Albany-Schenectady-Troy, NY` (has commas, so it is in quotes) |
| `year`, `quarter`, `index_nsa`, `index_sa` | Same as the state file |

### `hpi_us_division_monthly.csv` (4,270 rows: U.S. and 9 divisions, January 1991 to July 2026)

| Column | Description |
| --- | --- |
| `place_id` | `USA` for the United States, or a division ID such as `DV_SA` |
| `place_name` | `United States` or the Census division name |
| `year` | Year |
| `month` | Month, 1 to 12 |
| `index_nsa`, `index_sa` | Same as above |

### `hmda_state_originations.csv` (1,224 rows: 51 states, 2018 to 2025, 3 loan purposes)

| Column | Description |
| --- | --- |
| `state_code` | Two-letter USPS code |
| `year` | HMDA reporting year |
| `loan_purpose` | `Home purchase` (code 1), `Refinance` (code 31), or `Cash-out refinance` (code 32) |
| `loans` | Number of originated loans |
| `dollar_volume` | Total loan amount in U.S. dollars |

## Attribution

Show the source (FHFA HPI, CFPB HMDA) and the latest period next to every chart.

Built from public FHFA and CFPB data. Not an official Fannie Mae, FHFA, or CFPB product.
