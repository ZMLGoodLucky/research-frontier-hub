import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
IDEAS=ROOT / "site" / "research-ideas.json"

class SinglePaperProposalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(IDEAS.read_text(encoding="utf-8"))
        cls.ideas=cls.data["ideas"]

    def test_three_independent_papers(self):
        self.assertEqual(len(self.ideas),3)
        self.assertEqual({x["id"] for x in self.ideas},{
            "event-evidence","incident-arrival-boundary","graph-credibility"
        })
        self.assertEqual(self.data["intent"],"single_top_journal_paper_candidates")

    def test_every_paper_has_narrow_scope_and_falsifiable_check(self):
        for x in self.ideas:
            for field in ("paper_title_en","paper_scope","question","hypothesis",
                          "key_experiment","stop_condition","core_claim","venue_fit",
                          "validation","overlap","scope_size"):
                self.assertGreater(len(x[field].strip()),20, (x["id"],field))
            self.assertEqual(len(x["novelties"]),3)
            self.assertGreaterEqual(len(x["prior"]),3)
            self.assertTrue(all(p.get("url","").startswith("https://") for p in x["prior"]))

    def test_does_not_claim_guaranteed_acceptance(self):
        self.assertIn("不等于已达到录用标准",self.data["policy"])

    def test_prioritized_feasible_paper(self):
        self.assertEqual(self.ideas[0]["id"],"event-evidence")

    def test_weekly_evidence_remains_weekly(self):
        self.assertEqual(self.data["update_policy"]["cadence"],"weekly")
        self.assertEqual(self.data["update_policy"]["weekday"],"Saturday")

if __name__=="__main__":
    unittest.main()
