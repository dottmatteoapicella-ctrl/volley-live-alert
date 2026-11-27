from volley_feed import decode
from volley_strategy import signals
from volley_odds import favorite_for

def observe(state,row,records,best,now):
    day=now.date().isoformat()
    d=state.setdefault("health",{})
    if d.get("day")!=day:
        d.clear()
        d.update(day=day,matches={})
    if row.get("id") is None: return
    m=d["matches"].setdefault(str(row["id"]),{})
    parsed=decode(row,best)
    favorite=favorite_for(row,records)
    m["decoded"]=bool(m.get("decoded") or parsed is not None)
    m["favorite"]=bool(m.get("favorite") or favorite is not None)
    if parsed is None or parsed[2] is not None or favorite is not None: return
    completed,current,_=parsed
    keys=set(m.get("hypothetical",[]))
    for side in (0,1):
        for strategy,n in signals(side,completed,current,best or 5):
            keys.add(f"{side}:{strategy}:{n}")
    m["hypothetical"]=sorted(keys)

def summary(state,now):
    d=state.get("health",{})
    matches=d.get("matches",{}) if d.get("day")==now.date().isoformat() else {}
    budget=state.get("budget",{})
    if budget.get("day")!=now.date().isoformat(): budget={}
    alerts=[a for a in state.get("alerts",{}).values() if a.get("message_id")]
    return ("🏐 Volley — diagnostica giornaliera (UTC)\n"
            f"Partite uniche: {len(matches)}\n"
            f"Punteggi validi: {sum(bool(m.get('decoded')) for m in matches.values())}\n"
            f"Favorite associate: {sum(bool(m.get('favorite')) for m in matches.values())}\n"
            f"Partite con condizioni ipotetiche senza favorita: {sum(bool(m.get('hypothetical')) for m in matches.values())}\n"
            f"Alert storici: {len(alerts)} | Esiti verificati: {sum(type(a.get('result')) is bool for a in alerts)}\n"
            f"Budget interno: {budget.get('live',0)+budget.get('results',0)}/90\n"
            f"Blocco provider: {'SI' if budget.get('blocked') else 'NO'}")

def daily(state,now,local,tg,persist):
    if local.hour!=23: return
    day=local.date().isoformat()
    if state.get("health_sent_day")==day: return
    state["health_sent_day"]=day
    persist()
    tg.send(summary(state,now))
