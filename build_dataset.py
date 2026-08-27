"""Combine per-year MFL exports in data/ into data/combined.json for the dashboard."""
import json
from pathlib import Path

DATA = Path(__file__).parent / "data"
YEARS = list(range(2009, 2027))

POS_GROUPS = {
    "QB": "QB", "RB": "RB", "WR": "WR", "TE": "TE",
    "DT": "DL", "DE": "DL", "LB": "LB", "CB": "DB", "S": "DB",
}


def as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def main():
    # Master player map (later years overwrite for freshest team info)
    players = {}
    for y in YEARS:
        for p in as_list(json.load(open(DATA / f"{y}_players.json"))["players"]["player"]):
            players[p["id"]] = {
                "name": p.get("name", ""),
                "pos": p.get("position", ""),
                "team": p.get("team", ""),
            }

    # YTD fantasy points per player per year
    points = {}  # year -> {pid: pts}
    for y in YEARS:
        f = DATA / f"{y}_playerScores.json"
        if not f.exists():
            continue
        ps = json.load(open(f)).get("playerScores", {})
        points[y] = {p["id"]: float(p.get("score") or 0) for p in as_list(ps.get("playerScore"))}

    # Weekly start/bench efficiency per franchise per year,
    # plus starter-only points per player per year
    eff = {}         # year -> {fid: {"act": actual_pts, "opt": optimal_pts}}
    starter_pts = {}  # year -> {pid: pts scored in weeks started}
    starter_wks = {}  # year -> {pid: number of weeks started}
    for y in YEARS:
        for f in sorted(DATA.glob(f"{y}_weeklyResults_*.json")):
            wr = json.load(open(f)).get("weeklyResults", {})
            for fr in as_list(wr.get("franchise")):
                for p in as_list(fr.get("player")):
                    if p.get("status") != "starter":
                        continue
                    try:
                        sc = float(p.get("score") or 0)
                    except ValueError:
                        sc = 0.0
                    sp = starter_pts.setdefault(y, {})
                    sp[p["id"]] = sp.get(p["id"], 0.0) + sc
                    sw = starter_wks.setdefault(y, {})
                    sw[p["id"]] = sw.get(p["id"], 0) + 1
            for fr in as_list(wr.get("franchise")):
                try:
                    act, opt = float(fr.get("score") or 0), float(fr.get("opt_pts") or 0)
                except ValueError:
                    continue
                if opt <= 0:
                    continue
                e = eff.setdefault(y, {}).setdefault(fr["id"], {"act": 0.0, "opt": 0.0})
                e["act"] += act
                e["opt"] += opt

    franchise_names = {}   # year -> {fid: name}
    current_names = {}     # fid -> latest name
    caps = {}
    rows = []
    for y in YEARS:
        lg = json.load(open(DATA / f"{y}_league.json"))["league"]
        caps[y] = float(lg.get("salaryCapAmount") or 0)
        fnames = {f["id"]: f["name"] for f in as_list(lg["franchises"]["franchise"])}
        franchise_names[y] = fnames
        current_names.update(fnames)

        rosters = json.load(open(DATA / f"{y}_rosters.json"))["rosters"]
        for fr in as_list(rosters["franchise"]):
            fid = fr["id"]
            for p in as_list(fr.get("player")):
                info = players.get(p["id"], {})
                pos = info.get("pos", "")
                try:
                    sal = float(p.get("salary") or 0)
                except ValueError:
                    sal = 0.0
                rows.append({
                    "y": y,
                    "f": fid,
                    "pid": p["id"],
                    "n": info.get("name", f"Unknown {p['id']}"),
                    "pos": pos,
                    "pg": POS_GROUPS.get(pos, "Other"),
                    "s": sal,
                    "cy": p.get("contractYear", ""),
                    "ci": p.get("contractInfo", ""),
                    "st": p.get("status", ""),
                    "pts": round(points.get(y, {}).get(p["id"], 0), 2),
                    "spts": round(starter_pts.get(y, {}).get(p["id"], 0), 2),
                    "sw": starter_wks.get(y, {}).get(p["id"], 0),
                })

    out = {
        "years": YEARS,
        "caps": caps,
        "franchises": {fid: {"current": current_names[fid],
                             "byYear": {y: franchise_names[y].get(fid, "") for y in YEARS}}
                       for fid in sorted(current_names)},
        "rows": rows,
        "efficiency": {y: {fid: {"act": round(e["act"], 1), "opt": round(e["opt"], 1)}
                           for fid, e in fids.items()}
                       for y, fids in eff.items()},
    }
    (DATA / "combined.json").write_text(json.dumps(out), encoding="utf-8")
    print(f"rows: {len(rows)}, players: {len({r['pid'] for r in rows})}")


if __name__ == "__main__":
    main()
