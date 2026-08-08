"""
Evaluation Metrics for Author Name Disambiguation (Shin et al., 2014, Section Evaluation Metrics).
Computes:
  - K-metric (Geometric mean of ACP - Average Cluster Purity and AAP - Average Author Purity)
  - Pairwise-F1 (Harmonic mean of PP - Pairwise Precision and PR - Pairwise Recall)
  - Cluster-F1 (Harmonic mean of CP - Cluster Precision and CR - Cluster Recall)
"""

import math
from typing import Dict, List, Set, Tuple


def comb2(n: int) -> int:
    """Combination C(n, 2) = n*(n-1)/2."""
    if n < 2:
        return 0
    return (n * (n - 1)) // 2


def _empty_metrics(q: int, r: int) -> Dict[str, float]:
    return {
        "ACP": 0.0, "AAP": 0.0, "K_metric": 0.0,
        "PP": 0.0, "PR": 0.0, "pF1": 0.0,
        "CP": 0.0, "CR": 0.0, "cF1": 0.0,
        "q_predicted": q, "r_reference": r, "m_matched": 0
    }


def _harmonic_mean(p: float, r: float) -> float:
    return 2.0 * p * r / (p + r) if (p + r) > 0 else 0.0


def _k_metric(
    n_ij: List[List[int]], n_i: List[int], n_j: List[int], n_total: int
) -> Tuple[float, float, float]:
    """K-Metric (Eq. 4): geometric mean of ACP and AAP."""
    q, r = len(n_i), len(n_j)

    acp_sum = 0.0
    for i in range(q):
        if n_i[i] > 0:
            acp_sum += sum(n_ij[i][j] ** 2 for j in range(r)) / n_i[i]
    acp = acp_sum / float(n_total)

    aap_sum = 0.0
    for j in range(r):
        if n_j[j] > 0:
            aap_sum += sum(n_ij[i][j] ** 2 for i in range(q)) / n_j[j]
    aap = aap_sum / float(n_total)

    return acp, aap, math.sqrt(acp * aap)


def _pairwise_f1(
    n_ij: List[List[int]], n_i: List[int], n_j: List[int]
) -> Tuple[float, float, float]:
    """Pairwise-F1 (Eq. 5): precision/recall over co-clustered paper pairs."""
    num_pairs = sum(comb2(cell) for row in n_ij for cell in row)
    denom_pp = sum(comb2(n) for n in n_i)
    denom_pr = sum(comb2(n) for n in n_j)

    pp = (float(num_pairs) / float(denom_pp)) if denom_pp > 0 else 1.0
    pr = (float(num_pairs) / float(denom_pr)) if denom_pr > 0 else 1.0
    return pp, pr, _harmonic_mean(pp, pr)


def _cluster_f1(
    q_clusters: List[Set[str]], r_clusters: List[Set[str]]
) -> Tuple[float, float, float, int]:
    """Cluster-F1 (Eq. 6): based on exactly matching clusters."""
    m = sum(1 for pred_c in q_clusters if pred_c in r_clusters)
    q, r = len(q_clusters), len(r_clusters)
    cp = float(m) / float(q) if q > 0 else 0.0
    cr = float(m) / float(r) if r > 0 else 0.0
    return cp, cr, _harmonic_mean(cp, cr), m


def evaluate_clusters(
    predicted_clusters: List[Set[str]],
    ground_truth_clusters: List[Set[str]]
) -> Dict[str, float]:
    """
    Computes K-metric, pF1, and cF1 metrics.

    Args:
        predicted_clusters: List of sets of paper_ids for each generated cluster.
        ground_truth_clusters: List of sets of paper_ids for each reference cluster.

    Returns:
        Dict containing ACP, AAP, K, PP, PR, pF1, CP, CR, cF1 metrics.
    """
    # Filter out empty clusters
    q_clusters = [c for c in predicted_clusters if len(c) > 0]
    r_clusters = [c for c in ground_truth_clusters if len(c) > 0]

    q = len(q_clusters)
    r = len(r_clusters)

    if q == 0 or r == 0:
        return _empty_metrics(q, r)

    # Total unique papers across ground truth
    n_total = len(set().union(*r_clusters))
    if n_total == 0:
        return _empty_metrics(q, r)

    # Contingency matrix: n_ij = |predicted_i ∩ reference_j|
    n_i = [len(c) for c in q_clusters]
    n_j = [len(c) for c in r_clusters]
    n_ij = [[len(pred_c & ref_c) for ref_c in r_clusters] for pred_c in q_clusters]

    acp, aap, k_metric = _k_metric(n_ij, n_i, n_j, n_total)
    pp, pr, pf1 = _pairwise_f1(n_ij, n_i, n_j)
    cp, cr, cf1, m = _cluster_f1(q_clusters, r_clusters)

    return {
        "ACP": round(acp, 4),
        "AAP": round(aap, 4),
        "K_metric": round(k_metric, 4),
        "PP": round(pp, 4),
        "PR": round(pr, 4),
        "pF1": round(pf1, 4),
        "CP": round(cp, 4),
        "CR": round(cr, 4),
        "cF1": round(cf1, 4),
        "q_predicted": q,
        "r_reference": r,
        "m_matched": m
    }
