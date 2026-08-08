"""
Graph Model representing author vertices and co-authorship edges (Eq. 1 in Shin et al., 2014).
"""

from typing import Dict, List, Set, Optional
from .citation import CitationRecord

class AuthorVertex:
    """
    Represents an author vertex in the GFAD graph model.
    vi = {Identifier, Name, Publications_i}
    """
    def __init__(self, v_id: str, name: str, publications: Optional[List[CitationRecord]] = None):
        self.v_id = v_id
        self.name = name
        self.publications = publications or []

    def get_pub_list(self) -> List[CitationRecord]:
        return list(self.publications)

    def get_name(self) -> str:
        return self.name

    def add_publication(self, pub: CitationRecord):
        if not any(p.paper_id == pub.paper_id for p in self.publications):
            self.publications.append(pub)

    def remove_publication(self, paper_id: str):
        self.publications = [p for p in self.publications if p.paper_id != paper_id]

    def set_publications(self, pubs: List[CitationRecord]):
        self.publications = list(pubs)

    def to_dict(self) -> dict:
        return {
            "v_id": self.v_id,
            "name": self.name,
            "publications": [p.to_dict() for p in self.publications]
        }

    def __repr__(self) -> str:
        return f"<AuthorVertex {self.v_id}: '{self.name}' ({len(self.publications)} pubs)>"


class GraphModel:
    """
    GM = {V, E}
    Represents co-authorship graph model for an ambiguous author group.
    """
    def __init__(self):
        self.vertices: Dict[str, AuthorVertex] = {}
        self.adjacency: Dict[str, Set[str]] = {}
        self._vertex_counter = 0

    def generate_next_vid(self, prefix: str = "v") -> str:
        self._vertex_counter += 1
        return f"{prefix}{self._vertex_counter}"

    def add_vertex(self, vertex: AuthorVertex):
        if vertex.v_id not in self.vertices:
            self.vertices[vertex.v_id] = vertex
            self.adjacency[vertex.v_id] = set()

    def create_new_vertex(self, name: str, pubs: Optional[List[CitationRecord]] = None) -> AuthorVertex:
        v_id = self.generate_next_vid()
        vertex = AuthorVertex(v_id=v_id, name=name, publications=pubs)
        self.add_vertex(vertex)
        return vertex

    def remove_vertex(self, v_id: str):
        if v_id in self.vertices:
            # Remove all edges connecting to v_id
            self.remove_all_edges(v_id)
            del self.vertices[v_id]
            del self.adjacency[v_id]

    def add_edge(self, v1_id: str, v2_id: str):
        if v1_id == v2_id:
            return
        if v1_id in self.vertices and v2_id in self.vertices:
            self.adjacency[v1_id].add(v2_id)
            self.adjacency[v2_id].add(v1_id)

    def remove_edge(self, v1_id: str, v2_id: str):
        if v1_id in self.adjacency and v2_id in self.adjacency[v1_id]:
            self.adjacency[v1_id].remove(v2_id)
        if v2_id in self.adjacency and v1_id in self.adjacency[v2_id]:
            self.adjacency[v2_id].remove(v1_id)

    def remove_all_edges(self, v_id: str):
        if v_id in self.adjacency:
            neighbors = list(self.adjacency[v_id])
            for n_id in neighbors:
                self.remove_edge(v_id, n_id)

    def link_edges(self, v_id: str, neighbor_ids: List[str]):
        for n_id in neighbor_ids:
            self.add_edge(v_id, n_id)

    def get_neighbors(self, v_id: str) -> List[AuthorVertex]:
        if v_id not in self.adjacency:
            return []
        return [self.vertices[n_id] for n_id in self.adjacency[v_id] if n_id in self.vertices]

    def get_neighbor_ids(self, v_id: str) -> Set[str]:
        return self.adjacency.get(v_id, set()).copy()

    def get_all_vertices(self) -> List[AuthorVertex]:
        return list(self.vertices.values())

    def get_vertex(self, v_id: str) -> Optional[AuthorVertex]:
        return self.vertices.get(v_id)

    def clone(self) -> 'GraphModel':
        """Deep clone graph model for state tracking."""
        new_gm = GraphModel()
        new_gm._vertex_counter = self._vertex_counter
        for v in self.vertices.values():
            new_gm.vertices[v.v_id] = AuthorVertex(
                v_id=v.v_id,
                name=v.name,
                publications=[CitationRecord.from_dict(p.to_dict()) for p in v.publications]
            )
        for v_id, nbrs in self.adjacency.items():
            new_gm.adjacency[v_id] = nbrs.copy()
        return new_gm
