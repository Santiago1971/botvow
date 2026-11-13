import copy, datetime as dt, json, os, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from card_tool import validate, answer, export
L = lambda n: json.load(open(os.path.join(ROOT, "cards", n)))
CAFE, CASA = L("cafe-exemplo-do-cais.json"), L("casa-exemplo-da-serra.json")
TODAY = dt.date(2026, 11, 13)

class T(unittest.TestCase):
    def test_examples_valid(self):
        self.assertEqual(validate(CAFE, TODAY), []); self.assertEqual(validate(CASA, TODAY), [])
    def test_lodging_needs_rnal(self):
        c = copy.deepcopy(CASA); del c["lodging"]; self.assertTrue(validate(c, TODAY))
    def test_demo_must_be_labelled(self):
        c = copy.deepcopy(CAFE); c["name"] = "Café do Cais"; self.assertTrue(validate(c, TODAY))
    def test_booking_requires_human(self):
        c = copy.deepcopy(CAFE); c["booking"]["human_confirmation_required"] = False; self.assertTrue(validate(c, TODAY))
    def test_unknown_zone(self):
        c = copy.deepcopy(CAFE); c["zones"][0]["id"] = "atlantis"; self.assertTrue(validate(c, TODAY))
    def test_expired(self):
        self.assertTrue(validate(CAFE, dt.date(2027, 6, 1)))
    def test_extra_field_rejected(self):
        c = copy.deepcopy(CAFE); c["owner_mobile"] = "+351..."; self.assertTrue(validate(c, TODAY))
    def test_open_weekday(self):
        self.assertEqual(answer(CAFE, "open", "2026-11-17T10:00")["answer"], "open")    # Tuesday
        self.assertEqual(answer(CAFE, "open", "2026-11-16T10:00")["answer"], "closed")  # Monday
    def test_holiday_uses_official_calendar(self):
        r = answer(CAFE, "open", "2026-12-08T19:30")                                   # Tue, Imaculada Conceição -> Sunday hours
        self.assertEqual(r["answer"], "open"); self.assertIn("Imaculada", r["why"])
        self.assertEqual(answer(CAFE, "open", "2026-12-25T10:00")["answer"], "closed")  # exception
    def test_export(self):
        import tempfile
        d = tempfile.mkdtemp(); files = export(CASA, d)
        self.assertIn("agent-card.draft.json", files)
        ld = json.load(open(os.path.join(d, "localbusiness.jsonld")))
        self.assertEqual(ld["@type"], "LodgingBusiness")

if __name__ == "__main__": unittest.main(verbosity=2)
