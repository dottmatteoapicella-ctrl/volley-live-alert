import re
from volley_odds import stamp
from volley_strategy import set_winner

def adapt(m,now,final=False):
    if not isinstance(m,dict): return None
    mid=m.get("fixture_id" if final else "id")
    names=[m.get(k) for k in ("home","away")]
    if not mid or not all(isinstance(n,str) and n.strip() for n in names) or names[0]==names[1]: return None
    if final:
        if m.get("status")!="finished" or not stamp(m.get("finished_at")) or stamp(m["finished_at"])>now: return None
    else:
        polled=stamp(m.get("polled_at"))
        if m.get("in_play") is not True or m.get("stale") is True or not polled or not 0<=(now-polled).total_seconds()<=90: return None
    raw=m.get("final_score" if final else "score")
    if not isinstance(raw,str) or not re.fullmatch(r"\d+-\d+(,\d+-\d+){0,4}",raw): return None
    pairs=[tuple(map(int,p.split("-"))) for p in raw.split(",")]
    if final:
        periods=m.get("periods")
        if not isinstance(periods,list) or len(periods)!=len(pairs) or any(not isinstance(p,dict) or p.get("name")!=f"Set {i+1}" or p.get("score")!=raw.split(",")[i] for i,p in enumerate(periods)): return None
    # Standard best-of-five only when demonstrated by a fourth/fifth set or a three-set winner.
    # Otherwise preserve ambiguity; do not generate alerts that depend on the format.
    fmt=5 if len(pairs)>=4 else None
    completed=[]
    for i,(a,b) in enumerate(pairs):
        target=15 if i==4 else 25
        w=set_winner(a,b,target)
        if i==2 and fmt is None and w is None and final: w=set_winner(a,b,15)
        if w is None:
            if final or i!=len(pairs)-1: return None
            break
        if not final and i==len(pairs)-1: return None
        completed.append(w)
    if final:
        if max(completed.count(0),completed.count(1))==3: fmt=5
        elif max(completed.count(0),completed.count(1))==2: fmt=3
        else: return None
    if not final and len(completed)==2 and completed[0]==completed[1]: fmt=5
    row={"id":"moviodds:"+str(mid),"home":{"name":names[0]},"away":{"name":names[1]},"league":m.get("league"),"startTime":m.get("kickoff_utc"),"stale":False,"awarded":False,"status":{"type":"finished" if final else "inprogress","period":"period"+str(len(completed)+1)}}
    for side,k in enumerate(("homeScore","awayScore")):
        row[k]={"current":completed.count(side),"periods":{f"period{i+1}":p[side] for i,p in enumerate(pairs)}}
    return row,fmt

def reserve(b,now,kind):
    day=now.date().isoformat()
    month=day[:7]
    if b.get("month")!=month: b.update(month=month,monthly=0)
    if b.get("day")!=day: b.update(day=day,live=0,results=0,blocked=False)
    if b.get("blocked") or b["monthly"]>=1178 or b[kind]>=(30 if kind=="live" else 8): return False
    b[kind]+=1
    b["monthly"]+=1
    return True
