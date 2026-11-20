import datetime as dt
import unittest
from zoneinfo import ZoneInfo
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from refresh_research_ideas import scan, topic_score

class ResearchIdeasTests(unittest.TestCase):
    def setUp(self):
        self.idea = {
            "id": "incident-arrival-boundary",
            "match_terms": ["traffic incident", "incident", "arrival", "boundary", "propagation"],
            "prior": [{"url": "https://example.org/old"}],
        }
        self.now = dt.datetime(2026, 11, 20, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
        self.items = [
            {"id": "first", "type": "paper", "title": "Traffic Incident Propagation and Arrival Time Prediction",
             "date": "2026-11-19", "url": "https://example.org/new",
             "venue": "Journal of Testing", "topics": ["事件", "交通预测"]},
            {"id": "prior", "type": "paper", "title": "Traffic Incident Propagation and Arrival Time Prediction",
             "date": "2026-11-19", "url": "https://example.org/old",
             "topics": ["事件"]},
            {"id": "old", "type": "paper", "title": "Traffic Incident Propagation and Arrival Time Prediction",
             "date": "2026-10-01", "url": "https://example.org/ancient",
             "topics": ["事件"]},
            {"id": "unrelated", "type": "paper", "title": "Generic language models for chemistry",
             "date": "2026-11-19", "url": "https://example.org/unrelated", "topics": ["语言模型"]},
        ]

    def test_relevance_requires_title_hit_and_at_least_two_signals(self):
        self.assertGreater(topic_score(self.items[0], self.idea), 0)
        self.assertEqual(topic_score(self.items[3], self.idea), 0)

    def test_only_recent_and_not_known_prior(self):
        x = scan({"ideas": [self.idea]}, {"items": self.items}, {}, self.now)
        papers = x["topics"][self.idea["id"]]["papers"]
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]["url"], "https://example.org/new")
        self.assertTrue(papers[0]["candidate_only"])

    def test_next_week_does_not_repeat_same_candidate(self):
        first = scan({"ideas": [self.idea]}, {"items": self.items}, {}, self.now)
        second = scan({"ideas": [self.idea]}, {"items": self.items}, first,
                      self.now + dt.timedelta(days=7))
        self.assertEqual(second["topics"][self.idea["id"]]["new_count"], 0)
        self.assertIn("https://example.org/new", second["seen"][self.idea["id"]])

    def test_data_published_in_future_is_excluded(self):
        future = dict(self.items[0], date="2026-12-01")
        x = scan({"ideas": [self.idea]}, {"items": [future]}, {}, self.now)
        self.assertEqual(x["topics"][self.idea["id"]]["new_count"], 0)

    def test_preserves_curated_research_problem_content(self):
        idea_data = {"ideas": [dict(self.idea, title="Human-reviewed research question")]}
        original = idea_data["ideas"][0]["title"]
        scan(idea_data, {"items": self.items}, {}, self.now)
        self.assertEqual(idea_data["ideas"][0]["title"], original)

if __name__ == "__main__":
    unittest.main()
