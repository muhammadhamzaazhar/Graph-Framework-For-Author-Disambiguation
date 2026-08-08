"""
Benchmark Runner for GFAD Paper Implementation (Shin et al., 2014).
Runs GFAD-AD and GFAD-OR across the 14 core DBLP benchmark author groups.
"""

import json
import os
import sys
from typing import Dict

# Ensure project root is on sys.path when run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gfad.config import BENCHMARK_GROUPS, BENCHMARK_RESULTS_FILE, CLEANED_DATASET_JSON
from gfad.data_loader import load_dataset
from gfad.pipeline import GFADPipeline


def _format_metrics(m: dict) -> str:
    return f"K:{m['K_metric']:.2f}  pF1:{m['pF1']:.2f}  cF1:{m['cF1']:.2f}"


def run_benchmark(dataset_path: str = CLEANED_DATASET_JSON):
    records = load_dataset(dataset_path)
    print(f"Loaded {len(records)} cleaned records from {dataset_path}\n")

    pipeline_ad = GFADPipeline(with_outlier_removal=False)
    pipeline_or = GFADPipeline(with_outlier_removal=True)

    results_ad: Dict[str, dict] = {}
    results_or: Dict[str, dict] = {}

    print("=" * 95)
    print(f"{'Ambiguous Group':<18} | {'GFAD-AD (K, pF1, cF1)':<32} | {'GFAD-OR (K, pF1, cF1)':<32}")
    print("=" * 95)

    sum_ad = {"K": 0.0, "pF1": 0.0, "cF1": 0.0}
    sum_or = {"K": 0.0, "pF1": 0.0, "cF1": 0.0}

    for grp in BENCHMARK_GROUPS:
        m_ad = pipeline_ad.run_group(records, grp)["metrics"]
        m_or = pipeline_or.run_group(records, grp)["metrics"]

        results_ad[grp] = m_ad
        results_or[grp] = m_or

        sum_ad["K"] += m_ad["K_metric"]
        sum_ad["pF1"] += m_ad["pF1"]
        sum_ad["cF1"] += m_ad["cF1"]

        sum_or["K"] += m_or["K_metric"]
        sum_or["pF1"] += m_or["pF1"]
        sum_or["cF1"] += m_or["cF1"]

        print(f"{grp:<18} | {_format_metrics(m_ad):<32} | {_format_metrics(m_or):<32}")

    n_groups = len(BENCHMARK_GROUPS)
    avg_ad = {k: round(v / n_groups, 4) for k, v in sum_ad.items()}
    avg_or = {k: round(v / n_groups, 4) for k, v in sum_or.items()}

    print("-" * 95)
    str_avg_ad = f"K:{avg_ad['K']:.2f}  pF1:{avg_ad['pF1']:.2f}  cF1:{avg_ad['cF1']:.2f}"
    str_avg_or = f"K:{avg_or['K']:.2f}  pF1:{avg_or['pF1']:.2f}  cF1:{avg_or['cF1']:.2f}"
    print(f"{'AVERAGE':<18} | {str_avg_ad:<32} | {str_avg_or:<32}")
    print("=" * 95)

    output_data = {
        "benchmark_14_groups": BENCHMARK_GROUPS,
        "GFAD_AD_results": results_ad,
        "GFAD_OR_results": results_or,
        "GFAD_AD_average": avg_ad,
        "GFAD_OR_average": avg_or
    }

    os.makedirs(os.path.dirname(BENCHMARK_RESULTS_FILE), exist_ok=True)
    with open(BENCHMARK_RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    print(f"\nSaved benchmark evaluation results to {BENCHMARK_RESULTS_FILE}")


if __name__ == '__main__':
    run_benchmark()
