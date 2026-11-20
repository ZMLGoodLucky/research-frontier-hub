import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class _Ids(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids={}
        self.pages=set()
        self.sections=set()
        self.script_srcs=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids[a['id']]=self.ids.get(a['id'],0)+1
        if 'data-page' in a:self.pages.add(a['data-page'])
        if 'data-page-section' in a:self.sections.add(a['data-page-section'])
        if tag=='script':self.script_srcs.append(a.get('src',''))

class NavigationStructureTest(unittest.TestCase):
    def test_six_separate_research_sections(self):
        doc=_Ids()
        doc.feed((ROOT/'site/index.html').read_text(encoding='utf-8'))
        self.assertEqual(doc.pages,{'home','daily','papers','ideas','insights','saved'})
        self.assertEqual(doc.sections,{'home','daily','ideas','research'})
        for id_ in ('homePage','dailyBrief','researchBody','innovationLab','homePapers',
                    'homeIdea','homeSourceSummary','pageBreadcrumb','pageHeadline'):
            self.assertEqual(doc.ids.get(id_),1,id_)
        self.assertIn('navigation.js',doc.script_srcs)
        self.assertTrue(all(n==1 for n in doc.ids.values()), 'Duplicate HTML element id')

    def test_eswa_reference_has_provenance(self):
        data=json.loads((ROOT/'data/venue_registry.json').read_text(encoding='utf-8'))
        entry=next(x for x in data['venues'] if x.get('abbr')=='ESWA')
        self.assertEqual(entry['cas_zone'],1)
        self.assertTrue(entry['cas_top'])
        self.assertEqual(entry['cas_year'],2025)
        self.assertEqual(entry['impact_factor'],9.4)
        self.assertEqual(entry['impact_factor_year'],2025)
        self.assertIn('letpub.com.cn',entry['cas_source'])
        self.assertTrue(entry['impact_factor_source'].startswith('https://shop.elsevier.com'))
        self.assertEqual(entry['ccf'],'C')

    def test_home_not_full_feed(self):
        html=(ROOT/'site/index.html').read_text(encoding='utf-8')
        self.assertLess(html.index('id="homePage"'),html.index('id="innovationLab"'))
        self.assertNotIn('class="hero"',html)
        self.assertIn('data-go-page="papers"',html)

if __name__=='__main__':
    unittest.main()
