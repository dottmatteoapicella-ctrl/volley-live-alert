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
