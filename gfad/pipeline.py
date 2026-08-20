"""
End-to-End Pipeline for GFAD (Graph Framework for Author Disambiguation).
Supports GFAD-AD (without outlier removal) and GFAD-OR (with outlier removal).
Paper: Shin et al. (2014)
"""

from typing import Dict, List, Set

from gfad.config import LCS_SIMILARITY_THRESHOLD
from gfad.models.citation import CitationRecord
from gfad.models.graph import GraphModel
from gfad.algorithms.graph_builder import build_graph_model
from gfad.algorithms.cycle_detector import find_elementary_cycles, detect_longest_cycles
from gfad.algorithms.namesake_splitter import split_namesakes
from gfad.algorithms.name_similarity import search_similar_names
from gfad.algorithms.same_author_detector import detect_same_author
from gfad.algorithms.heteronymous_merger import merge_heteronymous_names
from gfad.algorithms.outlier_remover import remove_outliers
from gfad.evaluation.metrics import evaluate_clusters


class GFADPipeline:
    """
    Main execution engine for GFAD framework.
    """

    def __init__(self, with_outlier_removal: bool = False, lcs_threshold: float = LCS_SIMILARITY_THRESHOLD):
        self.with_outlier_removal = with_outlier_removal
        self.lcs_threshold = lcs_threshold

    @property
    def mode(self) -> str:
        return "GFAD-OR" if self.with_outlier_removal else "GFAD-AD"

    def run_group(self, records: List[CitationRecord], ambiguous_group: str) -> Dict:
        """
        Executes GFAD disambiguation for a single ambiguous group.
        Returns dictionary containing:
          - initial_graph: GraphModel state before disambiguation
          - final_graph: GraphModel state after disambiguation
          - snapshots: Graph states after each stage
          - trace: Step-by-step audit log
          - metrics: Evaluation metrics (K-metric, pF1, cF1)
          - predicted_clusters: List of paper_id sets per predicted cluster
          - ground_truth_clusters: List of paper_id sets per reference cluster
        """
        group_records = [r for r in records if r.ambiguous_group.lower() == ambiguous_group.lower()]
        if not group_records:
            return {"error": f"No records found for group '{ambiguous_group}'"}

        # 1. Build initial Graph Model (BDC -> GM)
        gm = build_graph_model(group_records, ambiguous_group)
        initial_snapshot = gm.clone()

        trace = {
            "ambiguous_group": ambiguous_group,
            "mode": self.mode,
            "initial_vertex_count": len(gm.vertices),
            "initial_edge_count": sum(len(n) for n in gm.adjacency.values()) // 2,
            "steps": [{
                "stage": "Graph Model Construction",
                "description": f"Built initial graph with {len(gm.vertices)} vertices for '{ambiguous_group}'.",
                "vertex_count": len(gm.vertices)
            }]
        }

        # 2. Namesake Resolution (Cycle Detection & Splitting)
        split_count = self._resolve_namesakes(gm, ambiguous_group)
        after_namesake_snapshot = gm.clone()
        trace["steps"].append({
            "stage": "Namesake Resolution",
            "description": f"Detected namesake polysemes. Created {split_count} split author vertices.",
            "vertex_count": len(gm.vertices)
        })

        # Identity vertices: those actually representing the ambiguous target author
        # (as opposed to coauthor vertices, which also hold copies of the same
        # publications and must not be treated as separate predicted clusters).
        identity_ids = {v.v_id for v in gm.get_all_vertices() if v.name.lower() == ambiguous_group.lower()}

        # 3. Heteronymous Name Resolution (Similarity Search, Same Author Detection & Merging)
        merge_count = self._resolve_heteronyms(gm, ambiguous_group, identity_ids)
        after_heteronym_snapshot = gm.clone()
        trace["steps"].append({
            "stage": "Heteronymous Resolution",
            "description": f"Merged {merge_count} heteronymous vertices with similar names.",
            "vertex_count": len(gm.vertices)
        })

        # 4. Outlier Removal (Algorithm 6)
        if self.with_outlier_removal:
            outlier_logs = remove_outliers(gm)
            for log in outlier_logs:
                if log["outlier_v_id"] in identity_ids:
                    identity_ids.discard(log["outlier_v_id"])
                    identity_ids.add(log["merged_into_v_id"])
            trace["steps"].append({
                "stage": "Outlier Removal",
                "description": f"Merged {len(outlier_logs)} isolated outlier vertices using title keyword cosine similarity.",
                "vertex_count": len(gm.vertices),
                "outlier_logs": outlier_logs
            })
        after_outlier_snapshot = gm.clone()

        # 5. Evaluate predicted clusters against ground truth
        predicted_clusters = self._extract_predicted_clusters(gm, identity_ids)
        ground_truth_clusters = self._extract_ground_truth_clusters(group_records)
        metrics = evaluate_clusters(predicted_clusters, ground_truth_clusters)

        return {
            "ambiguous_group": ambiguous_group,
            "mode": self.mode,
            "record_count": len(group_records),
            "initial_graph": initial_snapshot,
            "final_graph": gm,
            "snapshots": {
                "initial": initial_snapshot,
                "after_namesake": after_namesake_snapshot,
                "after_heteronym": after_heteronym_snapshot,
                "after_outlier": after_outlier_snapshot
            },
            "trace": trace,
            "metrics": metrics,
            "predicted_clusters": [list(c) for c in predicted_clusters],
            "ground_truth_clusters": [list(c) for c in ground_truth_clusters]
        }

    def _resolve_namesakes(self, gm: GraphModel, ambiguous_group: str) -> int:
        """
        Splits target vertices whose co-authorship cycles form multiple
        non-overlapping social circles (Algorithms 1 & 2).
        Returns the number of new vertices created by splitting.
        """
        target_vertices = [v for v in gm.get_all_vertices() if v.name.lower() == ambiguous_group.lower()]
        split_count = 0

        for target_v in target_vertices:
            if target_v.v_id not in gm.vertices:
                continue

            raw_cycles = find_elementary_cycles(gm, target_v.v_id)
            longest_cycles = detect_longest_cycles(raw_cycles, target_v.v_id)

            if len(longest_cycles) > 1:
                split_nodes = split_namesakes(target_v.v_id, longest_cycles, gm)
                split_count += len(split_nodes) - 1

        return split_count

    def _resolve_heteronyms(self, gm: GraphModel, ambiguous_group: str, identity_ids: Set[str]) -> int:
        """
        Merges vertices with similar names that share co-authors
        (Algorithms 3, 4 & 5). Returns the number of vertices merged away.
        Only searches heteronyms for vertices that represent the target author's
        identity (identity_ids), not arbitrary coauthor vertices; identity_ids is
        updated in place to follow the base vertex resulting from each merge.
        """
        target_vertices = [v for v in gm.get_all_vertices() if v.v_id in identity_ids]
        merge_count = 0

        for target_v in target_vertices:
            if target_v.v_id not in gm.vertices:
                continue

            sim_vertices = search_similar_names(target_v, gm, threshold=self.lcs_threshold)
            if sim_vertices:
                merging_list = detect_same_author(target_v, sim_vertices, gm)
                if len(merging_list) > 1:
                    base_vertex = merge_heteronymous_names(merging_list, gm)
                    for m_vertex in merging_list:
                        identity_ids.discard(m_vertex.v_id)
                    identity_ids.add(base_vertex.v_id)
                    merge_count += len(merging_list) - 1

        return merge_count

    @staticmethod
    def _extract_predicted_clusters(gm: GraphModel, identity_ids: Set[str]) -> List[Set[str]]:
        """Each surviving identity vertex (descended from the target author) is one predicted cluster."""
        clusters: List[Set[str]] = []
        for v in gm.get_all_vertices():
            if v.v_id not in identity_ids:
                continue
            paper_ids = {p.paper_id for p in v.get_pub_list()}
            if paper_ids:
                clusters.append(paper_ids)
        return clusters

    @staticmethod
    def _extract_ground_truth_clusters(group_records: List[CitationRecord]) -> List[Set[str]]:
        """Groups paper_ids by their ground-truth author label."""
        gt_map: Dict[str, Set[str]] = {}
        for r in group_records:
            gt_map.setdefault(r.ground_truth_label, set()).add(r.paper_id)
        return list(gt_map.values())
