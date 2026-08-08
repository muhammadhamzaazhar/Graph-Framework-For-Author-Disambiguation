"""
Merging Heteronymous Names (Algorithm 5 in Shin et al., 2014).
Merges multiple vertices representing heteronyms of the same author into a single vertex.
"""

from typing import List
from gfad.models.graph import GraphModel, AuthorVertex
from gfad.models.citation import CitationRecord

def merge_heteronymous_names(merging_list: List[AuthorVertex], gm: GraphModel) -> AuthorVertex:
    """
    Implementation of Algorithm 5 (Merging Heteronymous Names).
    1. Base vertex is chosen as the min-indexed vertex in merging_list.
    2. Publications of all merged vertices are combined into base vertex.
    3. All neighbor edges of merged vertices are relinked to base vertex.
    4. Merged vertices are removed from GM.
    
    Returns the updated base vertex.
    """
    if not merging_list:
        raise ValueError("merging_list cannot be empty")
    if len(merging_list) == 1:
        return merging_list[0]

    # Select base vertex with lowest v_id index
    sorted_vertices = sorted(merging_list, key=lambda v: v.v_id)
    base_vertex = sorted_vertices[0]
    vertices_to_merge = sorted_vertices[1:]

    # Collect publications
    combined_pubs: List[CitationRecord] = base_vertex.get_pub_list()
    seen_paper_ids = {p.paper_id for p in combined_pubs}

    for m_vertex in vertices_to_merge:
        for pub in m_vertex.get_pub_list():
            if pub.paper_id not in seen_paper_ids:
                combined_pubs.append(pub)
                seen_paper_ids.add(pub.paper_id)

    # Update base vertex publication information
    base_vertex.set_publications(combined_pubs)

    # Relink neighbor edges and remove merged vertices
    for m_vertex in vertices_to_merge:
        nbr_ids = list(gm.get_neighbor_ids(m_vertex.v_id))
        for n_id in nbr_ids:
            if n_id != base_vertex.v_id:
                gm.add_edge(base_vertex.v_id, n_id)
        gm.remove_vertex(m_vertex.v_id)

    return base_vertex
