"""Tracking primitives; callers must persist before external delivery."""
from volley_strategy import outcome

def register(state,match_id,strategy,set_number,favorite,teams,prematch,live_odds=None):
    if strategy not in ("volley1","volley2","volley3","volley4") or favorite not in (0,1):
        return None
    key=f"{match_id}:{strategy}:{set_number if strategy=='volley3' else 0}"
    alerts=state.setdefault("alerts",{})
    if key in alerts:
        return None
    alerts[key]={"match_id":str(match_id),"strategy":strategy,"set_number":set_number,
                 "favorite":favorite,"teams":list(teams),"prematch":prematch,
                 "live_odds":live_odds,"result":None,"message_id":None}
    return key

def settle(state,match_id,teams,completed,final_winner=None):
    changed=[]
    for key,r in state.get("alerts",{}).items():
        if r["match_id"]!=str(match_id) or r["teams"]!=list(teams) or r["result"] is not None:
            continue
        result=outcome(r["strategy"],r["favorite"],r["set_number"],completed,final_winner)
        if result is not None:
            r["result"]=result
            changed.append(key)
    return changed

def statistics(state):
    import math
    report={}
    for strategy in ("volley1","volley2","volley3","volley4"):
        rows=[r for r in state.get("alerts",{}).values() if r["strategy"]==strategy and r.get("message_id")]
        verified=[r for r in rows if type(r["result"]) is bool]
        priced=[r for r in verified if type(r.get("live_odds")) in (float,int) and math.isfinite(r["live_odds"]) and r["live_odds"]>1]
        wins=sum(r["result"] for r in verified)
        report[strategy]={"alerts":len(rows),"wins":wins,"losses":len(verified)-wins,
                          "pending":len(rows)-len(verified),"priced":len(priced),
                          "success_pct":100*wins/len(verified) if verified else None,
                          "roi_pct":100*sum(r["live_odds"]-1 if r["result"] else -1 for r in priced)/len(priced) if priced else None}
    return report
