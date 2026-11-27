import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from volley_state import load,save
from cryptography.fernet import InvalidToken
class StateTests(unittest.TestCase):
    def test_roundtrip(self):
        with TemporaryDirectory() as d:
            p=Path(d)/"state.enc"
            with self.assertRaises(RuntimeError): load(p,"secret")
            self.assertEqual(load(p,"secret",initialize=True),{})
            save(p,"secret",{"private":"example","budget":12})
            self.assertNotIn(b"example",p.read_bytes())
            self.assertEqual(load(p,"secret")["budget"],12)
            with self.assertRaises(InvalidToken): load(p,"wrong")
