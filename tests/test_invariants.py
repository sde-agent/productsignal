import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from productsignal.dataset import main as generate
from productsignal.embeddings import preprocess
from productsignal.metrics import clean_behavior_metrics


class Invariants(unittest.TestCase):
    def test_noise_and_mixed_clusters_do_not_inflate_clean_coverage(self):
        frame = pd.DataFrame({'behavior':['outage','outage','outage','relevance','howto'],
                              'cluster':[2,-1,3,3,4]})
        result = clean_behavior_metrics(frame)
        self.assertEqual(result['outage']['clean_cases'], 1)
        self.assertAlmostEqual(result['outage']['clean_case_coverage'], 1/3)
        self.assertEqual(result['outage']['cases_in_mixed_clusters'], 1)
        self.assertEqual(result['outage']['noise_cases'], 1)
        self.assertEqual(result['relevance']['clean_cases'], 0)
        self.assertEqual(result['howto']['clean_cases'], 1)

    def test_dataset_contract_seed_and_small_issue_counts(self):
        with tempfile.TemporaryDirectory() as folder:
            first, second = Path(folder)/'a', Path(folder)/'b'
            with contextlib.redirect_stdout(io.StringIO()):
                generate(first); generate(second)
            raw = (first/'raw/support_cases.jsonl').read_bytes()
            self.assertEqual(raw, (second/'raw/support_cases.jsonl').read_bytes())
            cases = [json.loads(line) for line in raw.splitlines()]
            labels = [json.loads(line) for line in (first/'golden/labels.jsonl').read_text().splitlines()]
            self.assertEqual(len(cases),1000)
            self.assertTrue(all(set(c)=={'case_id','created_at','text'} for c in cases))
            self.assertEqual({c['case_id'] for c in cases},{c['case_id'] for c in labels})
            self.assertEqual(sum(c['behavior']=='search_unavailable' for c in labels),15)
            self.assertEqual(sum(c['behavior']=='checkout_promo_freeze' for c in labels),25)
            with self.assertRaises(SystemExit):
                generate(first)

    def test_preprocessing_preserves_contrast(self):
        text = 'Cart hangs without emptying.\n Email me at test@example.com'
        cleaned = preprocess(text)
        self.assertIn('without emptying',cleaned)
        self.assertNotIn('test@example.com',cleaned)
        self.assertIn('[EMAIL]',cleaned)


if __name__ == '__main__':
    unittest.main()
