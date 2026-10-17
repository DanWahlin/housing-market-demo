"""Download public U.S. housing data into data/.

Sources (public U.S. government data, no API key):
- FHFA House Price Index: https://www.fhfa.gov/data/hpi/datasets
- CFPB HMDA Data Browser API: https://ffiec.cfpb.gov/documentation/api/data-browser/

Run: python3 scripts/fetch_data.py
"""

import csv
import io
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
HPI_URL = "https://www.fhfa.gov/hpi/download/monthly/hpi_master.csv"
HMDA_URL = (
    "https://ffiec.cfpb.gov/v2/data-browser-api/view/aggregations"
    "?years={year}&states={state}&actions_taken=1&loan_purposes=1,31,32"
)
HMDA_YEARS = range(2018, 2026)
PURPOSES = {"1": "Home purchase", "31": "Refinance", "32": "Cash-out refinance"}

# code, name, FIPS, census region, census division
STATES = [
    ("AL", "Alabama", "01", "South", "East South Central"),
    ("AK", "Alaska", "02", "West", "Pacific"),
    ("AZ", "Arizona", "04", "West", "Mountain"),
    ("AR", "Arkansas", "05", "South", "West South Central"),
    ("CA", "California", "06", "West", "Pacific"),
    ("CO", "Colorado", "08", "West", "Mountain"),
    ("CT", "Connecticut", "09", "Northeast", "New England"),
    ("DE", "Delaware", "10", "South", "South Atlantic"),
    ("DC", "District of Columbia", "11", "South", "South Atlantic"),
    ("FL", "Florida", "12", "South", "South Atlantic"),
    ("GA", "Georgia", "13", "South", "South Atlantic"),
    ("HI", "Hawaii", "15", "West", "Pacific"),
    ("ID", "Idaho", "16", "West", "Mountain"),
    ("IL", "Illinois", "17", "Midwest", "East North Central"),
    ("IN", "Indiana", "18", "Midwest", "East North Central"),
    ("IA", "Iowa", "19", "Midwest", "West North Central"),
    ("KS", "Kansas", "20", "Midwest", "West North Central"),
    ("KY", "Kentucky", "21", "South", "East South Central"),
    ("LA", "Louisiana", "22", "South", "West South Central"),
    ("ME", "Maine", "23", "Northeast", "New England"),
    ("MD", "Maryland", "24", "South", "South Atlantic"),
    ("MA", "Massachusetts", "25", "Northeast", "New England"),
    ("MI", "Michigan", "26", "Midwest", "East North Central"),
    ("MN", "Minnesota", "27", "Midwest", "West North Central"),
    ("MS", "Mississippi", "28", "South", "East South Central"),
    ("MO", "Missouri", "29", "Midwest", "West North Central"),
    ("MT", "Montana", "30", "West", "Mountain"),
    ("NE", "Nebraska", "31", "Midwest", "West North Central"),
    ("NV", "Nevada", "32", "West", "Mountain"),
    ("NH", "New Hampshire", "33", "Northeast", "New England"),
    ("NJ", "New Jersey", "34", "Northeast", "Middle Atlantic"),
    ("NM", "New Mexico", "35", "West", "Mountain"),
    ("NY", "New York", "36", "Northeast", "Middle Atlantic"),
    ("NC", "North Carolina", "37", "South", "South Atlantic"),
    ("ND", "North Dakota", "38", "Midwest", "West North Central"),
    ("OH", "Ohio", "39", "Midwest", "East North Central"),
    ("OK", "Oklahoma", "40", "South", "West South Central"),
    ("OR", "Oregon", "41", "West", "Pacific"),
    ("PA", "Pennsylvania", "42", "Northeast", "Middle Atlantic"),
    ("RI", "Rhode Island", "44", "Northeast", "New England"),
    ("SC", "South Carolina", "45", "South", "South Atlantic"),
    ("SD", "South Dakota", "46", "Midwest", "West North Central"),
    ("TN", "Tennessee", "47", "South", "East South Central"),
    ("TX", "Texas", "48", "South", "West South Central"),
    ("UT", "Utah", "49", "West", "Mountain"),
    ("VT", "Vermont", "50", "Northeast", "New England"),
    ("VA", "Virginia", "51", "South", "South Atlantic"),
    ("WA", "Washington", "53", "West", "Pacific"),
    ("WV", "West Virginia", "54", "South", "South Atlantic"),
    ("WI", "Wisconsin", "55", "Midwest", "East North Central"),
    ("WY", "Wyoming", "56", "West", "Mountain"),
]


def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "curl/8.7.1"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))


def write(name, header, rows):
    with open(DATA / name, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"data/{name}: {len(rows):,} rows")


def num(v):
    return round(float(v), 2) if v not in ("", None) else ""


def fetch_hpi():
    names = {s[0]: s[1] for s in STATES}
    state, metro, us = [], [], []
    for r in csv.DictReader(io.StringIO(get(HPI_URL).decode("utf-8"))):
        key = (r["hpi_type"], r["hpi_flavor"], r["frequency"], r["level"])
        if key == ("traditional", "purchase-only", "quarterly", "State") and r["place_id"] in names:
            state.append([r["place_id"], names[r["place_id"]], r["yr"], r["period"], num(r["index_nsa"]), num(r["index_sa"])])
        elif key == ("traditional", "purchase-only", "quarterly", "MSA"):
            metro.append([r["place_id"], r["place_name"], r["yr"], r["period"], num(r["index_nsa"]), num(r["index_sa"])])
        elif key == ("traditional", "purchase-only", "monthly", "USA or Census Division"):
            us.append([r["place_id"], r["place_name"], r["yr"], r["period"], num(r["index_nsa"]), num(r["index_sa"])])
    write("hpi_state_quarterly.csv", ["state_code", "state_name", "year", "quarter", "index_nsa", "index_sa"], state)
    write("hpi_metro_quarterly.csv", ["cbsa_code", "metro_name", "year", "quarter", "index_nsa", "index_sa"], metro)
    write("hpi_us_division_monthly.csv", ["place_id", "place_name", "year", "month", "index_nsa", "index_sa"], us)


def fetch_hmda():
    jobs = [(s[0], y) for s in STATES for y in HMDA_YEARS]

    def one(job):
        code, year = job
        data = json.loads(get(HMDA_URL.format(year=year, state=code)))
        return [[code, year, PURPOSES[a["loan_purposes"]], a["count"], int(a["sum"])] for a in data["aggregations"]]

    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = [row for result in pool.map(one, jobs) for row in result]
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    write("hmda_state_originations.csv", ["state_code", "year", "loan_purpose", "loans", "dollar_volume"], rows)


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    write("states.csv", ["state_code", "state_name", "fips", "region", "division"], STATES)
    fetch_hpi()
    fetch_hmda()
