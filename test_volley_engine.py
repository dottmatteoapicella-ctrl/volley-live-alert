import unittest
from volley_engine import process
class FakeTelegram:
    def __init__(self): self.sent=[]; self.edits=[]
    def send(self,t): self.sent.append(t); return len(self.sent)
    def edit(self,i,t): self.edits.append((i,t)); return True
class EngineTests(unittest.TestCase):
    def test_flow(self):
        s={}; tg=FakeTelegram()
        row={"id":1,"home":{"name":"A"},"away":{"name":"B"},"startTime":"2026-11-27T12:00:00Z","stale":False,"awarded":False,"status":{"type":"inprogress","period":"period2"},"homeScore":{"current":0,"periods":{"period1":20,"period2":10}},"awayScore":{"current":1,"periods":{"period1":25,"period2":15}}}
        records=[{"names":["a","b"],"prices":{"a":1.5,"b":2.5},"start":row["startTime"],"captured":"2026-11-27T11:00:00Z"}]
        for _ in range(2): process(s,row,records,5,tg,lambda:None)
        self.assertEqual(len(tg.sent),2)
        row["homeScore"]={"current":3,"periods":{"period1":20,"period2":25,"period3":25,"period4":25}}
        row["awayScore"]={"current":1,"periods":{"period1":25,"period2":20,"period3":20,"period4":20}}
        row["status"]={"type":"finished"}
        process(s,row,records,5,tg,lambda:None)
        self.assertEqual(len(tg.edits),2)
        self.assertTrue(all(r["result"] for r in s["alerts"].values()))
