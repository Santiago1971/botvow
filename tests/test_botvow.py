"""Unit tests for BotVow (run: python3 -m unittest discover -s tests -v)."""
import copy, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import botvow as bv

class BotVowTests(unittest.TestCase):
    def setUp(self):
        self.log, _ = bv.build_bot2bot()
        self.od, (self.bot, self.agent) = bv.build_open_door()

    def test_bot2bot_ok(self):
        self.assertEqual(bv.verify(self.log, self.log[-1]["entry_hash"]), [])

    def test_open_door_same_rules_ok(self):
        self.assertEqual(bv.verify(self.od), [])

    def test_tamper_detected(self):
        t = copy.deepcopy(self.log); t[3]["content"]["valid_until"] = "2099-01-01"
        self.assertTrue(bv.verify(t))

    def test_agent_own_rules_rejected_even_if_cosigned(self):
        t = copy.deepcopy(self.od)
        t[2]["content"]["own_rules"] = {"cancel": "any time"}
        bv.rehash_resign(t[2], [self.bot, self.agent])
        t[3]["prev_hash"] = t[2]["entry_hash"]; bv.rehash_resign(t[3], [self.bot, self.agent])
        errs = bv.verify(t)
        self.assertTrue(any("own rules or exceptions are not allowed" in e for e in errs), errs)

    def test_agent_custom_type_rejected(self):
        t = copy.deepcopy(self.od); t[2]["type"] = "custom"
        bv.rehash_resign(t[2], [self.bot, self.agent])
        t[3]["prev_hash"] = t[2]["entry_hash"]; bv.rehash_resign(t[3], [self.bot, self.agent])
        self.assertTrue(any("type not allowed" in e for e in bv.verify(t)))

    def test_extra_field_rejected(self):
        t = copy.deepcopy(self.od); t[1]["rules_override"] = "x"
        bv.rehash_resign(t[1], [self.agent])
        self.assertTrue(any("fields differ" in e for e in bv.verify(t)))

    def test_agreement_needs_all_signatures(self):
        t = copy.deepcopy(self.od); bv.rehash_resign(t[2], [self.bot])
        self.assertTrue(any("ALL parties" in e for e in bv.verify(t)))

if __name__ == "__main__":
    unittest.main()
