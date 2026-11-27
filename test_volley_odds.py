import unittest
from datetime import datetime,timezone
from volley_odds import prematch_record,favorite_for

class OddsTests(unittest.TestCase):
    def test_matching(self):
        now=datetime(2026,11,27,10,tzinfo=timezone.utc)
        m={"home":"Alpha W","away":"Beta W","in_play":False,"stale":False,"kickoff_utc":"2026-11-27T12:00:00Z","quotes":[{"group_name":"Winner","side":n,"odds_dec":p,"suspended":False} for n,p in [("Alpha W",1.4),("Beta W",2.8)]]}
        r=prematch_record(m,now)
        self.assertIsNotNone(r)
        f={"home":{"name":"Beta W"},"away":{"name":"Alpha W"},"startTime":m["kickoff_utc"]}
        self.assertEqual(favorite_for(f,[r])["favorite"],1)
        self.assertIsNone(favorite_for(f,[r,r]))
        f["home"]["name"]="Beta"
        self.assertIsNone(favorite_for(f,[r]))
        m["in_play"]=True
        self.assertIsNone(prematch_record(m,now))

    def test_provider_null_flags(self):
        now=datetime(2026,11,27,9,48,41,tzinfo=timezone.utc)
        m={"home":"Alpha","away":"Beta","in_play":False,"kickoff_utc":"2026-11-27T10:00:00Z","polled_at":"2026-11-27T09:48:36.252645815Z","quotes":[{"group_name":"Winner","side":n,"odds_dec":p,"ts":"2026-11-27T09:15:06.339326548Z"} for n,p in [("Alpha",1.2),("Beta",4.33)]]}
        self.assertIsNotNone(prematch_record(m,now))
        m["quotes"][0]["suspended"]=True
        self.assertIsNone(prematch_record(m,now))
        m["quotes"][0]["suspended"]=None
        m["polled_at"]="2026-11-27T08:00:00Z"
        self.assertIsNone(prematch_record(m,now))
