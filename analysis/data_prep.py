"""Load data/ CSVs and compute the shared metrics used by the workbook."""
import csv
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
YEARS = list(range(2018, 2026))
PURPOSES = ["Home purchase", "Refinance", "Cash-out refinance"]


def read(name):
    with open(DATA / name, newline="") as f:
        return list(csv.DictReader(f))


def load():
    states = sorted(read("states.csv"), key=lambda r: r["state_name"])
    hpi = {(r["state_code"], int(r["year"]), int(r["quarter"])): float(r["index_nsa"])
           for r in read("hpi_state_quarterly.csv")}
    us_month = {(int(r["year"]), int(r["month"])): float(r["index_nsa"])
                for r in read("hpi_us_division_monthly.csv") if r["place_id"] == "USA"}
    hmda = defaultdict(lambda: [0, 0])
    for r in read("hmda_state_originations.csv"):
        hmda[(r["state_code"], int(r["year"]), r["loan_purpose"])] = [int(r["loans"]), int(r["dollar_volume"])]

    codes = [s["state_code"] for s in states]
    quarters = sorted({(y, q) for (_, y, q) in hpi})
    latest = max(k for k in quarters if all((c, *k) in hpi for c in codes))
    ly, lq = latest

    def us_q(y, q):
        vals = [us_month[(y, m)] for m in range(3 * q - 2, 3 * q + 1)]
        return sum(vals) / 3

    rows = []
    for s in states:
        c = s["state_code"]
        for y in YEARS:
            loans = [hmda[(c, y, p)][0] for p in PURPOSES]
            vols = [hmda[(c, y, p)][1] for p in PURPOSES]
            tl, tv = sum(loans), sum(vols)
            rows.append({
                "code": c, "name": s["state_name"], "region": s["region"], "division": s["division"], "year": y,
                "loans": loans, "vols": vols, "total_loans": tl, "total_vol": tv,
                "avg": round(tv / tl, 2) if tl else 0,
                "q4_yoy": round(hpi[(c, y, 4)] / hpi[(c, y - 1, 4)] - 1, 6),
            })

    state_metrics = [{
        "code": s["state_code"], "name": s["state_name"], "region": s["region"],
        "yoy": hpi[(s["state_code"], ly, lq)] / hpi[(s["state_code"], ly - 1, lq)] - 1,
        "since": hpi[(s["state_code"], ly, lq)] / hpi[(s["state_code"], 2019, 4)] - 1,
        "index": hpi[(s["state_code"], ly, lq)],
    } for s in states]

    us = {
        "yoy": us_q(ly, lq) / us_q(ly - 1, lq) - 1,
        "since": us_q(ly, lq) / us_q(2019, 4) - 1,
        "q4_yoy": {y: us_q(y, 4) / us_q(y - 1, 4) - 1 for y in YEARS},
    }
    qrange = [k for k in quarters if (2015, 1) <= k <= latest]
    hpi_matrix = [(f"{y} Q{q}", round(us_q(y, q), 2), [hpi[(c, y, q)] for c in codes]) for (y, q) in qrange]
    return {"states": states, "codes": codes, "rows": rows, "state_metrics": state_metrics,
            "us": us, "latest": latest, "hpi_matrix": hpi_matrix}
