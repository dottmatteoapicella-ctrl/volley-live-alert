import unittest
from unittest.mock import patch
from volley_main import sports_headers
class HeaderTests(unittest.TestCase):
    def test_headers(self):
        with patch.dict("os.environ",{"SPORTSAPI_KEY":" example "}):
            self.assertEqual(sports_headers(),{"Authorization":"Bearer example","Accept":"application/json"})
