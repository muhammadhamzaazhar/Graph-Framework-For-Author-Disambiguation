"""
Unit tests for evaluation metrics (ACP, AAP, K-metric, pF1, cF1).
"""

import unittest
from gfad.evaluation.metrics import evaluate_clusters

class TestMetrics(unittest.TestCase):

    def test_perfect_clustering(self):
        ground_truth = [{"P1", "P2"}, {"P3", "P4"}]
        predicted = [{"P1", "P2"}, {"P3", "P4"}]

        metrics = evaluate_clusters(predicted, ground_truth)
        self.assertEqual(metrics["K_metric"], 1.0)
        self.assertEqual(metrics["pF1"], 1.0)
        self.assertEqual(metrics["cF1"], 1.0)

    def test_over_split_clustering(self):
        ground_truth = [{"P1", "P2", "P3", "P4"}]
        predicted = [{"P1", "P2"}, {"P3", "P4"}]

        metrics = evaluate_clusters(predicted, ground_truth)
        self.assertLess(metrics["K_metric"], 1.0)
        self.assertLess(metrics["cF1"], 1.0)
        print("Over-split metrics:", metrics)

    def test_over_merged_clustering(self):
        ground_truth = [{"P1", "P2"}, {"P3", "P4"}]
        predicted = [{"P1", "P2", "P3", "P4"}]

        metrics = evaluate_clusters(predicted, ground_truth)
        self.assertLess(metrics["K_metric"], 1.0)
        self.assertLess(metrics["cF1"], 1.0)
        print("Over-merged metrics:", metrics)

if __name__ == '__main__':
    unittest.main()
