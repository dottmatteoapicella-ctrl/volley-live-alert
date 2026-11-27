import json
from datetime import timedelta
from volley_feed import decode
from volley_odds import favorite_for
from volley_tracking import statistics

def label(row):
    league=row.get("league")
    league=league if isinstance(league,dict) else {"name":league}
    def field(v):
        if isinstance(v,dict): v=v.get("name")
        return v.strip() if isinstance(v,str) and v.strip() else "N/D"
    return [field(league.get("name")),field(league.get("country") or row.get("country")),field(league.get("gender") or row.get("gender"))]

def observe(state,row,records,best,now):
    if row.get("id") is None: return
    key=str(row["id"])
    rows=state.setdefault("league_coverage",{})
    r=rows.setdefault(key,{})
    old=r.get("label",["N/D"]*3)
    r["label"]=[a if a!="N/D" else b for a,b in zip(label(row),old)]
    r["last"]=now.isoformat()
    parsed=decode(row,best)
    r["decoded"]=bool(r.get("decoded") or parsed is not None)
    r["points"]=bool(r.get("points") or (parsed is not None and parsed[1] is not None))
    r["favorite"]=bool(r.get("favorite") or favorite_for(row,records) is not None)
    for a in state.get("alerts",{}).values():
        if a["match_id"]==key: a["coverage_label"]=r["label"]

def report(state,now):
    rows=state.setdefault("league_coverage",{})
    cutoff=(now-timedelta(days=30)).isoformat()
    for k in list(rows):
        if rows[k]["last"]<cutoff: del rows[k]
    groups={}
    def group(label):
        return groups.setdefault(tuple(label),{"live":0,"decoded":0,"points":0,"favorite":0,"alerts":{}})
    for r in rows.values():
        g=group(r["label"])
        g["live"]+=1
        for k in ("decoded","points","favorite"): g[k]+=bool(r.get(k))
    for k,a in state.get("alerts",{}).items():
        label=a.get("coverage_label") or rows.get(a["match_id"],{}).get("label",["N/D"]*3)
        group(label)["alerts"][k]=a
    for label,g in sorted(groups.items()):
        print("VOLLEY_LEAGUE_REPORT:",json.dumps({"league":label[0],"country":label[1],"gender":label[2],**{k:v for k,v in g.items() if k!="alerts"},"strategies":statistics({"alerts":g["alerts"]})},ensure_ascii=True))
    return groups
