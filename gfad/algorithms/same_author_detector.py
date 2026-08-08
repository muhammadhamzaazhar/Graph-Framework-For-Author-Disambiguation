"""
Detecting the Same Author among Vertices with Similar Names (Algorithm 4 in Shin et al., 2014).
"""

from typing import List, Set

from gfad.config import SHARED_COAUTHOR_MAX_DEPTH
from gfad.models.graph import GraphModel, AuthorVertex


def check_sharing_vertex(
    vertex: AuthorVertex,
    s_vertex: AuthorVertex,
    gm: GraphModel,
    max_depth: int = SHARED_COAUTHOR_MAX_DEPTH
) -> bool:
    """
    Implementation of checkSharingVertex function from Algorithm 4.
    Checks if target vertex and s_vertex share a common neighbor directly or indirectly
    (via bidirectional BFS bounded by max_depth hops).
    """
    v_nbr_ids = gm.get_neighbor_ids(vertex.v_id)
    s_nbr_ids = gm.get_neighbor_ids(s_vertex.v_id)

    # Direct common neighbor check
    if v_nbr_ids & s_nbr_ids:
        return True

    visited_v: Set[str] = {vertex.v_id}
    queue_v: List[str] = list(v_nbr_ids)

    visited_s: Set[str] = {s_vertex.v_id}
    queue_s: List[str] = list(s_nbr_ids)

    depth = 1
    while (queue_v or queue_s) and depth <= max_depth:
        if set(queue_v) & set(queue_s):
            return True

        queue_v = _expand_frontier(gm, queue_v, visited_v)
        queue_s = _expand_frontier(gm, queue_s, visited_s)
        depth += 1

    return False


def _expand_frontier(gm: GraphModel, frontier: List[str], visited: Set[str]) -> List[str]:
    """Advances a BFS frontier by one hop, marking current nodes as visited."""
    next_frontier: List[str] = []
    for n_id in frontier:
        visited.add(n_id)
        for nn_id in gm.get_neighbor_ids(n_id):
            if nn_id not in visited:
                next_frontier.append(nn_id)
    return next_frontier


def detect_same_author(
    target_vertex: AuthorVertex,
    sim_name_vertices: List[AuthorVertex],
    gm: GraphModel
) -> List[AuthorVertex]:
    """
    Implementation of Algorithm 4 (DetectSameAuthor procedure).
    Returns a list of vertices (including target_vertex) determined to refer to the same author.
    """
    merging_list: List[AuthorVertex] = [target_vertex]

    for s_vertex in sim_name_vertices:
        if s_vertex.v_id == target_vertex.v_id:
            continue
        if check_sharing_vertex(target_vertex, s_vertex, gm):
            merging_list.append(s_vertex)

    return merging_list
