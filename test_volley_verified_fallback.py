import unittest
from volley_odds import favorite_diagnostic

class VerifiedFallbackTest(unittest.TestCase):
    def test_strict_fallback(self):
        fixture=dict(id="moviodds:live",home={"name":"Alpha"},away={"name":"Beta"},league="League A",startTime="2026-11-27T20:00:00Z")
        record=dict(fixture_id="moviodds:pre",names=["alpha","beta"],prices={"alpha":1.5,"beta":2.5},league="leaguea",start="2026-11-27T20:00:00Z",captured="2026-11-27T19:00:00Z")
        self.assertEqual(favorite_diagnostic(fixture,[record]),({"favorite":0,"odds":[1.5,2.5]},"matched_verified_fallback"))
        for bad in (dict(record,league=""),dict(record,league="leagueb"),dict(record,captured=record["start"]),dict(record,start="2026-11-27T21:00:00Z"),dict(record,prices={"alpha":1,"beta":2.5})):
            self.assertIsNone(favorite_diagnostic(fixture,[bad])[0])
        self.assertIsNone(favorite_diagnostic(fixture,[record,dict(record,fixture_id="moviodds:other")])[0])
        self.assertIsNone(favorite_diagnostic(fixture,[record,dict(record,fixture_id=fixture["id"],names=["wrong","beta"])])[0])
