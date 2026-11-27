import unittest
from volley_feed import decode
class FeedTests(unittest.TestCase):
    def test_live(self):
        r={"stale":False,"awarded":False,"status":{"type":"inprogress","period":"period2"},"homeScore":{"current":0,"periods":{"period1":20,"period2":10}},"awayScore":{"current":1,"periods":{"period1":25,"period2":15}}}
        self.assertEqual(decode(r,5),([1],(10,15),None))
        self.assertIsNone(decode(r))
        r["homeScore"]["current"]=1
        self.assertIsNone(decode(r,5))
    def test_final(self):
        r={"stale":False,"awarded":False,"status":{"type":"finished"},"homeScore":{"current":2,"periods":{"period1":25,"period2":25}},"awayScore":{"current":0,"periods":{"period1":20,"period2":19}}}
        self.assertEqual(decode(r,3),([0,0],None,0))
        self.assertIsNone(decode(r,5))
