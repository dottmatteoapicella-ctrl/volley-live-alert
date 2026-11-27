import math
import unicodedata
from datetime import datetime, timedelta, timezone

def name_key(value):
    if not isinstance(value,str):
        return ""
    return "".join(c for c in unicodedata.normalize("NFKD",value).casefold() if c.isalnum())

def stamp(value):
    try:
        dt=datetime.fromisoformat(value.replace("Z","+00:00"))
        return dt.astimezone(timezone.utc) if dt.tzinfo else None
    except (ValueError,TypeError,AttributeError):
        return None

def prematch_record(match,now):
    if match.get("in_play") is not False or match.get("stale") not in (None,False):
        return None
    start=stamp(match.get("kickoff_utc"))
    polled=stamp(match.get("polled_at"))
    if match.get("stale") is None and (not polled or not 0 <= (now-polled).total_seconds() <= 900):
        return None
    names=[name_key(match.get(k)) for k in ("home","away")]
    if not start or start<=now+timedelta(minutes=5) or not all(names) or names[0]==names[1]:
        return None
    prices={}
    for q in match.get("quotes") or []:
        if not isinstance(q,dict) or str(q.get("group_name","")).casefold()!="winner":
            continue
        if q.get("suspended") not in (None,False) or str(q.get("phase","")).casefold()=="inplay":
            continue
        ts=stamp(q.get("ts"))
        if q.get("suspended") is None and (not ts or not 0 <= (now-ts).total_seconds() <= 7200 or ts>=start):
            continue
        side=name_key(q.get("side"))
        if side not in names:
            continue
        try: price=float(q.get("odds_dec"))
        except (ValueError,TypeError): continue
        if not math.isfinite(price) or price<=1:
            continue
        if side in prices and prices[side]!=price:
            return None
        prices[side]=price
    if len(prices)!=2 or prices[names[0]]==prices[names[1]]:
        return None
    return {"names":names,"prices":prices,"start":start.isoformat(),"captured":now.isoformat()}

def favorite_for(fixture,records):
    start=stamp(fixture.get("startTime"))
    names=[name_key((fixture.get(k) or {}).get("name")) for k in ("home","away")]
    if not start or not all(names) or names[0]==names[1]:
        return None
    candidates=[]
    for r in records:
        kickoff=stamp(r.get("start"))
        captured=stamp(r.get("captured"))
        if not kickoff or not captured or captured>=min(start,kickoff):
            continue
        if set(r["names"])!=set(names) or abs((kickoff-start).total_seconds())>3600:
            continue
        candidates.append(r)
    if len(candidates)!=1:
        return None
    prices=candidates[0]["prices"]
    return {"favorite":int(prices[names[1]]<prices[names[0]]),"odds":[prices[n] for n in names]}
