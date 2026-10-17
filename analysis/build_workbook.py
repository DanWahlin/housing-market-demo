"""Build analysis/housing-market-analysis.xlsx from the CSV files in data/.

Run:  .venv/bin/python analysis/build_workbook.py
XlsxWriter builds the workbook. A small post-process step adds a real
PivotTable (pivot cache + records) and turns the pivot chart into a PivotChart,
because XlsxWriter cannot write PivotTables.
"""
import csv
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "analysis" / "housing-market-analysis.xlsx"
FILE_NAME = OUT.name

YEARS = list(range(2018, 2026))
PURPOSES = [("Home purchase", "Purchase"), ("Refinance", "Refi"), ("Cash-out refinance", "Cash-out")]
DISCLAIMER = "Built from public FHFA and CFPB data. Not an official Fannie Mae, FHFA, or CFPB product."
HMDA_SRC = "Source: CFPB HMDA Data Browser, originated loans (action_taken = 1), 2018 to 2025."
HPI_SRC = "Source: FHFA House Price Index, purchase-only, not seasonally adjusted. Q4 vs. prior-year Q4."

# Okabe-Ito color-blind-safe palette plus sequential blues/oranges
BLUE, ORANGE, GREEN, VERMILION = "#0072B2", "#E69F00", "#009E73", "#D55E00"
BLUES = ["#C6DBEF", "#9ECAE1", "#6BAED6", "#4292C6", "#2171B5", "#08519C", "#08306B", "#041E42"]
ORANGES = ["#FDD0A2", "#FDAE6B", "#FD8D3C", "#F16913", "#D94801", "#A63603", "#7F2704", "#4D1702"]

COLUMNS = [  # (header, width, format key)
    ("State", 16, None), ("State code", 10, None), ("Region", 11, None), ("Year", 7, "year"),
    ("Purchase loans", 14, "int"), ("Purchase volume", 18, "usd"),
    ("Refi loans", 12, "int"), ("Refi volume", 18, "usd"),
    ("Cash-out loans", 14, "int"), ("Cash-out volume", 18, "usd"),
    ("Total loans", 13, "int"), ("Total volume", 18, "usd"),
    ("Avg loan size", 14, "usd"), ("HPI Q4 YoY", 12, "pct"),
]


def read_csv(name):
    with open(DATA / name, newline="") as f:
        return list(csv.DictReader(f))


def load_rows():
    states = {r["state_code"]: r for r in read_csv("states.csv")}

    hmda = defaultdict(dict)
    for r in read_csv("hmda_state_originations.csv"):
        hmda[(r["state_code"], int(r["year"]))][r["loan_purpose"]] = (int(r["loans"]), int(r["dollar_volume"]))

    q4, latest_q = {}, (0, 0)
    for r in read_csv("hpi_state_quarterly.csv"):
        y, q = int(r["year"]), int(r["quarter"])
        latest_q = max(latest_q, (y, q))
        if q == 4:
            q4[(r["state_code"], y)] = float(r["index_nsa"])

    rows = []
    for code, s in sorted(states.items(), key=lambda kv: kv[1]["state_name"]):
        for y in YEARS:
            purpose = hmda.get((code, y), {})
            row = {"State": s["state_name"], "State code": code, "Region": s["region"], "Year": y}
            total_loans = total_vol = 0
            for key, short in PURPOSES:
                loans, vol = purpose.get(key, (0, 0))
                row[f"{short} loans"], row[f"{short} volume"] = loans, vol
                total_loans += loans
                total_vol += vol
            row["Total loans"], row["Total volume"] = total_loans, total_vol
            row["Avg loan size"] = round(total_vol / total_loans, 2) if total_loans else None
            now, before = q4.get((code, y)), q4.get((code, y - 1))
            row["HPI Q4 YoY"] = round(now / before - 1, 6) if now and before else None
            rows.append(row)
    return rows, latest_q


def build(rows, latest_q):
    OUT.parent.mkdir(exist_ok=True)
    wb = xlsxwriter.Workbook(OUT)
    wb.set_properties({"title": "U.S. housing market analysis", "comments": DISCLAIMER})
    F = {
        "int": wb.add_format({"num_format": "#,##0"}),
        "usd": wb.add_format({"num_format": "$#,##0"}),
        "pct": wb.add_format({"num_format": "0.0%"}),
        "usd_b": wb.add_format({"num_format": '$#,##0.0,,,"B"'}),
        "year": wb.add_format({"num_format": "0", "align": "center"}),
        "title": wb.add_format({"bold": True, "font_size": 20, "font_color": "#1F2328"}),
        "sub": wb.add_format({"font_size": 10, "font_color": "#57606A"}),
        "note": wb.add_format({"italic": True, "font_size": 9, "font_color": "#57606A"}),
        "h2": wb.add_format({"bold": True, "font_size": 13, "font_color": "#1F2328", "bottom": 2, "bottom_color": BLUE}),
        "label": wb.add_format({"bold": True, "align": "right", "valign": "vcenter"}),
        "input": wb.add_format({"bold": True, "font_size": 12, "bg_color": "#FFF8C5", "border": 1,
                                "border_color": "#BF8700", "valign": "vcenter"}),
        "value": wb.add_format({"bold": True, "font_size": 12, "align": "left", "valign": "vcenter"}),
        "th": wb.add_format({"bold": True, "bg_color": "#1F2328", "font_color": "#FFFFFF", "align": "center",
                             "text_wrap": True, "valign": "vcenter"}),
        "cell": wb.add_format({"font_size": 10}),
    }
    footer = "&L&8" + DISCLAIMER.replace("&", "&&")

    dash = wb.add_worksheet("Dashboard")
    data = wb.add_worksheet("Data")
    pivot = wb.add_worksheet("Pivot")
    notes = wb.add_worksheet("Notes")
    for ws in (dash, pivot, notes):
        ws.hide_gridlines(2)
    for ws in (dash, data, pivot, notes):
        ws.set_footer(footer)

    # ------------------------------------------------------------------ Data
    n = len(rows)
    data.add_table(0, 0, n, len(COLUMNS) - 1, {
        "name": "tblData", "style": "Table Style Medium 2",
        "data": [[r[c] for c, _, _ in COLUMNS] for r in rows],
        "columns": [{"header": c, "format": F[fmt] if fmt else None} for c, _, fmt in COLUMNS],
    })
    for i, (_, width, _) in enumerate(COLUMNS):
        data.set_column(i, i, width)
    data.freeze_panes(1, 1)
    note_col = len(COLUMNS) + 1
    data.write(0, note_col, "One row per state and year. " + HMDA_SRC, F["note"])
    data.write(1, note_col, HPI_SRC + f" Latest Q4 used: {YEARS[-1]}.", F["note"])
    data.write(2, note_col, DISCLAIMER, F["note"])

    # ------------------------------------------------------ Pivot (cached view)
    regions = sorted({r["Region"] for r in rows})
    agg = defaultdict(lambda: [0, 0])
    for r in rows:
        for key in ((r["Region"], r["Year"]), ("Grand Total", r["Year"])):
            agg[key][0] += r["Total loans"]
            agg[key][1] += r["Total volume"]

    ny = len(YEARS)
    pivot.write(0, 0, "PivotTable: total loans and average loan size by region and year", F["title"])
    pivot.write(1, 0, HMDA_SRC + " Avg loan size = dollar volume ÷ loans (calculated field, loan-weighted).", F["note"])
    top = 3  # pivot starts at A4
    pivot.write(top, 1, "Column Labels")
    pivot.write(top + 1, 1, "Loans (total)")
    pivot.write(top + 1, 1 + ny, "Avg loan size ($)")
    pivot.write(top + 2, 0, "Region")
    for j, y in enumerate(YEARS):
        pivot.write(top + 2, 1 + j, y)
        pivot.write(top + 2, 1 + ny + j, y)
    for i, reg in enumerate(regions + ["Grand Total"]):
        pivot.write(top + 3 + i, 0, reg)
        for j, y in enumerate(YEARS):
            loans, vol = agg[(reg, y)]
            pivot.write(top + 3 + i, 1 + j, loans, F["int"])
            pivot.write(top + 3 + i, 1 + ny + j, vol / loans, F["int"])
    pivot.set_column(0, 0, 14)
    pivot.set_column(1, 2 * ny, 11)
    pivot.freeze_panes(top + 3, 0)
    grand_row = top + 3 + len(regions)
    pivot_ref = f"A{top + 1}:{xl_rowcol_to_cell(grand_row, 2 * ny)}"

    col = wb.add_chart({"type": "column"})
    line = wb.add_chart({"type": "line"})
    cats = ["Pivot", top + 3, 0, grand_row - 1, 0]
    for j, y in enumerate(YEARS):
        col.add_series({
            "name": f"Loans (total) - {y}", "categories": cats,
            "values": ["Pivot", top + 3, 1 + j, grand_row - 1, 1 + j],
            "fill": {"color": BLUES[j]}, "border": {"none": True},
        })
    for j, y in enumerate(YEARS):
        line.add_series({
            "name": f"Avg loan size ($) - {y}", "categories": cats,
            "values": ["Pivot", top + 3, 1 + ny + j, grand_row - 1, 1 + ny + j],
            "line": {"none": True}, "y2_axis": True,
            "marker": {"type": "diamond", "size": 8, "fill": {"color": ORANGES[j]}, "border": {"color": "#333333"}},
        })
    col.combine(line)
    col.set_title({"name": "PivotChart: total loans (columns) and average loan size (diamonds) by region and year",
                   "name_font": {"size": 12}})
    col.set_x_axis({"name": "Region", "num_font": {"size": 10}})
    col.set_y_axis({"name": "Loans originated", "num_format": "#,##0", "num_font": {"size": 10}})
    line.set_y2_axis({"name": "Average loan size ($)", "num_format": "$#,##0", "num_font": {"size": 10}})
    col.set_legend({"position": "right", "font": {"size": 9}})
    col.set_size({"width": 1150, "height": 480})
    pivot.insert_chart(grand_row + 3, 0, col)
    pivot.write(grand_row + 28, 0, HMDA_SRC + " Latest year: 2025.", F["note"])
    pivot.write(grand_row + 29, 0, DISCLAIMER, F["note"])

    # ------------------------------------------------------------- Dashboard
    dash.set_column(0, 0, 2)
    dash.set_column(1, 12, 12.5)
    dash.set_column(1, 1, 17)
    dash.write(0, 1, "U.S. Housing Market Dashboard", F["title"])
    dash.write(1, 1, "Mortgage originations from CFPB HMDA (2018 to 2025) and home prices from FHFA HPI "
                     f"(purchase-only; latest quarter in the data: {latest_q[0]} Q{latest_q[1]}). "
                     "Pick a state in cell C4.", F["sub"])
    dash.set_row(3, 22)
    dash.write(3, 1, "State:", F["label"])
    dash.merge_range("C4:D4", "California", F["input"])
    state_names = [r["State"] for r in rows[::ny]]
    heat_top = 41  # heat map header row index (row 42)
    first_state, last_state = heat_top + 1, heat_top + len(state_names)
    dash.data_validation("C4", {
        "validate": "list", "source": f"=$B${first_state + 1}:$B${last_state + 1}",
    })
    dash.write(3, 5, "Region:", F["label"])
    dash.write_formula(3, 6, '=IFERROR(INDEX(tblData[Region],MATCH($C$4,tblData[State],0)),"")', F["value"])
    dash.write(3, 8, "Latest HMDA year:", F["label"])
    dash.write_formula("J4", "=MAX(tblData[Year])", wb.add_format({"bold": True, "font_size": 12, "num_format": "0", "align": "left"}))
    dash.write(3, 11, "Latest HPI qtr:", F["label"])
    dash.write(3, 12, f"{latest_q[0]} Q{latest_q[1]}", F["value"])
    dash.freeze_panes(4, 0)

    S, LY, prev = "$C$4", "$J$4", "($J$4-1)"

    def sumifs(column, year=LY):
        return f"SUMIFS(tblData[{column}],tblData[State],{S},tblData[Year],{year})"

    def yoy_txt(cur, old):
        return f'=IFERROR("vs. prior year: "&TEXT({cur}/{old}-1,"+0.0%;-0.0%"),"")'

    hpi = f"AVERAGEIFS(tblData[HPI Q4 YoY],tblData[State],{S},tblData[Year],{LY})"
    avg_now = f'({sumifs("Total volume")}/{sumifs("Total loans")})'
    avg_prev = f'({sumifs("Total volume", prev)}/{sumifs("Total loans", prev)})'
    cards = [
        (f'="Total loans, "&{LY}', "=" + sumifs("Total loans"), "#,##0",
         yoy_txt(sumifs("Total loans"), sumifs("Total loans", prev))),
        (f'="Dollar volume, "&{LY}', "=" + sumifs("Total volume"), '$#,##0.0,,,"B"',
         yoy_txt(sumifs("Total volume"), sumifs("Total volume", prev))),
        (f'="Average loan size, "&{LY}', f'=IFERROR({avg_now},"")', "$#,##0", yoy_txt(avg_now, avg_prev)),
        (f'="Home purchase share of loans, "&{LY}', f'=IFERROR({sumifs("Purchase loans")}/{sumifs("Total loans")},"")', "0.0%",
         f'=IFERROR("Refi + cash-out: "&TEXT(({sumifs("Refi loans")}+{sumifs("Cash-out loans")})/{sumifs("Total loans")},"0.0%"),"")'),
        (f'="Q4 home price change (YoY), "&{LY}', f'=IFERROR({hpi},"")', "+0.0%;-0.0%",
         f'=IFERROR("Rank "&(COUNTIFS(tblData[Year],{LY},tblData[HPI Q4 YoY],">"&{hpi})+1)'
         f'&" of "&COUNTIFS(tblData[Year],{LY})&" (1 = fastest)","")'),
        ('="Loans, change since 2018"', f'=IFERROR({sumifs("Total loans")}/{sumifs("Total loans", 2018)}-1,"")', "+0.0%;-0.0%",
         f'="2018: "&TEXT({sumifs("Total loans", 2018)},"#,##0")&" loans"'),
    ]
    card_label = wb.add_format({"font_size": 9, "bold": True, "font_color": "#57606A", "bg_color": "#F6F8FA",
                                "top": 5, "top_color": BLUE, "text_wrap": True, "valign": "top"})
    card_sub = wb.add_format({"font_size": 9, "font_color": "#57606A", "bg_color": "#F6F8FA",
                              "bottom": 1, "bottom_color": "#D0D7DE"})
    for k, (label, value, fmt, sub) in enumerate(cards):
        c0 = 1 + 2 * k
        vfmt = wb.add_format({"bold": True, "font_size": 18, "bg_color": "#F6F8FA", "num_format": fmt,
                              "align": "left", "valign": "vcenter"})
        for r, formula, f in ((5, label, card_label), (6, value, vfmt), (7, sub, card_sub)):
            dash.merge_range(r, c0, r, c0 + 1, "", f)
            dash.write_formula(r, c0, formula, f)
    dash.set_row(5, 28)
    dash.set_row(6, 30)
    dash.write(8, 1, "KPI cards use the latest HMDA year (2025) and the FHFA HPI change from Q4 2024 to Q4 2025. "
               + DISCLAIMER, F["note"])

    def section(row, text):
        dash.write(row, 1, text, F["h2"])
        for c in range(2, 13):
            dash.write_blank(row, c, None, F["h2"])

    section(9, "Selected state trends")

    # Helper table that feeds the charts
    tbl_top = 29
    section(tbl_top - 1, "Selected state by year (formulas; feeds the charts above)")
    heads = ["Year", "Purchase loans", "Refi loans", "Cash-out loans", "Total loans", "Total volume ($B)",
             "Avg loan size", "HPI Q4 YoY"]
    for j, h in enumerate(heads):
        dash.write(tbl_top, 1 + j, h, F["th"])
    dash.set_row(tbl_top, 30)
    for i, y in enumerate(YEARS):
        r = tbl_top + 1 + i
        yc = f"$B{r + 1}"
        dash.write_number(r, 1, y, F["year"])
        for j, name in enumerate(["Purchase loans", "Refi loans", "Cash-out loans", "Total loans", "Total volume"]):
            dash.write_formula(r, 2 + j, "=" + sumifs(name, yc), F["usd_b" if name == "Total volume" else "int"])
        dash.write_formula(r, 7, f'=IFERROR(G{r + 1}/F{r + 1},"")', F["usd"])
        dash.write_formula(r, 8, f'=IFERROR(AVERAGEIFS(tblData[HPI Q4 YoY],tblData[State],{S},tblData[Year],{yc}),"")', F["pct"])
    t1, t2 = tbl_top + 1, tbl_top + ny

    # Chart titles are formulas so they change with the selected state
    dash.merge_range(tbl_top, 10, tbl_top, 12, "Chart titles (formulas)", F["th"])
    titles = ['=$C$4&": loans by purpose"', '=$C$4&": Q4 home price change (YoY)"', '=$C$4&": average loan size"']
    for i, t in enumerate(titles):
        dash.merge_range(tbl_top + 1 + i, 10, tbl_top + 1 + i, 12, "", F["cell"])
        dash.write_formula(tbl_top + 1 + i, 10, t, F["cell"])

    years_ref = ["Dashboard", t1, 1, t2, 1]
    grid = {"visible": True, "line": {"color": "#E5E7EB"}}
    c1 = wb.add_chart({"type": "column", "subtype": "stacked"})
    for j, (name, color) in enumerate([("Home purchase", BLUE), ("Refinance", ORANGE), ("Cash-out refinance", GREEN)]):
        c1.add_series({"name": name, "categories": years_ref, "values": ["Dashboard", t1, 2 + j, t2, 2 + j],
                       "fill": {"color": color}, "border": {"none": True}, "gap": 60})
    c1.set_y_axis({"name": "Loans originated", "num_format": "#,##0", "major_gridlines": grid})
    c1.set_legend({"position": "bottom", "font": {"size": 9}})

    c2 = wb.add_chart({"type": "line"})
    c2.add_series({"name": "Q4 YoY change", "categories": years_ref, "values": ["Dashboard", t1, 8, t2, 8],
                   "line": {"color": VERMILION, "width": 2.5},
                   "marker": {"type": "circle", "size": 6, "fill": {"color": VERMILION}, "border": {"color": VERMILION}},
                   "data_labels": {"value": True, "position": "above", "num_format": "0.0%", "font": {"size": 8}}})
    c2.set_y_axis({"name": "Change vs. prior-year Q4", "num_format": "0%", "major_gridlines": grid})
    c2.set_legend({"none": True})

    c3 = wb.add_chart({"type": "line"})
    c3.add_series({"name": "Average loan size", "categories": years_ref, "values": ["Dashboard", t1, 7, t2, 7],
                   "line": {"color": BLUE, "width": 2.5},
                   "marker": {"type": "square", "size": 6, "fill": {"color": BLUE}, "border": {"color": BLUE}}})
    c3.set_y_axis({"name": "Average loan ($)", "num_format": "$#,##0", "major_gridlines": grid})
    c3.set_legend({"none": True})

    for i, (ch, cell) in enumerate([(c1, "B11"), (c2, "F11"), (c3, "J11")]):
        ch.set_title({"name": ["Dashboard", tbl_top + 1 + i, 10], "name_font": {"size": 11, "bold": True}})
        ch.set_x_axis({"name": "Year", "num_font": {"size": 9}, "name_font": {"size": 9}})
        ch.set_size({"width": 352, "height": 315})
        ch.set_chartarea({"border": {"color": "#D0D7DE"}})
        dash.insert_chart(cell, ch, {"x_offset": 2, "y_offset": 4})
    dash.write("B27", "Source: CFPB HMDA, originated loans. Latest: 2025.", F["note"])
    dash.write("F27", "Source: FHFA HPI purchase-only (NSA). Latest Q4: 2025.", F["note"])
    dash.write("J27", "Source: CFPB HMDA; volume ÷ loans. Latest: 2025.", F["note"])

    # Heat map (states x years) with a sparkline per state
    section(heat_top - 2, "Q4 year-over-year home price change by state (heat map)")
    for j, h in enumerate(["State", "Region"] + YEARS):
        dash.write(heat_top, 1 + j, h, F["th"])
    dash.merge_range(heat_top, 11, heat_top, 12, "Trend 2018 to 2025", F["th"])
    heat_pct = wb.add_format({"num_format": "0.0%", "align": "center", "font_size": 10,
                              "border": 1, "border_color": "#FFFFFF"})
    for i, name in enumerate(state_names):
        r = first_state + i
        dash.write(r, 1, name, F["cell"])
        dash.write_formula(r, 2, f'=IFERROR(INDEX(tblData[Region],MATCH($B{r + 1},tblData[State],0)),"")', F["cell"])
        for j in range(ny):
            year_cell = xl_rowcol_to_cell(heat_top, 3 + j, row_abs=True)
            dash.write_formula(r, 3 + j, f'=IFERROR(AVERAGEIFS(tblData[HPI Q4 YoY],tblData[State],$B{r + 1},'
                                         f'tblData[Year],{year_cell}),"")', heat_pct)
        dash.merge_range(r, 11, r, 12, "", F["cell"])
        dash.add_sparkline(r, 11, {"range": f"Dashboard!D{r + 1}:K{r + 1}", "type": "line", "series_color": BLUE,
                                   "high_point": True, "low_point": True, "high_color": VERMILION,
                                   "low_color": "#5E3C99", "axis": True})
    dash.conditional_format(f"D{first_state + 1}:K{last_state + 1}", {
        "type": "3_color_scale", "min_color": "#8073AC", "mid_type": "num", "mid_value": 0,
        "mid_color": "#F7F7F7", "max_color": "#E08214"})
    dash.conditional_format(f"B{first_state + 1}:C{last_state + 1}", {
        "type": "formula", "criteria": f"=$B{first_state + 1}=$C$4",
        "format": wb.add_format({"bold": True, "bg_color": "#FFF8C5"})})
    dash.write(last_state + 1, 1, HPI_SRC + " Latest Q4: 2025. Purple = falling prices, white = no change, "
               "orange = faster growth. Sparkline: high point vermilion, low point purple.", F["note"])
    dash.write(last_state + 2, 1, DISCLAIMER, F["note"])
    dash.activate()

    # ----------------------------------------------------------------- Notes
    notes.set_column(0, 0, 24)
    notes.set_column(1, 1, 120)
    wrap = wb.add_format({"text_wrap": True, "valign": "top"})
    bold = wb.add_format({"bold": True, "valign": "top"})
    notes.write(0, 0, "Notes and sources", F["title"])
    items = [
        ("Purpose", "Facts about mortgage originations and home price changes by state. No forecasts. No investment advice."),
        ("Source: home prices", "FHFA House Price Index (HPI), purchase-only, state by quarter (data/hpi_state_quarterly.csv). "
                                "https://www.fhfa.gov/data/hpi/datasets"),
        ("Source: mortgages", "CFPB HMDA Data Browser, originated loans (action_taken = 1), state by year by loan purpose "
                              "(data/hmda_state_originations.csv). https://ffiec.cfpb.gov/documentation/api/data-browser/"),
        ("Source: regions", "U.S. Census Bureau regions (data/states.csv)."),
        ("Latest periods", f"HMDA: 2018 to 2025 (latest year 2025). HPI: latest quarter in the data is {latest_q[0]} "
                           f"Q{latest_q[1]}. The HPI Q4 YoY column uses Q4 2018 to Q4 2025."),
        ("HPI Q4 YoY", "Q4 index_nsa of the year ÷ Q4 index_nsa of the prior year − 1. HPI is an index (1991 Q1 = 100), not a price."),
        ("Loans and volume", "Count and summed loan amount (U.S. dollars) of originated loans for home purchase, refinance, and "
                             "cash-out refinance. Total = sum of the three purposes."),
        ("Avg loan size", "Dollar volume ÷ loans. In the PivotTable it is a calculated field (Total volume ÷ Total loans), "
                          "so regional values are loan-weighted."),
        ("Sheets", "Dashboard: state drop-down (C4), KPI cards, three formula-driven charts, heat map, and sparklines. "
                   "Data: Excel table tblData (one row per state and year). Pivot: PivotTable and PivotChart on tblData."),
        ("Refresh", "The PivotTable refreshes when the file opens. After you edit tblData, right-click the PivotTable and "
                    "select Refresh. Dashboard formulas update automatically."),
        ("Disclaimer", DISCLAIMER),
    ]
    for i, (k, v) in enumerate(items):
        notes.write(2 + i, 0, k, bold)
        notes.write(2 + i, 1, v, wrap)
    notes.freeze_panes(1, 0)

    wb.close()
    return regions, pivot_ref


# --------------------------------------------------- PivotTable post-process
NS = ('xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
XML_HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'


def num(v):
    return repr(float(v)) if isinstance(v, float) else str(v)


def pivot_parts(rows, regions, pivot_ref):
    names = [c for c, _, _ in COLUMNS]
    shared = {"State": sorted({r["State"] for r in rows}), "State code": sorted({r["State code"] for r in rows}),
              "Region": regions, "Year": YEARS}
    fields, recs = [], [[] for _ in rows]
    for name in names:
        vals = [r[name] for r in rows]
        if name in shared:
            items = shared[name]
            if name == "Year":
                inner = "".join(f'<n v="{v}"/>' for v in items)
                attrs = (f'containsSemiMixedTypes="0" containsString="0" containsNumber="1" containsInteger="1" '
                         f'minValue="{min(items)}" maxValue="{max(items)}" count="{len(items)}"')
            else:
                inner = "".join(f'<s v="{escape(v, {chr(34): "&quot;"})}"/>' for v in items)
                attrs = f'count="{len(items)}"'
            fields.append(f'<cacheField name="{name}" numFmtId="0"><sharedItems {attrs}>{inner}</sharedItems></cacheField>')
            idx = {v: i for i, v in enumerate(items)}
            for k, v in enumerate(vals):
                recs[k].append(f'<x v="{idx[v]}"/>')
        else:
            present = [v for v in vals if v is not None]
            blank = len(present) < len(vals)
            attrs = (("" if blank else 'containsSemiMixedTypes="0" ') + 'containsString="0" '
                     + ('containsBlank="1" ' if blank else "") + 'containsNumber="1" '
                     + ('containsInteger="1" ' if all(isinstance(v, int) for v in present) else "")
                     + f'minValue="{num(min(present))}" maxValue="{num(max(present))}"')
            fields.append(f'<cacheField name="{name}" numFmtId="0"><sharedItems {attrs}/></cacheField>')
            for k, v in enumerate(vals):
                recs[k].append("<m/>" if v is None else f'<n v="{num(v)}"/>')
    fields.append('<cacheField name="AvgLoanCalc" numFmtId="0" formula="\'Total volume\'/\'Total loans\'" databaseField="0"/>')

    cache_def = (f'{XML_HEAD}<pivotCacheDefinition {NS} r:id="rId1" refreshOnLoad="1" refreshedBy="build_workbook.py" '
                 f'refreshedDate="46000" createdVersion="6" refreshedVersion="6" minRefreshableVersion="3" '
                 f'recordCount="{len(rows)}"><cacheSource type="worksheet"><worksheetSource name="tblData"/></cacheSource>'
                 f'<cacheFields count="{len(fields)}">{"".join(fields)}</cacheFields></pivotCacheDefinition>')
    cache_rec = (f'{XML_HEAD}<pivotCacheRecords {NS} count="{len(rows)}">'
                 + "".join(f"<r>{''.join(r)}</r>" for r in recs) + "</pivotCacheRecords>")

    reg_i, year_i, loans_i, calc_i = names.index("Region"), names.index("Year"), names.index("Total loans"), len(names)
    pfields = []
    for i in range(len(names) + 1):
        if i in (reg_i, year_i):
            count = len(regions) if i == reg_i else len(YEARS)
            axis = "axisRow" if i == reg_i else "axisCol"
            items = "".join(f'<item x="{k}"/>' for k in range(count)) + '<item t="default"/>'
            pfields.append(f'<pivotField axis="{axis}" showAll="0"><items count="{count + 1}">{items}</items></pivotField>')
        elif i == loans_i:
            pfields.append('<pivotField dataField="1" showAll="0"/>')
        elif i == calc_i:
            pfields.append('<pivotField dataField="1" dragToRow="0" dragToCol="0" dragToPage="0" showAll="0" defaultSubtotal="0"/>')
        else:
            pfields.append('<pivotField showAll="0"/>')
    row_items = "".join("<i><x/></i>" if k == 0 else f'<i><x v="{k}"/></i>' for k in range(len(regions)))
    row_items += '<i t="grand"><x/></i>'
    col_items = []
    for d in range(2):  # data field (outer), then year (inner)
        for k in range(len(YEARS)):
            if k == 0:
                col_items.append("<i><x/><x/></i>" if d == 0 else f'<i i="{d}"><x v="{d}"/><x/></i>')
            else:
                col_items.append(f'<i r="1"><x v="{k}"/></i>' if d == 0 else f'<i r="1" i="{d}"><x v="{k}"/></i>')
    table = (
        f'{XML_HEAD}<pivotTableDefinition {NS} name="PivotTable1" cacheId="1" applyNumberFormats="0" '
        'applyBorderFormats="0" applyFontFormats="0" applyPatternFormats="0" applyAlignmentFormats="0" '
        'applyWidthHeightFormats="1" dataCaption="Values" updatedVersion="6" minRefreshableVersion="3" '
        'useAutoFormatting="1" colGrandTotals="0" itemPrintTitles="1" createdVersion="6" indent="0" outline="1" '
        'outlineData="1" multipleFieldFilters="0" chartFormat="1" dataPosition="0" rowHeaderCaption="Region" '
        'colHeaderCaption="Year">'
        f'<location ref="{pivot_ref}" firstHeaderRow="1" firstDataRow="3" firstDataCol="1"/>'
        f'<pivotFields count="{len(pfields)}">{"".join(pfields)}</pivotFields>'
        f'<rowFields count="1"><field x="{reg_i}"/></rowFields>'
        f'<rowItems count="{len(regions) + 1}">{row_items}</rowItems>'
        f'<colFields count="2"><field x="-2"/><field x="{year_i}"/></colFields>'
        f'<colItems count="{len(col_items)}">{"".join(col_items)}</colItems>'
        '<dataFields count="2">'
        f'<dataField name="Loans (total)" fld="{loans_i}" baseField="0" baseItem="0" numFmtId="3"/>'
        f'<dataField name="Avg loan size ($)" fld="{calc_i}" baseField="0" baseItem="0" numFmtId="3"/>'
        '</dataFields><pivotTableStyleInfo name="PivotStyleMedium2" showRowHeaders="1" showColHeaders="1" '
        'showRowStripes="0" showColStripes="0" showLastColumn="1"/></pivotTableDefinition>')
    return cache_def, cache_rec, table


def rels(*items):
    body = "".join(f'<Relationship Id="{i}" Type="{REL}/{t}" Target="{tg}"/>' for i, t, tg in items)
    return f'{XML_HEAD}<Relationships xmlns="{PKG_REL}">{body}</Relationships>'


def add_pivot(rows, regions, pivot_ref):
    cache_def, cache_rec, table = pivot_parts(rows, regions, pivot_ref)
    with zipfile.ZipFile(OUT) as z:
        parts = {name: z.read(name) for name in z.namelist()}

    wb_xml = parts["xl/workbook.xml"].decode()
    sheet_rid = re.search(r'<sheet name="Pivot" sheetId="\d+" r:id="(rId\d+)"', wb_xml).group(1)
    wb_xml = re.sub(r"(<calcPr[^>]*/>)", r'\1<pivotCaches><pivotCache cacheId="1" r:id="rId900"/></pivotCaches>',
                    wb_xml, count=1)
    wb_rels = parts["xl/_rels/workbook.xml.rels"].decode()
    sheet_file = re.search(rf'Id="{sheet_rid}"[^>]*Target="worksheets/([^"]+)"', wb_rels).group(1)
    wb_rels = wb_rels.replace("</Relationships>", f'<Relationship Id="rId900" Type="{REL}/pivotCacheDefinition" '
                                                  'Target="pivotCache/pivotCacheDefinition1.xml"/></Relationships>')

    sheet_rels_name = f"xl/worksheets/_rels/{sheet_file}.rels"
    sheet_rels = parts[sheet_rels_name].decode()
    drawing = re.search(r'Target="\.\./drawings/([^"]+)"', sheet_rels).group(1)
    sheet_rels = sheet_rels.replace("</Relationships>", f'<Relationship Id="rId900" Type="{REL}/pivotTable" '
                                                        'Target="../pivotTables/pivotTable1.xml"/></Relationships>')
    chart = re.search(r'Target="\.\./charts/([^"]+)"', parts[f"xl/drawings/_rels/{drawing}.rels"].decode()).group(1)
    chart_xml = parts[f"xl/charts/{chart}"].decode().replace(
        "<c:chart>", f"<c:pivotSource><c:name>[{FILE_NAME}]Pivot!PivotTable1</c:name><c:fmtId val=\"0\"/></c:pivotSource><c:chart>", 1)

    base = "application/vnd.openxmlformats-officedocument.spreadsheetml"
    ctypes = parts["[Content_Types].xml"].decode().replace("</Types>",
        f'<Override PartName="/xl/pivotCache/pivotCacheDefinition1.xml" ContentType="{base}.pivotCacheDefinition+xml"/>'
        f'<Override PartName="/xl/pivotCache/pivotCacheRecords1.xml" ContentType="{base}.pivotCacheRecords+xml"/>'
        f'<Override PartName="/xl/pivotTables/pivotTable1.xml" ContentType="{base}.pivotTable+xml"/></Types>')

    parts.update({
        "[Content_Types].xml": ctypes.encode(),
        "xl/workbook.xml": wb_xml.encode(),
        "xl/_rels/workbook.xml.rels": wb_rels.encode(),
        sheet_rels_name: sheet_rels.encode(),
        f"xl/charts/{chart}": chart_xml.encode(),
        "xl/pivotCache/pivotCacheDefinition1.xml": cache_def.encode(),
        "xl/pivotCache/_rels/pivotCacheDefinition1.xml.rels":
            rels(("rId1", "pivotCacheRecords", "pivotCacheRecords1.xml")).encode(),
        "xl/pivotCache/pivotCacheRecords1.xml": cache_rec.encode(),
        "xl/pivotTables/pivotTable1.xml": table.encode(),
        "xl/pivotTables/_rels/pivotTable1.xml.rels":
            rels(("rId1", "pivotCacheDefinition", "../pivotCache/pivotCacheDefinition1.xml")).encode(),
    })
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for name, blob in parts.items():
            z.writestr(name, blob)


if __name__ == "__main__":
    rows, latest_q = load_rows()
    regions, pivot_ref = build(rows, latest_q)
    add_pivot(rows, regions, pivot_ref)
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(rows)} rows, latest HPI quarter {latest_q[0]} Q{latest_q[1]}")
