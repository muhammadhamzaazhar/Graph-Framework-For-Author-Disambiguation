"""
Searching for Similar Names using Token-level LCS (Algorithm 3 & Eq. 2 in Shin et al., 2014).
"""

import re
from typing import List

from gfad.config import LCS_SIMILARITY_THRESHOLD
from gfad.models.graph import GraphModel, AuthorVertex

def get_lcs(s1: str, s2: str) -> int:
    """
    Computes Longest Common Subsequence (LCS) length between two token strings.
    """
    s1_lower = s1.lower()
    s2_lower = s2.lower()
    m, n = len(s1_lower), len(s2_lower)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1_lower[i - 1] == s2_lower[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
                
    return dp[m][n]


def tokenize(name: str) -> List[str]:
    """
    Tokenizes an author name string using spaces and punctuation marks as delimiters.
    """
    tokens = re.split(r'[\s\.,\-_]+', name.strip())
    return [t for t in tokens if t]


def name_sim(s1: str, s2: str) -> float:
    """
    Implementation of Equation (2) for author name similarity:
    nameSim(s1, s2) = sum_{t1 in s1} max_{t2 in s2} LCS(t1, t2) / max_{i=1,2} Length(si)
    where Length(si) is the sum of character lengths of all tokens in string si.
    """
    tokens1 = tokenize(s1)
    tokens2 = tokenize(s2)
    
    if not tokens1 or not tokens2:
        return 0.0

    total_lcs = 0
    for t1 in tokens1:
        max_lcs = 0
        for t2 in tokens2:
            current_lcs = get_lcs(t1, t2)
            if current_lcs > max_lcs:
                max_lcs = current_lcs
        total_lcs += max_lcs

    # Sum of token lengths for s1 and s2
    len1 = sum(len(t) for t in tokens1)
    len2 = sum(len(t) for t in tokens2)
    max_len = max(len1, len2)

    if max_len == 0:
        return 0.0

    similarity = total_lcs / float(max_len)
    return min(similarity, 1.0)


def search_similar_names(
    target_vertex: AuthorVertex,
    gm: GraphModel,
    threshold: float = LCS_SIMILARITY_THRESHOLD
) -> List[AuthorVertex]:
    """
    Implementation of Algorithm 3 (Searching Similar Names).
    Returns list of vertices in GM (excluding target_vertex) with nameSim >= threshold.
    """
    similar_vertices: List[AuthorVertex] = []
    all_vertices = gm.get_all_vertices()
    target_name = target_vertex.get_name()

    for comp_v in all_vertices:
        if comp_v.v_id == target_vertex.v_id:
            continue
        comp_name = comp_v.get_name()
        sim_val = name_sim(target_name, comp_name)
        if sim_val >= threshold:
            similar_vertices.append(comp_v)

    return similar_vertices
