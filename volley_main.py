import os,json,urllib.request,urllib.error
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from volley_state import load,save
from volley_odds import prematch_record,stamp
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
        if state.get(key)==slot or not reserve(budget,now,kind): return None
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
        if isinstance(rows,list):
            cache=state.setdefault("odds",{})
            for m in rows:
                if not isinstance(m,dict) or m.get("id") is None: continue
                rec=prematch_record(m,now)
                if rec: cache[str(m["id"])]=rec
            state["odds"]={k:v for k,v in cache.items() if stamp(v.get("start")) and (now-stamp(v["start"])).total_seconds()<259200}
            persist()
            accepted=0
            for m in rows:
                a=adapt(m,now)
                if not a: continue
                row,best=a
                records=list(state["odds"].values())
                volley_health.observe(state,row,records,best,now)
                volley_coverage.observe(state,row,records,best,now)
                accepted+=bool(process(state,row,records,best,tg,persist))
                volley_coverage.observe(state,row,records,best,now)
            print("MoviOdds rows",len(rows),"decoded",accepted,"cached odds",len(state["odds"]))
    volley_health.daily(state,now,local,tg,persist)
    volley_coverage.report(state,now)
    persist()
    print("MoviOdds budget",json.dumps(budget))
    print("Statistics",json.dumps(statistics(state)))
if __name__=="__main__": main()
