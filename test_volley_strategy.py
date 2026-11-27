import unittest
from volley_strategy import signals,outcome,reserve,set_winner

class VolleyTests(unittest.TestCase):
    def test_strategies(self):
        self.assertIn(("volley1",0),signals(0,[1]))
        self.assertIn(("volley2",0),signals(0,[1,1]))
        self.assertIn(("volley4",0),signals(0,[1,0]))
        self.assertIn(("volley3",2),signals(0,[1],(10,15)))
        self.assertNotIn(("volley3",2),signals(0,[1],(10,25)))
        self.assertEqual(signals(0,[1,1],best_of=3),[])
    def test_outcomes(self):
        self.assertTrue(outcome("volley3",0,2,[1,0]))
        self.assertFalse(outcome("volley1",0,0,[1,1,1],1))
        self.assertIsNone(outcome("volley1",0,0,[1]))
        self.assertIsNone(set_winner(25,24))
        self.assertEqual(set_winner(28,26),0)
    def test_budget(self):
        s={}
        for _ in range(60): self.assertTrue(reserve(s,"day","live"))
        self.assertFalse(reserve(s,"day","live"))
        for _ in range(30): self.assertTrue(reserve(s,"day","results"))
        self.assertFalse(reserve(s,"day","results"))
        self.assertTrue(reserve(s,"next","live"))
        s["blocked"]=True
        self.assertFalse(reserve(s,"next","results"))

if __name__=="__main__": unittest.main()
