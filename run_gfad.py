"""
Master CLI and Application Entry Point for GFAD (Graph Framework for Author Disambiguation).
Paper: Shin et al. (2014)

Usage Examples:
  python run_gfad.py --benchmark
  python run_gfad.py --group "A. Gupta"
  python run_gfad.py --test
"""

import argparse
import sys
import unittest

from gfad.config import CLEANED_DATASET_JSON
from gfad.data_loader import load_dataset
from gfad.pipeline import GFADPipeline


def load_dataset_or_exit(dataset_path: str) -> list:
    try:
        return load_dataset(dataset_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)


def print_metrics(heading: str, m: dict):
    print(f"=== {heading} Metrics ===")
    print(f"  K-Metric: {m['K_metric']:.4f}  (ACP: {m['ACP']:.4f}, AAP: {m['AAP']:.4f})")
    print(f"  Pairwise-F1: {m['pF1']:.4f}  (PP: {m['PP']:.4f}, PR: {m['PR']:.4f})")
    print(f"  Cluster-F1:  {m['cF1']:.4f}  (CP: {m['CP']:.4f}, CR: {m['CR']:.4f})")
    print(f"  Predicted Clusters: {m['q_predicted']} | Reference Clusters: {m['r_reference']} | Exact Matched: {m['m_matched']}\n")


def run_single_group(group_name: str, dataset_path: str):
    records = load_dataset_or_exit(dataset_path)
    print(f"\n=======================================================")
    print(f"  Running GFAD for Ambiguous Group: {group_name}")
    print(f"=======================================================\n")

    result_ad = GFADPipeline(with_outlier_removal=False).run_group(records, group_name)
    result_or = GFADPipeline(with_outlier_removal=True).run_group(records, group_name)

    if "error" in result_ad:
        print(result_ad["error"])
        return

    print_metrics("GFAD-AD (Without Outlier Removal)", result_ad["metrics"])
    print_metrics("GFAD-OR (With Outlier Removal)", result_or["metrics"])


def run_unit_tests():
    print("\nRunning GFAD Unit Test Suite...\n")
    suite = unittest.TestLoader().discover(start_dir='tests')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())


def main():
    parser = argparse.ArgumentParser(description="GFAD - Graph Framework for Author Disambiguation (Shin et al., 2014)")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark evaluation across all 14 DBLP author groups")
    parser.add_argument("--group", type=str, help="Run GFAD for a specific ambiguous author group (e.g. 'A. Gupta', 'J. Lee')")
    parser.add_argument("--test", action="store_true", help="Run unit test suite")
    parser.add_argument("--dataset", type=str, default=CLEANED_DATASET_JSON, help="Path to cleaned dataset JSON file")

    args = parser.parse_args()

    if args.test:
        run_unit_tests()
    elif args.benchmark:
        from experiments.run_benchmark import run_benchmark
        run_benchmark(args.dataset)
    elif args.group:
        run_single_group(args.group, args.dataset)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
