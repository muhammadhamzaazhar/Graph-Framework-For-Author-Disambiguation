"""
Constructs the initial Co-Author Graph Model (GM = {V, E}) from Bibliographic Data Collection (BDC).
Paper Section: "Graph model construction" (Shin et al., 2014)
"""

from typing import List, Dict
from gfad.models.citation import CitationRecord
from gfad.models.graph import GraphModel, AuthorVertex

def build_graph_model(records: List[CitationRecord], ambiguous_group: str) -> GraphModel:
    """
    Constructs a graph model GM = {V, E} for a given ambiguous group.
    1. Create a primary target author vertex for the ambiguous query name containing all publications.
    2. Create co-author vertices for every co-author appearing in the citation records.
    3. Connect target author vertex with co-authors of each paper.
    4. Connect co-authors of the same paper with each other (forming paper cliques/cycles).
    """
    gm = GraphModel()
    
    # Filter records for the target ambiguous group
    group_records = [r for r in records if r.ambiguous_group.lower() == ambiguous_group.lower()]
    if not group_records:
        return gm

    # Primary target vertex for ambiguous group name
    target_v_id = gm.generate_next_vid("v")
    target_vertex = AuthorVertex(v_id=target_v_id, name=ambiguous_group, publications=group_records)
    gm.add_vertex(target_vertex)

    # Map co-author name (lowercase clean) -> AuthorVertex
    coauthor_map: Dict[str, AuthorVertex] = {}

    for record in group_records:
        paper_coauthors = record.coauthors
        paper_vertices: List[AuthorVertex] = [target_vertex]

        for ca_name in paper_coauthors:
            ca_key = ca_name.strip().lower()
            if not ca_key:
                continue
            if ca_key not in coauthor_map:
                v_id = gm.generate_next_vid("v")
                ca_vertex = AuthorVertex(v_id=v_id, name=ca_name.strip(), publications=[])
                gm.add_vertex(ca_vertex)
                coauthor_map[ca_key] = ca_vertex
            
            ca_vertex = coauthor_map[ca_key]
            ca_vertex.add_publication(record)
            paper_vertices.append(ca_vertex)

        # Connect all pairs of authors in this paper (forming a clique/cycle in co-author graph)
        n = len(paper_vertices)
        for i in range(n):
            for j in range(i + 1, n):
                gm.add_edge(paper_vertices[i].v_id, paper_vertices[j].v_id)

    return gm
