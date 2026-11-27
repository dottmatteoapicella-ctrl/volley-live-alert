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

def prematch_diagnostic(match,now):
    if match.get("in_play") is not False or match.get("stale") not in (None,False):
        return None,"missing_or_equal_prices","conflicting_prices","invalid_identity_or_kickoff","missing_or_stale_poll","not_prematch_or_stale"
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
    return {"names":names,"prices":prices,"start":start.isoformat(),"captured":now.isoformat(),"league":name_key(match.get("league"))},"accepted"

def prematch_record(match,now):
    return prematch_diagnostic(match,now)[0]

def legacy_favorite_for(fixture,records):
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

def favorite_diagnostic(fixture,records):
    mid=str(fixture.get("id",""))
    if not mid.startswith("moviodds:"):
        result=legacy_favorite_for(fixture,records)
        return result,"legacy_matched" if result else "legacy_unmatched"
    exact=[r for r in records if r.get("fixture_id")==mid]
    if not exact:
        result,reason=verified_fallback(fixture,records)
        return (result,"matched_verified_fallback") if result else (None,"missing_prematch_id")
    if len(exact)!=1: return None,"duplicate_id"
    r=exact[0]
    names=[name_key((fixture.get(k) or {}).get("name")) for k in ("home","away")]
    if not all(names) or names[0]==names[1] or set(names)!=set(r.get("names",[])):
        return None,"team_mismatch"
    start=stamp(fixture.get("startTime"))
    kickoff=stamp(r.get("start"))
    captured=stamp(r.get("captured"))
    if not start or not kickoff or not captured: return None,"missing_timestamp"
    if captured>=min(start,kickoff): return None,"not_prematch"
    if abs((kickoff-start).total_seconds())>3600: return None,"kickoff_mismatch"
    try: prices=[r["prices"][n] for n in names]
    except (KeyError,TypeError): return None,"invalid_prices"
    if any(type(x) not in (int,float) or not math.isfinite(x) or x<=1 for x in prices) or prices[0]==prices[1]:
        return None,"invalid_prices"
    return {"favorite":int(prices[1]<prices[0]),"odds":prices},"matched_id"

def favorite_for(fixture,records):
    return favorite_diagnostic(fixture,records)[0]

def verified_fallback(fixture,records):
    """Strict fallback only for missing IDs; no fuzzy names."""
    mid=str(fixture.get("id",""))
    names=[name_key((fixture.get(k) or {}).get("name")) for k in ("home","away")]
    start=stamp(fixture.get("startTime"))
    league=name_key(fixture.get("league"))
    if not start or not all(names) or names[0]==names[1]:
        return None,"missing_live_identity"
    pairs=[r for r in records if r.get("fixture_id")!=mid and set(r.get("names",[]))==set(names)]
    if not pairs:
        return None,"no_cached_team_pair"
    timed=[]
    for r in pairs:
        kickoff=stamp(r.get("start"))
        captured=stamp(r.get("captured"))
        if kickoff and captured and captured<min(start,kickoff) and abs((kickoff-start).total_seconds())<=1800:
            timed.append(r)
    if not timed:
        return None,"no_valid_prematch_time"
    if len(timed)!=1:
        return None,"ambiguous_team_time"
    r=timed[0]
    if not league or not r.get("league"):
        return None,"candidate_league_unknown"
    if r["league"]!=league:
        return None,"candidate_league_mismatch"
    candidate=dict(r,fixture_id=mid)
    result,reason=favorite_diagnostic(fixture,[candidate])
    return (result,"unique_verified_candidate") if result else (None,"candidate_"+reason)


def shadow_matching_reason(fixture,records):
    return verified_fallback(fixture,records)[1]
