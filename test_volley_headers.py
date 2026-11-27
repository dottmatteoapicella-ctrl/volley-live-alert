import unittest
from unittest.mock import patch
from volley_main import moviodds_headers
class HeaderTests(unittest.TestCase):
    def test_headers(self):
        with patch.dict("os.environ",{"MOVIODDS_API_KEY":" example "}):
            self.assertEqual(moviodds_headers(),{"X-API-Key":"example","Accept":"application/json"})
