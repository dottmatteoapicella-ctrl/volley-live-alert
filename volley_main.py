import os,json,urllib.request,urllib.error
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from volley_state import load,save
from volley_odds import prematch_record,stamp,favorite_diagnostic
from volley_engine import process
from volley_tracking import statistics
from volley_moviodds import adapt,reserve
import volley_coverage,volley_health
from volley_telegram import Telegram

def moviodds_headers():
    return {"X-API-Key":os.environ["MOVIODDS_API_KEY"].strip(),"Accept":"application/json"}

def get(path):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs): return None
    req=urllib.request.Request("https://moviodds.com"+path,headers=moviodds_headers())
    with urllib.request.build_opener(NoRedirect()).open(req,timeout=25) as res:
        print("MoviOdds HTTP",res.status)
        return json.load(res)

def main():
    now=datetime.now(timezone.utc)
    local=now.astimezone(ZoneInfo("Europe/Rome"))
    token=os.environ["TELEGRAM_BOT_TOKEN"]
    state=load("volley.enc",token,initialize=os.environ.get("VOLLEY_INITIALIZE")=="yes")
    def persist(): save("volley.enc",token,state)
    budget=state.setdefault("moviodds_budget",{})
    tg=Telegram(token,os.environ["TELEGRAM_CHAT_ID"])
    def request(kind,slot,path):
        key="moviodds_"+kind+"_slot"
        if state.get(key)==slot:
            print("VOLLEY_REQUEST",kind,"skipped_slot")
            return None
        if not reserve(budget,now,kind):
            print("VOLLEY_REQUEST",kind,"skipped_budget")
            return None
        state[key]=slot
        persist()
        try: return get(path)
        except urllib.error.HTTPError as e:
            if e.code in (401,403,429): budget["blocked"]=True; persist()
            print("MoviOdds HTTP",e.code)
        except (OSError,ValueError): print("MoviOdds unavailable")
        return None
    pending={r["match_id"] for r in state.get("alerts",{}).values() if r.get("message_id") and (r["result"] is None or not r.get("edited")) and r["match_id"].startswith("moviodds:")}
    if pending:
        data=request("results",now.strftime("%Y-%m-%d:")+str(now.hour//3),"/results?sport=volleyball")
        rows=data.get("results",[]) if isinstance(data,dict) else []
        if isinstance(rows,list):
            for m in rows:
                if not isinstance(m,dict) or "moviodds:"+str(m.get("fixture_id")) not in pending: continue
                a=adapt(m,now,True)
                if a: process(state,a[0],[],a[1],tg,persist,False)
    if 8<=local.hour<23:
        data=request("live",now.strftime("%Y-%m-%dT%H:")+str(now.minute//30),"/odds?sport=volleyball&stats=1")
        rows=data.get("matches",[]) if isinstance(data,dict) else []
        print("VOLLEY_RESPONSE", "no_payload" if data is None else "matches_list" if isinstance(data,dict) and isinstance(data.get("matches"),list) else "unexpected_schema")
        if isinstance(rows,list):
            cache=state.setdefault("odds",{})
            counts={"invalid_row":0,"prematch_accepted":0,"prematch_rejected":0,"live_seen":0,"live_rejected":0,"live_adapted":0}
            for m in rows:
                if not isinstance(m,dict) or m.get("id") is None:
                    counts["invalid_row"]+=1
                    continue
                rec=prematch_record(m,now)
                if rec:
                    cache[str(m["id"])]=rec
                    counts["prematch_accepted"]+=1
                elif m.get("in_play") is False:
                    counts["prematch_rejected"]+=1
            state["odds"]={k:v for k,v in cache.items() if stamp(v.get("start")) and (now-stamp(v["start"])).total_seconds()<259200}
            persist()
            accepted=0
            diagnostics={}
            records=[dict(v,fixture_id="moviodds:"+str(k)) for k,v in state["odds"].items()]
            for m in rows:
                is_live=isinstance(m,dict) and m.get("in_play") is True
                if is_live: counts["live_seen"]+=1
                a=adapt(m,now)
                if not a:
                    if is_live: counts["live_rejected"]+=1
                    continue
                counts["live_adapted"]+=1
                row,best=a
                _,reason=favorite_diagnostic(row,records)
                diagnostics[reason]=diagnostics.get(reason,0)+1
                volley_health.observe(state,row,records,best,now)
                volley_coverage.observe(state,row,records,best,now)
                accepted+=bool(process(state,row,records,best,tg,persist))
                volley_coverage.observe(state,row,records,best,now)
            print("VOLLEY_CYCLE_REPORT",json.dumps(counts,sort_keys=True))
            print("VOLLEY_MATCHING_REPORT",json.dumps(diagnostics,sort_keys=True))
            print("MoviOdds rows",len(rows),"decoded",accepted,"cached odds",len(state["odds"]))
    volley_health.daily(state,now,local,tg,persist)
    volley_coverage.report(state,now)
    persist()
    print("MoviOdds budget",json.dumps(budget))
    print("Statistics",json.dumps(statistics(state)))
if __name__=="__main__": main()
