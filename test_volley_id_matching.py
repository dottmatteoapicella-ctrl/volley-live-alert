import unittest
from volley_odds import favorite_diagnostic
class MatchingTests(unittest.TestCase):
    def test_exact(self):
        row={"id":"moviodds:123","home":{"name":"A"},"away":{"name":"B"},"startTime":"2026-11-27T18:00:00Z"}
        rec={"fixture_id":"moviodds:123","names":["a","b"],"prices":{"a":1.2,"b":4},"start":row["startTime"],"captured":"2026-11-27T17:00:00Z"}
        self.assertEqual(favorite_diagnostic(row,[rec]),({"favorite":0,"odds":[1.2,4]},"matched_id"))
        for changes,reason in [({"fixture_id":"moviodds:124"},"missing_prematch_id"),({"names":["a","c"]},"team_mismatch"),({"captured":row["startTime"]},"not_prematch"),({"start":"2026-11-27T20:00:00Z"},"kickoff_mismatch")]:
            self.assertEqual(favorite_diagnostic(row,[dict(rec,**changes)]),(None,reason))
        self.assertEqual(favorite_diagnostic(row,[rec,rec]),(None,"duplicate_id"))
