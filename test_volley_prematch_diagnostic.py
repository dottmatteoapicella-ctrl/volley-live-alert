import unittest
from datetime import datetime, timezone
from volley_odds import prematch_diagnostic, prematch_record

class PrematchDiagnosticTest(unittest.TestCase):
    def test_rejections(self):
        now=datetime(2026,11,27,18,tzinfo=timezone.utc)
        base=dict(in_play=False,stale=False,home="A",away="B",kickoff_utc="2026-11-27T20:00:00Z")
        for row,reason in [({}, "not_prematch_or_stale"),(dict(base,stale=None),"missing_or_stale_poll"),(dict(base,home=""),"invalid_identity_or_kickoff"),(base,"missing_or_equal_prices")]:
            self.assertEqual(prematch_diagnostic(row,now),(None,reason))
            self.assertIsNone(prematch_record(row,now))
