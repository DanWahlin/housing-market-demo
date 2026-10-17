"""Build analysis/housing-market-analysis.xlsx from data/.

Run: .venv/bin/python analysis/build_workbook.py
"""
from pathlib import Path

import xlsxwriter
from xlsxwriter.utility import xl_col_to_name, xl_rowcol_to_cell

from data_prep import PURPOSES, YEARS, load
from add_pivot import add_pivot

OUT = Path(__file__).resolve().parent / "housing-market-analysis.xlsx"
FOOTER = "Built from public FHFA and CFPB data. Not an official Fannie Mae, FHFA, or CFPB product."
DEFAULT_STATE = "Virginia"
PCT = '+0.0%;-0.0%;0.0%'
# Okabe-Ito and viridis palettes are color-blind safe.
OKABE = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7"]
VIRIDIS = ["#440154", "#46327E", "#365C8D", "#277F8E", "#1FA187", "#4AC16D", "#A0DA39", "#FDE725"]

d = load()
rows, sm, us = d["rows"], d["state_metrics"], d["us"]
ly, lq = d["latest"]
LATEST = f"{ly} Q{lq}"
N = len(rows)
NS = len(sm)

wb = xlsxwriter.Workbook(str(OUT))
wb.set_properties({"title": "U.S. Housing Market Analysis", "comments": FOOTER})
wb.set_calc_mode("auto")
F = lambda **k: wb.add_format({"font_name": "Calibri", **k})
fmt = {
    "int": F(num_format="#,##0"), "usd": F(num_format="$#,##0"), "pct": F(num_format=PCT),
    "idx": F(num_format="0.00"), "title": F(bold=True, font_size=18, font_color="#1F2937"),
    "sub": F(italic=True, font_color="#4B5563"), "h": F(bold=True, bg_color="#1F4E79", font_color="white", border=1, text_wrap=True, valign="vcenter"),
    "b": F(bold=True), "wrap": F(text_wrap=True, valign="top"), "note": F(italic=True, font_size=9, font_color="#4B5563"),
    "link": F(font_color="#0563C1", underline=1),
}

dash = wb.add_worksheet("Dashboard")
data = wb.add_worksheet("Data")
piv = wb.add_worksheet("Pivot")
notes = wb.add_worksheet("Notes")
calc = wb.add_worksheet("Calc")
for ws in (dash, data, piv, notes, calc):
    ws.set_footer("&L&8" + FOOTER)

# ---------- Data sheet: one Excel table, one row per state and year ----------
headers = [("State code", None, 10), ("State", None, 20), ("Region", None, 11), ("Division", None, 19), ("Year", None, 7)]
for p, short in zip(PURPOSES, ["Purchase", "Refinance", "Cash-out refi"]):
    headers += [(f"{short} loans", fmt["int"], 13), (f"{short} volume", fmt["usd"], 17)]
headers += [("Total loans", fmt["int"], 12), ("Total dollar volume", fmt["usd"], 18),
            ("Avg loan size", fmt["usd"], 13), ("Q4 HPI YoY change", fmt["pct"], 13)]
table_rows = []
for r in rows:
    vals = [r["code"], r["name"], r["region"], r["division"], r["year"]]
    for l, v in zip(r["loans"], r["vols"]):
        vals += [l, v]
    vals += [r["total_loans"], r["total_vol"], r["avg"], r["q4_yoy"]]
    table_rows.append(vals)
data.add_table(0, 0, N, len(headers) - 1, {
    "name": "tblData", "style": "Table Style Medium 2", "data": table_rows,
    "columns": [{"header": h, **({"format": f} if f else {})} for h, f, _ in headers]})
for i, (_, _, w) in enumerate(headers):
    data.set_column(i, i, w)
data.set_row(0, 30, fmt["h"])
data.freeze_panes(1, 2)
data.write(N + 2, 0, "Sources: CFPB HMDA (originated loans, 2018-2025); FHFA HPI purchase-only, index_nsa (Q4 vs prior-year Q4).", fmt["note"])
data.write(N + 3, 0, FOOTER, fmt["note"])

# ---------- Calc sheet: lookups that drive the dashboard ----------
calc.set_column("A:B", 20); calc.set_column("C:F", 15)
calc.set_column("H:H", 30); calc.set_column("I:N", 14); calc.set_column("P:P", 10); calc.set_column("Q:R", 13)
calc.write_row(0, 0, ["State code", "State", "Region", f"HPI YoY {LATEST}", "Change since 2019 Q4", f"HPI {LATEST}"], fmt["h"])
for i, s in enumerate(sm, start=1):
    calc.write_row(i, 0, [s["code"], s["name"], s["region"]])
    calc.write(i, 3, s["yoy"], fmt["pct"]); calc.write(i, 4, s["since"], fmt["pct"]); calc.write(i, 5, s["index"], fmt["idx"])
SR = f"$B$2:$B${NS + 1}"  # state name list

us_avg25 = sum(r["total_vol"] for r in rows if r["year"] == 2025) / sum(r["total_loans"] for r in rows if r["year"] == 2025)
calc.write_row(0, 7, ["Metric", "Value"], fmt["h"])
calc.write(1, 7, f"U.S. HPI YoY ({LATEST})"); calc.write(1, 8, us["yoy"], fmt["pct"])
calc.write(2, 7, "U.S. change since 2019 Q4"); calc.write(2, 8, us["since"], fmt["pct"])
calc.write(3, 7, "U.S. avg loan size (2025)")
calc.write_formula(3, 8, "=SUMIFS(tblData[Total dollar volume],tblData[Year],2025)/SUMIFS(tblData[Total loans],tblData[Year],2025)", fmt["usd"], us_avg25)
calc.write(5, 7, "Selected state", fmt["b"]); calc.write_formula(5, 8, "=Dashboard!$C$4", fmt["b"], DEFAULT_STATE)
sel = next(s for s in sm if s["name"] == DEFAULT_STATE)
calc.write(6, 7, "State code"); calc.write_formula(6, 8, f"=INDEX($A$2:$A${NS + 1},MATCH($I$6,{SR},0))", None, sel["code"])

# Selected state by year (H9:N17)
calc.write_row(8, 7, ["Year"] + PURPOSES + ["Avg loan size", "State Q4 HPI YoY", "U.S. Q4 HPI YoY"], fmt["h"])
sel_rows = {r["year"]: r for r in rows if r["name"] == DEFAULT_STATE}
cols = ["Purchase loans", "Refinance loans", "Cash-out refi loans"]
for i, y in enumerate(YEARS):
    rr, sr = 9 + i, sel_rows[y]
    crit = f"tblData[State code],$I$7,tblData[Year],$H{rr + 1}"
    calc.write(rr, 7, y)
    for j, c in enumerate(cols):
        calc.write_formula(rr, 8 + j, f"=SUMIFS(tblData[{c}],{crit})", fmt["int"], sr["loans"][j])
    calc.write_formula(rr, 11, f"=SUMIFS(tblData[Total dollar volume],{crit})/SUMIFS(tblData[Total loans],{crit})", fmt["usd"], sr["avg"])
    calc.write_formula(rr, 12, f"=SUMIFS(tblData[Q4 HPI YoY change],{crit})", fmt["pct"], sr["q4_yoy"])
    calc.write(rr, 13, us["q4_yoy"][y], fmt["pct"])

# Dynamic chart titles (H19:H21)
titles = [
    ('"Loans originated by purpose, 2018-2025: "&$I$6', f"Loans originated by purpose, 2018-2025: {DEFAULT_STATE}"),
    ('"Q4 home price change, year over year: "&$I$6&" vs. U.S."', f"Q4 home price change, year over year: {DEFAULT_STATE} vs. U.S."),
    (f'"House price index (1991 Q1 = 100), 2015 Q1-{LATEST}: "&$I$6&" vs. U.S."', f"House price index (1991 Q1 = 100), 2015 Q1-{LATEST}: {DEFAULT_STATE} vs. U.S."),
]
calc.write(17, 7, "Chart titles", fmt["b"])
for i, (f_, v) in enumerate(titles):
    calc.write_formula(18 + i, 7, "=" + f_, None, v)

# Quarterly HPI matrix (P1:...) with a column for the selected state
codes = d["codes"]
first_c, last_c = 18, 18 + len(codes) - 1
calc.write_row(0, 15, ["Quarter", "U.S.", "Selected state"] + codes, fmt["h"])
sel_i = codes.index(sel["code"])
rng_cols = f"${xl_col_to_name(first_c)}${{r}}:${xl_col_to_name(last_c)}${{r}}"
for i, (label, usv, vals) in enumerate(d["hpi_matrix"], start=1):
    calc.write(i, 15, label); calc.write(i, 16, usv, fmt["idx"])
    calc.write_formula(i, 17, f"=INDEX({rng_cols.format(r=i + 1)},MATCH($I$7,{rng_cols.format(r=1)},0))", fmt["idx"], vals[sel_i])
    calc.write_row(i, first_c, vals, fmt["idx"])
QN = len(d["hpi_matrix"])

# Loans by state and year for the dashboard sparklines (A56:I107)
LR0 = 55
calc.write(LR0 - 1, 0, "Total loans by state and year (sparkline source)", fmt["b"])
calc.write_row(LR0, 0, ["State"] + YEARS, fmt["h"])
by_sy = {(r["name"], r["year"]): r["total_loans"] for r in rows}
for i, s in enumerate(sm, start=1):
    calc.write(LR0 + i, 0, s["name"])
    for j, y in enumerate(YEARS):
        f_ = f"=SUMIFS(tblData[Total loans],tblData[State],$A{LR0 + i + 1},tblData[Year],{xl_col_to_name(1 + j)}${LR0 + 1})"
        calc.write_formula(LR0 + i, 1 + j, f_, fmt["int"], by_sy[(s["name"], y)])
calc.freeze_panes(1, 0)

# ---------- Pivot sheet: cell preview of the PivotTable plus a PivotChart ----------
REGIONS = sorted({r["region"] for r in rows})
agg = {(g, y): [0, 0] for g in REGIONS for y in YEARS}
for r in rows:
    agg[(r["region"], r["year"])][0] += r["total_loans"]; agg[(r["region"], r["year"])][1] += r["total_vol"]
piv.write(0, 0, "PivotTable: loans and average loan size by Census region and year", fmt["title"])
piv.write(1, 0, "Source: CFPB HMDA originated loans, 2018-2025. Average loan size = total dollar volume / total loans (calculated field). Right-click > Refresh after you edit the Data table.", fmt["sub"])
piv.set_column(0, 0, 16); piv.set_column(1, 18, 12)
piv.write(2, 1, "Year"); piv.write(3, 1, "Loans (count)"); piv.write(3, 9, "Average loan size")
piv.write(3, 17, "Total Loans (count)"); piv.write(3, 18, "Total Average loan size"); piv.write(4, 0, "Region")
for j, y in enumerate(YEARS):
    piv.write(4, 1 + j, y); piv.write(4, 9 + j, y)
tot = lambda keys: [sum(agg[k][0] for k in keys), sum(agg[k][1] for k in keys)]
for i, g in enumerate(REGIONS + ["Grand Total"]):
    piv.write(5 + i, 0, g)
    for j, y in enumerate(YEARS + [None]):
        keys = [(gg, yy) for gg in (REGIONS if g == "Grand Total" else [g]) for yy in (YEARS if y is None else [y])]
        l, v = tot(keys)
        piv.write(5 + i, 1 + j if y else 17, l, fmt["int"]); piv.write(5 + i, 9 + j if y else 18, v / l, fmt["usd"])
piv.freeze_panes(5, 1)
pc = wb.add_chart({"type": "column"})
pl = wb.add_chart({"type": "line"})
for j, y in enumerate(YEARS):
    c = xl_col_to_name(1 + j); c2 = xl_col_to_name(9 + j)
    pc.add_series({"name": f"=Pivot!${c}$4:${c}$5", "categories": "=Pivot!$A$6:$A$9", "values": f"=Pivot!${c}$6:${c}$9",
                   "fill": {"color": VIRIDIS[j]}, "border": {"color": "#333333", "width": 0.5}})
    pl.add_series({"name": f"=Pivot!${c2}$4:${c2}$5", "categories": "=Pivot!$A$6:$A$9", "values": f"=Pivot!${c2}$6:${c2}$9",
                   "y2_axis": True, "line": {"none": True},
                   "marker": {"type": "diamond", "size": 8, "fill": {"color": VIRIDIS[j]}, "border": {"color": "#333333"}}})
pc.combine(pl)
pc.set_title({"name": "Loans originated (bars) and average loan size (diamonds) by region, 2018-2025", "name_font": {"size": 13}})
pc.set_x_axis({"name": "Census region", "name_font": {"size": 11}, "num_font": {"size": 10}})
pc.set_y_axis({"name": "Loans originated", "num_format": "#,##0", "name_font": {"size": 11}, "num_font": {"size": 10}, "major_gridlines": {"visible": True, "line": {"color": "#E5E7EB"}}})
pl.set_y2_axis({"name": "Average loan size ($)", "num_format": "$#,##0", "name_font": {"size": 11}, "num_font": {"size": 10}})
pc.set_legend({"position": "right", "font": {"size": 9}})
pc.set_size({"width": 1150, "height": 460})
piv.insert_chart("A13", pc)
piv.write(36, 0, "Source: CFPB HMDA, originated loans 2018-2025 (latest HMDA year: 2025).", fmt["note"])
piv.write(37, 0, FOOTER, fmt["note"])

# ---------- Dashboard ----------
dash.hide_gridlines(2); dash.set_zoom(80); dash.activate()
dash.set_column("A:A", 2); dash.set_column("B:B", 22); dash.set_column("C:J", 9); dash.set_column("K:L", 14)
dash.set_column("M:M", 3); dash.set_column("N:N", 12)
dash.set_row(0, 30)
dash.write(0, 1, "U.S. Housing Market Dashboard", fmt["title"])
dash.write(1, 1, f"Home prices: FHFA HPI (purchase-only, latest quarter {LATEST}). Loans: CFPB HMDA originations (2018-2025). HPI is an index (1991 Q1 = 100), not a price.", fmt["sub"])
dash.set_row(3, 24)
dash.write(3, 1, "Select a state  >", F(bold=True, font_size=12, align="right", valign="vcenter"))
dash.merge_range("C4:E4", DEFAULT_STATE, F(bold=True, font_size=12, bg_color="#FFF2CC", border=2, border_color="#B7791F", valign="vcenter"))
dash.data_validation("C4", {"validate": "list", "source": f"=Calc!{SR}", "input_title": "Pick a state",
                            "input_message": "Cards and charts update for this state."})
dash.write(3, 5, "Cards, charts, and the highlighted heat-map row update when you change the state.", fmt["note"])

st = "$C$4"
idx = lambda col: f"INDEX(Calc!${col}$2:${col}${NS + 1},MATCH({st},Calc!{SR},0))"
sumifs = lambda col, y: f"SUMIFS(tblData[{col}],tblData[State],{st},tblData[Year],{y})"
sel25, sel24 = sel_rows[2025], sel_rows[2024]
cards = [
    ("B6:C9", f"Home price change, YoY ({LATEST})", "=" + idx("D"), sel["yoy"], PCT,
     f'="U.S.: "&TEXT(Calc!$I$2,"{PCT}")', f"U.S.: {us['yoy']:+.1%}"),
    ("D6:F9", f"Home price change since 2019 Q4", "=" + idx("E"), sel["since"], PCT,
     f'="U.S.: "&TEXT(Calc!$I$3,"{PCT}")', f"U.S.: {us['since']:+.1%}"),
    ("G6:I9", "Loans originated (2025)", "=" + sumifs("Total loans", 2025), sel25["total_loans"], "#,##0",
     f'="vs. 2024: "&TEXT({sumifs("Total loans", 2025)}/{sumifs("Total loans", 2024)}-1,"{PCT}")',
     f"vs. 2024: {sel25['total_loans'] / sel24['total_loans'] - 1:+.1%}"),
    ("J6:L9", "Average loan size (2025)", f"={sumifs('Total dollar volume', 2025)}/{sumifs('Total loans', 2025)}", sel25["avg"], "$#,##0",
     '="U.S.: "&TEXT(Calc!$I$4,"$#,##0")', f"U.S.: ${us_avg25:,.0f}"),
]
card_bg = dict(bg_color="#EEF2F7", border=1, border_color="#C9D3E0")
dash.set_row(5, 20); dash.set_row(6, 22); dash.set_row(7, 22); dash.set_row(8, 18)
for rng, label, f_, val, nf, subf, subv in cards:
    c1, c2 = rng.split(":")
    col1, col2 = c1[0], c2[0]
    dash.merge_range(f"{col1}6:{col2}6", label, F(bold=True, font_size=10, font_color="#374151", align="center", **card_bg))
    dash.merge_range(f"{col1}7:{col2}8", "", F(bold=True, font_size=22, font_color="#1F4E79", align="center", valign="vcenter", num_format=nf, **card_bg))
    dash.write_formula(f"{col1}7", f_, F(bold=True, font_size=22, font_color="#1F4E79", align="center", valign="vcenter", num_format=nf, **card_bg), val)
    dash.merge_range(f"{col1}9:{col2}9", "", F(font_size=10, font_color="#4B5563", align="center", **card_bg))
    dash.write_formula(f"{col1}9", subf, F(font_size=10, font_color="#4B5563", align="center", **card_bg), subv)

# Heat map: states by year, Q4 HPI YoY change, with sparklines
H0 = 11  # header row index (row 12)
dash.write(H0 - 1, 1, "Heat map: Q4 home price change, year over year (FHFA HPI, purchase-only, index_nsa)", F(bold=True, font_size=12))
dash.write_row(H0, 1, ["State"] + YEARS + ["Price trend", "Loans trend"], fmt["h"])
q4 = {(r["name"], r["year"]): r["q4_yoy"] for r in rows}
for i, s in enumerate(sm):
    r_ = H0 + 1 + i
    dash.write(r_, 1, s["name"])
    for j, y in enumerate(YEARS):
        f_ = f"=SUMIFS(tblData[Q4 HPI YoY change],tblData[State],$B{r_ + 1},tblData[Year],{xl_col_to_name(2 + j)}${H0 + 1})"
        dash.write_formula(r_, 2 + j, f_, F(num_format="0.0%", align="center", font_size=10), q4[(s["name"], y)])
    dash.add_sparkline(r_, 10, {"range": f"Dashboard!C{r_ + 1}:J{r_ + 1}", "type": "column", "negative_points": True,
                                "series_color": "#5E3C99", "negative_color": "#E66101"})
    dash.add_sparkline(r_, 11, {"range": f"Calc!B{LR0 + 2 + i}:I{LR0 + 2 + i}", "markers": True, "high_point": True,
                                "series_color": "#0072B2", "high_color": "#D55E00"})
HL = H0 + NS  # last heat map row index
hm = f"C{H0 + 2}:J{HL + 1}"
dash.conditional_format(hm, {"type": "3_color_scale", "min_color": "#E66101", "mid_type": "num", "mid_value": 0,
                             "mid_color": "#F7F7F7", "max_color": "#8073AC"})
dash.conditional_format(f"B{H0 + 2}:J{HL + 1}", {"type": "formula", "criteria": f"=$B{H0 + 2}=$C$4",
                                                  "format": wb.add_format({"bold": True, "top": 2, "bottom": 2, "top_color": "#000000", "bottom_color": "#000000"})})
dash.write(HL + 2, 1, f"Source: FHFA HPI, Q4 vs. prior-year Q4, 2018-2025 (latest available quarter: {LATEST}). Orange = price decline, purple = price increase. Price trend = these values; loans trend = CFPB HMDA total originations, 2018-2025.", fmt["note"])
dash.write(HL + 3, 1, FOOTER, fmt["note"])

# Charts driven by the Calc helper ranges
def chart_base(kind, sub=None):
    c = wb.add_chart({"type": kind, **({"subtype": sub} if sub else {})})
    c.set_size({"width": 680, "height": 300})
    c.set_legend({"position": "bottom", "font": {"size": 10}})
    return c

c1 = chart_base("column", "stacked")
for j, p in enumerate(PURPOSES):
    col = xl_col_to_name(8 + j)
    c1.add_series({"name": f"=Calc!${col}$9", "categories": "=Calc!$H$10:$H$17", "values": f"=Calc!${col}$10:${col}$17", "fill": {"color": OKABE[j]}})
c1.set_title({"name": "=Calc!$H$19", "name_font": {"size": 12}})
c1.set_x_axis({"name": "HMDA year", "num_font": {"size": 10}})
c1.set_y_axis({"name": "Loans originated", "num_format": "#,##0", "num_font": {"size": 10}, "major_gridlines": {"visible": True, "line": {"color": "#E5E7EB"}}})

c2 = chart_base("column")
c2.add_series({"name": "=Calc!$I$6", "categories": "=Calc!$H$10:$H$17", "values": "=Calc!$M$10:$M$17", "fill": {"color": OKABE[0]}})
c2.add_series({"name": "U.S.", "categories": "=Calc!$H$10:$H$17", "values": "=Calc!$N$10:$N$17", "fill": {"color": OKABE[1]}})
c2.set_title({"name": "=Calc!$H$20", "name_font": {"size": 12}})
c2.set_x_axis({"name": "Year (Q4 vs. prior-year Q4)", "num_font": {"size": 10}, "label_position": "low"})
c2.set_y_axis({"name": "Change in HPI", "num_format": "0%", "num_font": {"size": 10}, "major_gridlines": {"visible": True, "line": {"color": "#E5E7EB"}}})

c3 = chart_base("line")
c3.add_series({"name": "=Calc!$I$6", "categories": f"=Calc!$P$2:$P${QN + 1}", "values": f"=Calc!$R$2:$R${QN + 1}", "line": {"color": OKABE[0], "width": 2.25}})
c3.add_series({"name": "U.S.", "categories": f"=Calc!$P$2:$P${QN + 1}", "values": f"=Calc!$Q$2:$Q${QN + 1}", "line": {"color": OKABE[1], "width": 2.25, "dash_type": "dash"}})
c3.set_title({"name": "=Calc!$H$21", "name_font": {"size": 12}})
c3.set_x_axis({"name": "Quarter", "num_font": {"size": 9}, "interval_unit": 4, "interval_tick": 4})
c3.set_y_axis({"name": "HPI (1991 Q1 = 100)", "num_format": "0", "num_font": {"size": 10}, "major_gridlines": {"visible": True, "line": {"color": "#E5E7EB"}}})

src = [
    "Source: CFPB HMDA, originated loans, 2018-2025 (latest HMDA year: 2025).",
    "Source: FHFA HPI, purchase-only, index_nsa. U.S. Q4 = average of Oct-Dec monthly index. Years 2018-2025.",
    f"Source: FHFA HPI, purchase-only, index_nsa. Latest quarter: {LATEST}. U.S. = average of 3 monthly values.",
]
for k, c in enumerate([c1, c2, c3]):
    top = 10 + 16 * k
    dash.insert_chart(top, 13, c)
    dash.write(top + 15, 13, src[k], fmt["note"])
dash.write(3, 13, "How to use", fmt["b"])
dash.write(4, 13, "1. Pick a state in the yellow box.  2. The cards and the three charts show that state.", fmt["note"])
dash.write(5, 13, f"3. The heat map shows all states. The selected state has a bold row.  Latest HPI quarter: {LATEST}.", fmt["note"])
dash.freeze_panes(4, 0)

# ---------- Notes ----------
notes.set_column("A:A", 30); notes.set_column("B:B", 70); notes.set_column("C:C", 40)
notes.write(0, 0, "Notes and sources", fmt["title"])
notes.write_row(2, 0, ["Source", "Link", "Used for"], fmt["h"])
srcs = [
    ("FHFA House Price Index (HPI) master file", "https://www.fhfa.gov/hpi/download/monthly/hpi_master.csv", "Heat map, home price cards and charts (traditional, purchase-only, index_nsa)"),
    ("CFPB HMDA Data Browser API", "https://ffiec.cfpb.gov/v2/data-browser-api/view/aggregations", "Loans and dollar volume by state, year, and loan purpose (originated loans only)"),
    ("U.S. Census Bureau regions and divisions", "https://www2.census.gov/geo/pdfs/maps-data/maps/reference/us_regdiv.pdf", "Region and division for each state"),
]
for i, (a, b, c) in enumerate(srcs, start=3):
    notes.write(i, 0, a); notes.write_url(i, 1, b, fmt["link"], b); notes.write(i, 2, c, fmt["wrap"])
defs = [
    ("Latest period", f"Latest complete HPI quarter: {LATEST}. HMDA years: 2018-2025."),
    ("HPI", "The HPI is an index, not a price. 1991 Q1 = 100 (January 1991 = 100 for monthly data)."),
    ("Q4 HPI YoY change", "State Q4 index_nsa divided by the same state's Q4 index_nsa one year earlier, minus 1."),
    ("State YoY change (cards)", f"State index_nsa for {LATEST} compared with the same quarter one year earlier."),
    ("U.S. YoY change", f"Average of the three monthly U.S. index_nsa values for {LATEST}, compared with the same quarter one year earlier."),
    ("Change since 2019 Q4", f"{LATEST} index compared with 2019 Q4 (the last quarter before the pandemic)."),
    ("Loans", "HMDA originated loans (action taken = 1). Purposes: Home purchase (1), Refinance (31), Cash-out refinance (32)."),
    ("Avg loan size", "Total dollar volume / total loans for the three loan purposes. The PivotTable uses the calculated field 'Weighted loan size' (= sum of dollar volume / sum of loans)."),
    ("Sheets", "Dashboard (state drop-down, KPI cards, charts, heat map, sparklines); Data (tblData table); Pivot (PivotTable and PivotChart); Calc (formula helpers for the dashboard)."),
    ("Rebuild", "Run: .venv/bin/python analysis/build_workbook.py (reads data/ only)."),
]
notes.write_row(8, 0, ["Item", "Definition"], fmt["h"])
for i, (a, b) in enumerate(defs, start=9):
    notes.write(i, 0, a, fmt["b"]); notes.write(i, 1, b, fmt["wrap"])
notes.write(len(defs) + 10, 0, "Facts from the data only. No forecasts and no investment advice.", fmt["note"])
notes.write(len(defs) + 11, 0, FOOTER, fmt["b"])
notes.freeze_panes(3, 0)

wb.close()
add_pivot(OUT, [h for h, _, _ in headers], table_rows, REGIONS, YEARS)
print("Wrote", OUT)
