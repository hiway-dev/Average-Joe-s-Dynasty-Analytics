"""Fetch all historical data for Average Joe's Dynasty (MFL) into data/ as JSON."""
import json
import time
import urllib.request
from pathlib import Path

# From the 2026 league export's history block: year -> (host, league_id)
HISTORY = {
    2009: ("www49", "71761"),
    2010: ("www45", "23239"),
    2011: ("www48", "16993"),
    2012: ("www48", "12092"),
    2013: ("www43", "43511"),
    2014: ("www48", "24866"),
    2015: ("www46", "13121"),
    2016: ("www48", "17313"),
    2017: ("www46", "17313"),
    2018: ("www46", "17313"),
    2019: ("www48", "17313"),
    2020: ("www47", "17313"),
    2021: ("www47", "17313"),
    2022: ("www47", "17313"),
    2023: ("www47", "17313"),
    2024: ("www47", "17313"),
    2025: ("www47", "17313"),
    2026: ("www47", "17313"),
}

DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)


def fetch(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (league-history-charts)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_one(url: str, out: Path, label: str):
    if out.exists():
        return
    try:
        data = fetch(url)
        out.write_text(json.dumps(data), encoding="utf-8")
        print(f"{label}: ok")
    except Exception as e:
        print(f"{label}: FAILED {e}")
    time.sleep(1.2)


def fetch_year(year: int, host: str, lid: str):
    base = f"https://{host}.myfantasyleague.com/{year}/export"
    for etype, extra in [("league", ""), ("rosters", ""), ("players", "&DETAILS=1"),
                         ("salaryAdjustments", ""), ("standings", "")]:
        fetch_one(f"{base}?TYPE={etype}&L={lid}&JSON=1{extra}",
                  DATA / f"{year}_{etype}.json", f"{year} {etype}")
    fetch_one(f"{base}?TYPE=playerScores&L={lid}&W=YTD&JSON=1",
              DATA / f"{year}_playerScores.json", f"{year} playerScores")
    # Weekly lineups (regular season weeks) for start/bench efficiency
    for w in range(1, 15):
        fetch_one(f"{base}?TYPE=weeklyResults&L={lid}&W={w}&JSON=1",
                  DATA / f"{year}_weeklyResults_{w:02d}.json", f"{year} weeklyResults w{w}")


if __name__ == "__main__":
    for year, (host, lid) in HISTORY.items():
        fetch_year(year, host, lid)
    print("done")
