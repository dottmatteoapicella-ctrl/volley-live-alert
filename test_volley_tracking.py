import unittest
from volley_tracking import register,settle,statistics
class TrackingTests(unittest.TestCase):
    def test_tracking(self):
        s={}
        k=register(s,1,"volley3",2,0,["A","B"],1.5,2.0)
        self.assertIsNone(register(s,1,"volley3",2,0,["A","B"],1.5))
        s["alerts"][k]["message_id"]=1
        self.assertEqual(settle(s,1,["B","A"],[1,0]),[])
        self.assertEqual(settle(s,1,["A","B"],[1,0]),[k])
        self.assertEqual(statistics(s)["volley3"]["roi_pct"],100)
        self.assertEqual(statistics(s)["volley1"]["roi_pct"],None)
