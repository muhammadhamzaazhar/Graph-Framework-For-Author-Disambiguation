"""
Splitting Vertices with Polysemes (Algorithm 2 in Shin et al., 2014).
Splits a target vertex containing namesake authors along detected non-overlapping longest cycles.
"""

from typing import List, Set
from gfad.models.graph import GraphModel, AuthorVertex
from gfad.models.citation import CitationRecord

def split_namesakes(target_v_id: str, longest_cycles: List[Set[str]], gm: GraphModel) -> List[AuthorVertex]:
    """
    Implementation of Algorithm 2 (Splitting Namesakes).
    If longest_cycles has <= 1 cycle, no splitting is required.
    If longest_cycles has > 1 non-overlapping cycles, target_v_id represents multiple namesake authors.
    The vertex is split into multiple vertices, one per social circle cycle.
    
    Returns list of resulting author vertices created/updated from target_v_id.
    """
    target_vertex = gm.get_vertex(target_v_id)
    if not target_vertex or len(longest_cycles) <= 1:
        return [target_vertex] if target_vertex else []

    all_pubs = target_vertex.get_pub_list()
    split_vertices: List[AuthorVertex] = []
    
    # Track papers that get assigned to cycles
    assigned_paper_ids: Set[str] = set()

    for idx, cycle in enumerate(longest_cycles):
        # getNeighborsInCycle(vertex, cycle, GM)
        cycle_neighbor_ids = list(cycle - {target_v_id})
        
        # Collect all publications of co-authors in this cycle
        n_pubs: List[CitationRecord] = []
        for n_id in cycle_neighbor_ids:
            nbr_vertex = gm.get_vertex(n_id)
            if nbr_vertex:
                n_pubs.extend(nbr_vertex.get_pub_list())

        n_pub_ids = {p.paper_id for p in n_pubs}

        # splitPubs <- allPubs intersect nPubs, excluding papers already claimed by an earlier cycle
        split_pubs = [p for p in all_pubs if p.paper_id in n_pub_ids and p.paper_id not in assigned_paper_ids]
        
        # If no intersection found (edge case), fallback to publications mentioning co-authors
        if not split_pubs:
            cycle_coauthor_names = {gm.get_vertex(n_id).name.lower() for n_id in cycle_neighbor_ids if gm.get_vertex(n_id)}
            split_pubs = [
                p for p in all_pubs 
                if any(ca.lower() in cycle_coauthor_names for ca in p.coauthors)
            ]

        for p in split_pubs:
            assigned_paper_ids.add(p.paper_id)

        if idx == 0:
            # First element of longestCycles: update existing target_vertex
            target_vertex.set_publications(split_pubs)
            gm.remove_all_edges(target_v_id)
            gm.link_edges(target_v_id, cycle_neighbor_ids)
            split_vertices.append(target_vertex)
        else:
            # Subsequent elements: create new vertex
            new_v = gm.create_new_vertex(name=target_vertex.name, pubs=split_pubs)
            gm.link_edges(new_v.v_id, cycle_neighbor_ids)
            split_vertices.append(new_v)

    # Handle unassigned publications (papers that didn't fit into any multi-node cycle)
    unassigned_pubs = [p for p in all_pubs if p.paper_id not in assigned_paper_ids]
    if unassigned_pubs:
        # Create a separate vertex for unassigned/isolated papers (outliers)
        outlier_v = gm.create_new_vertex(name=target_vertex.name, pubs=unassigned_pubs)
        split_vertices.append(outlier_v)

    return split_vertices
