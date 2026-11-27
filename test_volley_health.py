import unittest
from datetime import datetime,timezone
from volley_health import observe,summary
from volley_odds import name_key
class HealthTests(unittest.TestCase):
    def test_observe_unique(self):
        now=datetime.now(timezone.utc)
        s={}
        for _ in range(2): observe(s,{"id":1},[],None,now)
        self.assertIn("Partite uniche: 1",summary(s,now))
    def test_names(self):
        self.assertEqual(name_key("São Paulo"),name_key("Sao Paulo"))
        self.assertNotEqual(name_key("Team W"),name_key("Team"))
