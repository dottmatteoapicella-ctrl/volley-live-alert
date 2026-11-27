import unittest
from datetime import datetime,timezone,timedelta
from volley_coverage import observe,report
class CoverageTests(unittest.TestCase):
    def test_unique(self):
        now=datetime.now(timezone.utc)
        s={}
        row={"id":1,"league":{"name":"League","country":{"name":"Italy"}}}
        observe(s,row,[],None,now)
        observe(s,row,[],None,now)
        g=report(s,now)[("League","Italy","N/D")]
        self.assertEqual(g["live"],1)
        self.assertEqual(g["decoded"],0)
        self.assertEqual(g["favorite"],0)
        self.assertEqual(report(s,now+timedelta(days=31)),{})
