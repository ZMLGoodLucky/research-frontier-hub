import json
import sys
import unittest
import datetime as dt
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import collect
from venue_metadata import annotate, load_registry
from extra_sources import crossref, semantic_scholar, official_feed, choose_daily

class VenueMetadataTest(unittest.TestCase):
    def test_ccf_2026_journals(self):
        for name, abbr in [
            ("Expert Systems with Applications","ESWA"),
            ("Engineering Applications of Artificial Intelligence","EAAI"),
        ]:
            a=annotate({"type":"paper","venue":name,"source":"Elsevier","publication_type":"journal"})
            self.assertEqual(a["publication_type"],"journal")
            self.assertEqual(a["venue_abbr"],abbr)
            self.assertTrue(a["ccf_listed"])
            self.assertEqual(a["ccf_grade"],"C")
            self.assertEqual(a["cas_zone"],"1区" if abbr=="ESWA" else "2025版待核验")
            if abbr=="ESWA":
                self.assertTrue(a["cas_top"])
                self.assertEqual(a["impact_factor"],9.4)
                self.assertEqual(a["impact_factor_year"],2025)
    def test_arxiv_not_assigned_conference_grade(self):
        a=annotate({"type":"paper","venue":"arXiv","source":"arXiv","publication_type":"preprint","status":"作者声称NeurIPS接收"})
        self.assertEqual(a["ccf_grade"],"不适用")
        self.assertEqual(a["publication_type"],"preprint")
        self.assertEqual(a["cas_zone"],"不适用")
    def test_neurips_if_actual_venue(self):
        a=annotate({"type":"paper","venue":"NeurIPS","source":"Crossref","publication_type":"conference"})
        self.assertEqual(a["ccf_grade"],"A")
        self.assertEqual(a["publication_type"],"conference")
    def test_unknown_cannot_infer_cas(self):
        a=annotate({"type":"paper","venue":"A Fictional New Traffic Journal","source":"Crossref","publication_type":"journal"})
        self.assertEqual(a["ccf_grade"],"待核验")
        self.assertIsNone(a["ccf_listed"])
        self.assertEqual(a["cas_zone"],"2025版待核验")
    def test_news_is_not_journal(self):
        a=annotate({"type":"insight","venue":"IEEE Spectrum","source":"IEEE","publication_type":"news"})
        self.assertEqual(a["publication_type"],"news")
        self.assertEqual(a["ccf_grade"],"不适用")
    def test_daily_max_5_and_no_repeat(self):
        today=dt.date(2026,11,20)
        examples=[{"id":str(i),"title":"Traffic flow forecast","date":"2026-11-19","type":"paper","topics":["交通预测"]} for i in range(9)]
        ids=choose_daily(examples,today,{},limit=5)
        self.assertEqual(len(ids),5)
        later=choose_daily(examples,today+dt.timedelta(days=1),{"2026-11-20":ids},limit=5)
        self.assertEqual(len(later),4)
        self.assertTrue(set(ids).isdisjoint(later))
    def test_crossref_extracts_type_date(self):
        response={"message":{"items":[{"DOI":"10.1234/traffic",
            "type":"journal-article",
            "title":["Dynamic Graph Traffic Flow Forecasting"],
            "published":{"date-parts":[[2026,11,19]]},
            "container-title":["Expert Systems with Applications"],
            "URL":"https://doi.org/10.1234/traffic"}]}}
        def request(*a,**k):return json.dumps(response).encode()
        found=crossref({"crossref_queries":["traffic forecasting"]},dt.date(2026,11,13),request,collect.relevant,collect.valid_date,collect.candidate,dt.date(2026,11,20))
        self.assertEqual(len(found),1)
        self.assertEqual(found[0]["publication_type"],"journal")
        self.assertEqual(found[0]["doi"],"10.1234/traffic")
    def test_s2_retrieves_journal_venue(self):
        response={"data":[{"title":"Dynamic Graph Traffic Flow Forecasting","publicationDate":"2026-11-19","externalIds":{"DOI":"10.5555/s2"},"venue":"Expert Systems with Applications","publicationTypes":["JournalArticle"]}]}
        def request(*a,**k):return json.dumps(response).encode()
        found=semantic_scholar({"semantic_scholar_queries":["traffic forecasting"]},dt.date(2026,11,13),request,collect.relevant,collect.valid_date,collect.candidate,dt.date(2026,11,20))
        self.assertEqual(len(found),1)
        self.assertEqual(found[0]["publication_type"],"journal")
    def test_rss_parsing(self):
        data=b'<rss><channel><item><title>Traffic congestion propagation prediction study</title><link>https://example.com/a</link><pubDate>Thu, 19 Nov 2026 09:00:00 GMT</pubDate></item></channel></rss>'
        found=official_feed({"name":"IEEE Spectrum","venue":"IEEE Spectrum","kind":"insight","url":"https://example.com/rss"},dt.date(2026,11,13),lambda *a,**k:data,collect.relevant,collect.valid_date,collect.candidate)
        self.assertEqual(len(found),1)
        self.assertEqual(found[0]["type"],"insight")

if __name__=='__main__':
    unittest.main()
