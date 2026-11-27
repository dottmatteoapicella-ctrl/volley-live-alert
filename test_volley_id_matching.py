import unittest
from volley_odds import favorite_diagnostic, shadow_matching_reason
class MatchingTests(unittest.TestCase):
    def test_exact(self):
        row={"id":"moviodds:123","home":{"name":"A"},"away":{"name":"B"},"startTime":"2026-11-27T18:00:00Z"}
        rec={"fixture_id":"moviodds:123","names":["a","b"],"prices":{"a":1.2,"b":4},"start":row["startTime"],"captured":"2026-11-27T17:00:00Z"}
        self.assertEqual(favorite_diagnostic(row,[rec]),({"favorite":0,"odds":[1.2,4]},"matched_id"))
        for changes,reason in [({"fixture_id":"moviodds:124"},"missing_prematch_id"),({"names":["a","c"]},"team_mismatch"),({"captured":row["startTime"]},"not_prematch"),({"start":"2026-11-27T20:00:00Z"},"kickoff_mismatch")]:
            self.assertEqual(favorite_diagnostic(row,[dict(rec,**changes)]),(None,reason))
        self.assertEqual(favorite_diagnostic(row,[rec,rec]),(None,"duplicate_id"))

    def test_shadow(self):
        row={"id":"moviodds:1","home":{"name":"A"},"away":{"name":"B"},"league":"League","startTime":"2026-11-27T18:00:00Z"}
        rec={"fixture_id":"moviodds:2","names":["a","b"],"league":"league","prices":{"a":1.2,"b":4},"start":row["startTime"],"captured":"2026-11-27T17:00:00Z"}
        self.assertEqual(shadow_matching_reason(row,[rec]),"unique_verified_candidate")
        self.assertEqual(favorite_diagnostic(row,[rec]),(None,"missing_prematch_id"))
        self.assertEqual(shadow_matching_reason(row,[rec,rec]),"ambiguous_team_time")
        self.assertEqual(shadow_matching_reason(row,[dict(rec,league="")]),"candidate_league_unknown")
        self.assertEqual(shadow_matching_reason(row,[dict(rec,league="other")]),"candidate_league_mismatch")
        self.assertEqual(shadow_matching_reason(row,[dict(rec,captured=row["startTime"])]),"no_valid_prematch_time")
        self.assertEqual(shadow_matching_reason(row,[]),"no_cached_team_pair")
