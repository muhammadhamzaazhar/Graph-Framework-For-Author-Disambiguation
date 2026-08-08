"""
Detection of Longest Non-Overlapping Cycles (Algorithm 1 in Shin et al., 2014).
Combines elementary cycle enumeration with sub-cycle removal and cycle merging.
"""

from typing import Dict, List, Set

from gfad.models.graph import GraphModel


def _dedupe_cycles(cycles: List[Set[str]]) -> List[Set[str]]:
    """Removes duplicate cycle sets while preserving first-seen order."""
    unique: List[Set[str]] = []
    for c in cycles:
        if c not in unique:
            unique.append(c)
    return unique


def find_elementary_cycles(gm: GraphModel, target_v_id: str) -> List[Set[str]]:
    """
    Extracts elementary co-authorship cycles passing through target_v_id in the graph model.
    As specified in Shin et al. (2014) Section 'Namesake resolution':
    "A cycle in the graph model of GFAD ... is generated from each publication, and thus,
    each cycle denotes the co-authorship for each publication."
    """
    target_vertex = gm.get_vertex(target_v_id)
    if not target_vertex:
        return []

    cycles: List[Set[str]] = []

    # Map co-author name (lowercase) to vertex ID in GM for fast lookup
    coauthor_v_map: Dict[str, str] = {
        nbr.name.lower(): nbr.v_id for nbr in gm.get_neighbors(target_v_id)
    }

    # 1. Extract publication co-authorship cycles directly from publications
    for pub in target_vertex.get_pub_list():
        cycle_nodes = {target_v_id}
        for ca_name in pub.coauthors:
            ca_key = ca_name.strip().lower()
            if ca_key in coauthor_v_map:
                cycle_nodes.add(coauthor_v_map[ca_key])

        # Include cycles with co-authors
        if len(cycle_nodes) > 1:
            cycles.append(cycle_nodes)

    # 2. Add connected co-author triangles/cycles from graph adjacency
    nbr_ids = list(gm.get_neighbor_ids(target_v_id))
    for i in range(len(nbr_ids)):
        for j in range(i + 1, len(nbr_ids)):
            n1, n2 = nbr_ids[i], nbr_ids[j]
            if n2 in gm.get_neighbor_ids(n1):
                cycles.append({target_v_id, n1, n2})

    return _dedupe_cycles(cycles)


def detect_longest_cycles(cycles: List[Set[str]], target_v_id: str) -> List[Set[str]]:
    """
    Implementation of Algorithm 1 (Detection of Longest Cycles) from Shin et al., 2014.
    1. Sort cycles descending by length.
    2. Remove sub-cycles (if c1 is a subset of c2, remove c1).
    3. Merge cycles that share co-author vertices (other than target_v_id)
       until a fixed point is reached.
    """
    if not cycles:
        return []

    # Sort cycles in descending order of length
    sorted_cycles = sorted(_dedupe_cycles(cycles), key=len, reverse=True)

    # Remove sub-cycles (keep only maximal cycles)
    maximal_cycles: List[Set[str]] = []
    for c in sorted_cycles:
        if not any(c.issubset(mc) for mc in maximal_cycles):
            maximal_cycles.append(set(c))

    # Merge cycles that share co-author vertices (excluding target_v_id), repeating until no further merges occur (transitive social-circle closure).
    merged_cycles = maximal_cycles
    changed = True
    while changed:
        changed = False
        new_list: List[Set[str]] = []
        for c in merged_cycles:
            coauthor_set = c - {target_v_id}
            for existing in new_list:
                if coauthor_set & (existing - {target_v_id}):
                    existing.update(c)
                    changed = True
                    break
            else:
                new_list.append(c)
        merged_cycles = new_list

    return merged_cycles
