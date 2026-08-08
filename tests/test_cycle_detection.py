"""
Unit tests for cycle detection and Algorithm 1 (DetectLongestCycles).
"""

import unittest
from gfad.models.graph import GraphModel, AuthorVertex
from gfad.algorithms.cycle_detector import find_elementary_cycles, detect_longest_cycles

class TestCycleDetection(unittest.TestCase):

    def test_detect_longest_cycles_algorithm_1(self):
        """
        Test sub-cycle elimination and merging of overlapping cycles.
        """
        # Cycle 1: {v1, v2, v3, v5} (len 4)
        # Cycle 2: {v1, v2, v3} (sub-cycle of Cycle 1, should be removed)
        # Cycle 3: {v1, v6, v7} (len 3, non-overlapping with Cycle 1 co-authors)
        c1 = {"v1", "v2", "v3", "v5"}
        c2 = {"v1", "v2", "v3"}
        c3 = {"v1", "v6", "v7"}

        longest = detect_longest_cycles([c1, c2, c3], target_v_id="v1")
        
        # Should retain 2 non-overlapping cycles: {v1, v2, v3, v5} and {v1, v6, v7}
        self.assertEqual(len(longest), 2)
        v2_cycle = [c for c in longest if "v2" in c][0]
        v6_cycle = [c for c in longest if "v6" in c][0]
        self.assertIn("v5", v2_cycle)
        self.assertIn("v7", v6_cycle)

    def test_cycle_merging(self):
        """
        Cycles sharing co-authors should merge into a single wide social circle.
        """
        c1 = {"v1", "v2", "v3"}
        c2 = {"v1", "v3", "v4"}  # Shares co-author v3 with c1
        longest = detect_longest_cycles([c1, c2], target_v_id="v1")
        self.assertEqual(len(longest), 1)
        self.assertEqual(longest[0], {"v1", "v2", "v3", "v4"})

if __name__ == '__main__':
    unittest.main()
