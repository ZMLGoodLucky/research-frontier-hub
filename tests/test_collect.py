import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import collect

class TestResearchCollector(unittest.TestCase):
    def test_relevant_road_traffic(self):
        self.assertTrue(collect.relevant('Dynamic Graph Traffic Flow Forecasting'))
        self.assertTrue(collect.relevant('Accident-aware road traffic speed prediction'))
    def test_exclude_unrelated_traffic(self):
        self.assertFalse(collect.relevant('Network traffic forecasting for TCP packets'))
        self.assertFalse(collect.relevant('Aircraft air traffic prediction'))
    def test_deduplication(self):
        example={"id":"one","title":"Graph Traffic Flow Forecasting","url":"https://arxiv.org/abs/1234.56789","date":"2026-11-13","editorial":False}
        second={**example,"id":"two","url":"https://doi.org/10.123/x","editorial":True}
        result=collect.deduplicate([example,second],limit=10)
        self.assertEqual(len(result),1)
        self.assertTrue(result[0]['editorial'])
    def test_curated_source_links(self):
        curated=json.loads((Path(__file__).resolve().parents[1]/'data/curated.json').read_text(encoding='utf8'))
        for a in curated:
            self.assertIn('https://',a['url'])
            self.assertTrue(a['problem'])
            self.assertTrue(a['relevance'])
    def test_no_fake_grade_on_candidate(self):
        item=collect.candidate('arXiv','Traffic flow prediction','2026-11-19','https://arxiv.org/abs/2611.12345','Abstract','arXiv','预印本')
        self.assertFalse(item['verified'])
        self.assertIn('未核验',item['level'])

if __name__=='__main__':unittest.main()
