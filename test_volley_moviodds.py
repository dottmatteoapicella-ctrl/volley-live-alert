import unittest
from datetime import datetime,timezone
from volley_moviodds import adapt,reserve
from volley_feed import decode
class TestMoviOdds(unittest.TestCase):
    def test_live_final(self):
        now=datetime(2026,11,27,17,tzinfo=timezone.utc)
        m=dict(id="205277480",home="A",away="B",in_play=True,polled_at=now.isoformat(),score="25-18,25-9,24-26,20-12")
        row,b=adapt(m,now)
        self.assertEqual(decode(row,b),([0,0,1],(20,12),None))
        m.update(fixture_id=m["id"],status="finished",finished_at=now.isoformat(),final_score="25-18,25-9,24-26,25-15")
        m["periods"]=[dict(name=f"Set {i+1}",score=p) for i,p in enumerate(m["final_score"].split(","))]
        final,b=adapt(m,now,True)
        self.assertEqual(final["id"],row["id"])
        self.assertEqual(decode(final,b),([0,0,1,0],None,0))
    def test_budget(self):
        b={}
        now=datetime(2026,11,27,17,tzinfo=timezone.utc)
        for _ in range(30): self.assertTrue(reserve(b,now,"live"))
        self.assertFalse(reserve(b,now,"live"))
        for _ in range(8): self.assertTrue(reserve(b,now,"results"))
        self.assertFalse(reserve(b,now,"results"))
