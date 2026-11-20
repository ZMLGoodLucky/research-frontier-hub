import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class ResearchSourceAccessTest(unittest.TestCase):
    def setUp(self):
        self.sources=json.loads((ROOT/'data/source_directory.json').read_text(encoding='utf-8'))
        self.feeds=json.loads((ROOT/'data/feeds.json').read_text(encoding='utf-8'))
        self.html=(ROOT/'site/index.html').read_text(encoding='utf-8')

    def test_carsi_requires_explicit_school_login(self):
        carsi=next(x for x in self.sources if 'CARSI' in x['name'])
        self.assertEqual(carsi['url'],'https://ds.carsi.edu.cn/resource/resource.php')
        self.assertFalse(carsi['automatic'])
        self.assertIn('学校统一身份认证',carsi['auth'])
        self.assertIn('researchSourceHub',self.html)

    def test_wechat_personal_follows_not_claimed(self):
        accounts=[x for x in self.sources if x.get('category')=='wechat_public']
        self.assertGreaterEqual(len(accounts),1)
        self.assertTrue(all(not a['automatic'] for a in accounts))
        self.assertIn('个人微信关注列表目前无法通过此网站读取',self.html)

    def test_verified_mit_research_feed_is_separate_from_papers(self):
        feed=next(x for x in self.feeds if x['url']=='https://news.mit.edu/rss/research')
        self.assertTrue(feed['enabled'])
        self.assertEqual(feed['kind'],'insight')
        self.assertEqual(feed['format'],'rss')
        self.assertTrue(all(x.get('url','').startswith('https://') for x in self.sources))

if __name__=='__main__':unittest.main()
