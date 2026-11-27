import unittest
from unittest.mock import patch
from datetime import datetime, timezone
from contextlib import ExitStack
import volley_main as m

class MainCycleTest(unittest.TestCase):
    def test_live_paths(self):
        now=datetime(2026,11,27,18,tzinfo=timezone.utc)
        for payload in (None, {"matches":[{"id":"x","in_play":False}]}):
            with self.subTest(payload=payload), ExitStack() as stack:
                state={}
                stack.enter_context(patch.dict("os.environ",{"TELEGRAM_BOT_TOKEN":"test","TELEGRAM_CHAT_ID":"test"}))
                clock=stack.enter_context(patch.object(m,"datetime"))
                clock.now.return_value=now
                stack.enter_context(patch.object(m,"load",return_value=state))
                stack.enter_context(patch.object(m,"save"))
                stack.enter_context(patch.object(m,"Telegram"))
                stack.enter_context(patch.object(m,"reserve",return_value=True))
                stack.enter_context(patch.object(m,"get",return_value=payload))
                stack.enter_context(patch.object(m.volley_health,"daily"))
                stack.enter_context(patch.object(m.volley_coverage,"report"))
                stack.enter_context(patch.object(m,"adapt",return_value=None))
                m.main()
                self.assertIn("odds",state)
