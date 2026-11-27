import os,json,urllib.request,urllib.error
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from volley_state import load,save
from volley_strategy import reserve
from volley_odds import prematch_record,stamp
from volley_engine import process
from volley_tracking import statistics
import volley_coverage
from volley_telegram import Telegram

def sports_headers():
    return {"Authorization":"Bearer "+os.environ["SPORTSAPI_KEY"].strip(),"Accept":"application/json"}

def get(url,headers):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs): return None
    with urllib.request.build_opener(NoRedirect()).open(urllib.request.Request(url,headers=headers),timeout=25) as res:
        if url.startswith("https://api.sportsapi.app/"):
            print("SportsAPI HTTP",res.status)
            for k,v in res.headers.items():
                if "ratelimit" in k.lower() and str(v).isdigit(): print(k,v)
        return json.load(res)

def main():
    now=datetime.now(timezone.utc)
    token=os.environ["TELEGRAM_BOT_TOKEN"]
    chat=os.environ["TELEGRAM_CHAT_ID"]
    path="volley.enc"
    state=load(path,token,initialize=os.environ.get("VOLLEY_INITIALIZE")=="yes")
    def persist(): save(path,token,state)
    persist()
    budget=state.setdefault("budget",{})
    local=now.astimezone(ZoneInfo("Europe/Rome"))
    tg=Telegram(token,chat)
    pending=sorted({r["match_id"] for r in state.get("alerts",{}).values() if r.get("message_id") and (r["result"] is None or not r.get("edited"))})
    recovery_slot=now.strftime("%Y-%m-%dT%H:")+str(now.minute//30)
    if pending and state.get("recovery_slot")!=recovery_slot and reserve(budget,now.date().isoformat(),"results"):
        state["recovery_slot"]=recovery_slot
        cursor=state.get("recovery_cursor",0)
        mid=pending[cursor%len(pending)]
        state["recovery_cursor"]=cursor+1
        persist()
        if mid.isdigit():
            try:
                detail=get("https://api.sportsapi.app/v2/fixtures/"+mid,sports_headers())
                row=detail.get("data") if isinstance(detail,dict) else None
                if isinstance(row,dict) and str(row.get("id"))==mid:
                    fmt=row.get("matchFormat")
                    process(state,row,[],fmt if type(fmt) is int and fmt in (3,5) else None,tg,persist,False)
            except urllib.error.HTTPError as e:
                if e.code in (401,403,429): budget["blocked"]=True; persist()
                print("Recovery HTTP",e.code)
            except (OSError,ValueError): print("Recovery unavailable")
    if not 8<=local.hour<23:
        print("Outside live window",json.dumps(statistics(state)))
        return
    slot=now.strftime("%Y-%m-%dT%H:")+str(now.minute//15)
    if state.get("live_slot")==slot: return
    state["live_slot"]=slot
    if not reserve(budget,now.date().isoformat(),"live"):
        print("Live skipped: budget or provider block",json.dumps(budget))
        volley_coverage.report(state,now)
        persist()
        return
    persist()
    try:
        payload=get("https://api.sportsapi.app/v2/livescores?sport=volleyball",sports_headers())
    except urllib.error.HTTPError as e:
        if e.code in (401,403,429): budget["blocked"]=True; persist()
        print("SportsAPI HTTP",e.code)
        for k,v in (e.headers or {}).items():
            if ("ratelimit" in k.lower() or k.lower()=="retry-after") and str(v).isdigit(): print(k,v)
        return
    except (OSError,ValueError):
        print("SportsAPI unavailable"); return
    rows=payload.get("data") if isinstance(payload,dict) else None
    if not isinstance(rows,list): return
    last=stamp(state.get("odds_attempt"))
    if not last or (now-last).total_seconds()>=10800:
        state["odds_attempt"]=now.isoformat()
        persist()
        try:
            odds=get("https://moviodds.com/odds?sport=volleyball",{"X-API-Key":os.environ["MOVIODDS_API_KEY"],"Accept":"application/json"})
            matches=odds.get("matches",[]) if isinstance(odds,dict) else []
            cache=state.setdefault("odds",{})
            for m in matches:
                if not isinstance(m,dict) or m.get("id") is None: continue
                rec=prematch_record(m,now)
                if rec: cache[str(m["id"])]=rec
            state["odds"]={k:v for k,v in cache.items() if stamp(v["start"]) and (now-stamp(v["start"])).total_seconds()<259200}
            persist()
        except (OSError,ValueError):
            print("MoviOdds unavailable")
    tg=Telegram(token,chat)
    accepted=0
    for row in rows:
        if not isinstance(row,dict): continue
        # Only explicit verified format values; unknown formats are skipped.
        fmt=row.get("matchFormat")
        best=fmt if type(fmt) is int and fmt in (3,5) else None
        records=list(state.get("odds",{}).values())
        volley_coverage.observe(state,row,records,best,now)
        accepted+=bool(process(state,row,records,best,tg,persist))
        volley_coverage.observe(state,row,records,best,now)
    volley_coverage.report(state,now)
    persist()
    print("Live rows",len(rows),"decoded",accepted,"cached odds",len(state.get("odds",{})))
    print("Budget",json.dumps(budget))
    print("Statistics",json.dumps(statistics(state)))
if __name__=="__main__": main()
