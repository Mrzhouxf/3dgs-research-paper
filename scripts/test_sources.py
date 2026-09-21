import json
import unittest
from extended_sources import crossref, iclr, icml
from tracker import gaussian

class FakeClient:
    def __init__(self, responses): self.responses=iter(responses)
    def get(self, url): return next(self.responses)

class SourcesTests(unittest.TestCase):
    def test_topic_rejects_generic_gaussian(self):
        self.assertFalse(gaussian('Efficient Gaussian Processes for Classification'))
        self.assertTrue(gaussian('Efficient 3D Gaussian Splatting'))
    def test_journal_exact_identity(self):
        item={'title':['Fast Gaussian Splatting'],'container-title':['ACM Transactions on Graphics'],'ISSN':['0730-0301'],'DOI':'10.1145/test','issued':{'date-parts':[[2025]]}}
        fake=FakeClient([json.dumps({'message':{'items':[item]}})])
        papers=list(crossref(fake,2023,'TOG','0730-0301','ACM Transactions on Graphics'))
        self.assertEqual(papers[0]['publication_type'],'journal')
        item['container-title']=['Fake Transactions on Graphics']
        self.assertEqual(list(crossref(FakeClient([json.dumps({'message':{'items':[item]}})]),2023,'TOG','0730-0301','ACM Transactions on Graphics')),[])
    def test_icml_volume_only(self):
        index='<li><a href="/v267/">Volume 267</a> Proceedings of ICML 2025</li><li><a href="/v999/">Volume 999</a> ICML Workshop 2025</li>'
        body='<div class="paper"><p class="title">Fast Gaussian Splatting</p><a href="foo.html">Abstract</a></div>'
        papers=list(icml(FakeClient([index,body]),2023))
        self.assertEqual(len(papers),1)
        self.assertEqual(papers[0]['url'],'https://proceedings.mlr.press/v267/foo.html')

if __name__=='__main__': unittest.main()
