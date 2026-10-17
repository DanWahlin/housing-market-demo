# Housing market analysis workbook

`housing-market-analysis.xlsx` is built only from the files in `data/`.

| Sheet | Contents |
| --- | --- |
| Dashboard | State drop-down, KPI cards, three formula-driven charts, a heat map of Q4 home price change (states by year), and sparklines for each state |
| Data | `tblData`: one row for each state and year (2018 to 2025) with loans and dollar volume by loan purpose, average loan size, and Q4 HPI year-over-year change |
| Pivot | PivotTable (regions by years, total loans and average loan size) and a PivotChart |
| Notes | Sources, definitions, and the latest period |
| Calc | Formula helpers for the dashboard |

`dashboard.png` is a screenshot of the Dashboard sheet in Microsoft Excel.

## Rebuild

```bash
python3 -m venv .venv && .venv/bin/pip install xlsxwriter
.venv/bin/python analysis/build_workbook.py
```

XlsxWriter cannot make PivotTables, so `add_pivot.py` adds the PivotTable, its cache, and the PivotChart link as Office Open XML parts. Excel refreshes the PivotTable when it opens the file.

Built from public FHFA and CFPB data. Not an official Fannie Mae, FHFA, or CFPB product.
