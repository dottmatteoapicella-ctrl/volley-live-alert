import json
import urllib.request
import urllib.error

class Telegram:
    def __init__(self,token,chat):
        self.token=token
        self.chat=chat
    def call(self,method,fields):
        data=json.dumps({"chat_id":self.chat,**fields}).encode()
        req=urllib.request.Request("https://api.telegram.org/bot"+self.token+"/"+method,data=data,headers={"Content-Type":"application/json"})
        try:
            with urllib.request.urlopen(req,timeout=20) as res:
                result=json.load(res)
        except (OSError,ValueError):
            return None
        return result.get("result") if isinstance(result,dict) and result.get("ok") is True else None
    def send(self,text):
        result=self.call("sendMessage",{"text":text})
        return result.get("message_id") if isinstance(result,dict) else None
    def edit(self,message_id,text):
        return self.call("editMessageText",{"message_id":message_id,"text":text}) is not None

def alert_text(record):
    strategy=record["strategy"]
    teams=record["teams"]
    favorite=teams[record["favorite"]]
    labels={"volley1":"Favorita sotto 0-1: vincente partita",
            "volley2":"Favorita sotto 0-2: vincente partita",
            "volley3":"Favorita sotto di almeno 5 punti: vincente set",
            "volley4":"Favorita recupera 1-1: vincente partita"}
    lines=["🏐 "+strategy.upper()+" | SPERIMENTALE",teams[0]+" - "+teams[1],
           "Favorita: "+favorite,labels[strategy]]
    if strategy=="volley3":
        lines.append("Set: "+str(record["set_number"]))
    lines.append("Quota pre-match: "+str(record["prematch"]))
    lines.append("Quota live: "+str(record["live_odds"]) if record.get("live_odds") is not None else "Quota live: non disponibile")
    if record.get("result") is not None:
        lines.append("✅ Esito positivo" if record["result"] else "❌ Esito negativo")
    return "\n".join(lines)
