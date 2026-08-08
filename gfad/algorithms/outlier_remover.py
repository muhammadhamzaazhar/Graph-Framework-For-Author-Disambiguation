"""
Removing Outliers using Title Keyword Cosine Similarity (Algorithm 6 & Eq. 3 in Shin et al., 2014).
"""

import math
import re
from typing import Dict, List, Optional

from gfad.config import OUTLIER_NAME_SIMILARITY_THRESHOLD
from gfad.models.graph import GraphModel, AuthorVertex
from gfad.algorithms.name_similarity import search_similar_names

# Basic English stop words excluded from title feature vectors
TITLE_STOPWORDS = frozenset({
    'a', 'an', 'the', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
    'by', 'from', 'up', 'about', 'into', 'over', 'after', 'is', 'are', 'was',
    'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
    'using', 'based', 'via', 'its'
})

MIN_TOKEN_LENGTH = 2


def tokenize_title(title: str) -> List[str]:
    """
    Tokenizes paper title into clean word tokens, dropping stop words.
    """
    words = re.findall(r'\b[a-zA-Z0-9]+\b', title.lower())
    return [w for w in words if w not in TITLE_STOPWORDS and len(w) >= MIN_TOKEN_LENGTH]


def build_feature_vector(vertex: AuthorVertex) -> Dict[str, float]:
    """
    Composes a feature vector (tf representation) from words in paper titles.
    """
    vector: Dict[str, float] = {}
    for pub in vertex.get_pub_list():
        for w in tokenize_title(pub.title):
            vector[w] = vector.get(w, 0.0) + 1.0
    return vector


def cosine_similarity(fv1: Dict[str, float], fv2: Dict[str, float]) -> float:
    """
    Implementation of Equation (3) for Cosine Similarity between feature vectors:

    sim(fv1, fv2) = (fv1 . fv2) / (||fv1|| * ||fv2||)
    """
    if not fv1 or not fv2:
        return 0.0

    dot_product = sum(val * fv2[w] for w, val in fv1.items() if w in fv2)
    norm1 = math.sqrt(sum(val ** 2 for val in fv1.values()))
    norm2 = math.sqrt(sum(val ** 2 for val in fv2.values()))

    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0

    return dot_product / (norm1 * norm2)


def remove_outliers(gm: GraphModel, name_sim_threshold: float = OUTLIER_NAME_SIMILARITY_THRESHOLD) -> List[dict]:
    """
    Implementation of Algorithm 6 (Removing Outliers).
    1. Finds isolated vertices in GM (vertices with 0 co-authors/edges).
    2. Searches for non-outlier candidate vertices with similar author names.
    3. Calculates cosine similarity of title feature vectors (Eq. 3).
    4. Merges outlier publication list into candidate vertex with highest similarity.
    5. Removes outlier vertex from GM.

    Returns list of outlier merge log dicts.
    """
    merge_logs = []

    # Identify outliers (vertices with 0 neighbor edges)
    outliers = [v for v in gm.get_all_vertices() if not gm.get_neighbor_ids(v.v_id)]
    outlier_ids = {o.v_id for o in outliers}

    for outlier in outliers:
        if outlier.v_id not in gm.vertices:
            continue  # Already removed in a previous step

        # Search for vertices with similar names (excluding outliers)
        sim_name_vertices = search_similar_names(outlier, gm, threshold=name_sim_threshold)
        candidate_vertices = [
            v for v in sim_name_vertices
            if v.v_id not in outlier_ids and v.v_id in gm.vertices
        ]

        # If no non-outlier similar name vertex found, search all non-outlier vertices in GM
        if not candidate_vertices:
            candidate_vertices = [
                v for v in gm.get_all_vertices() if v.v_id not in outlier_ids
            ]

        if not candidate_vertices:
            continue

        outlier_fv = build_feature_vector(outlier)
        max_value = -1.0
        max_vertex: Optional[AuthorVertex] = None

        for cand_v in candidate_vertices:
            sim_val = cosine_similarity(outlier_fv, build_feature_vector(cand_v))
            if sim_val > max_value:
                max_value = sim_val
                max_vertex = cand_v

        if max_vertex:
            # Merge outlier publications into max_vertex
            for pub in outlier.get_pub_list():
                max_vertex.add_publication(pub)

            merge_logs.append({
                "outlier_v_id": outlier.v_id,
                "outlier_name": outlier.name,
                "merged_into_v_id": max_vertex.v_id,
                "merged_into_name": max_vertex.name,
                "similarity_score": round(max_value, 4)
            })

            gm.remove_vertex(outlier.v_id)

    return merge_logs
