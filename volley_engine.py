from volley_feed import decode
from volley_odds import favorite_for
from volley_strategy import signals
from volley_tracking import register,settle,statistics
from volley_telegram import alert_text

def process(state,row,records,best_of,telegram,persist,allow_alerts=True):
    parsed=decode(row,best_of)
    if parsed is None or row.get("id") is None:
        return False
    teams=[(row.get(k) or {}).get("name") for k in ("home","away")]
    if not all(isinstance(t,str) and t for t in teams):
        return False
    completed,current,winner=parsed
    match_id=str(row["id"])
    if settle(state,match_id,teams,completed,winner):
        persist()
    for r in state.get("alerts",{}).values():
        if r["match_id"]!=match_id or r["teams"]!=teams or r["result"] is None or not r.get("message_id") or r.get("edited"):
            continue
        if telegram.edit(r["message_id"],alert_text(r)):
            r["edited"]=True
            persist()
    if winner is not None or not allow_alerts:
        return True
    favorite=favorite_for(row,records)
    if favorite is None:
        return True
    idx=favorite["favorite"]
    for strategy,number in signals(idx,completed,current,best_of):
        key=register(state,match_id,strategy,number,idx,teams,favorite["odds"][idx])
        if key is None:
            continue
        persist()
        r=state["alerts"][key]
        r["message_id"]=telegram.send(alert_text(r))
        persist()
    return True
