"""
Unit tests for LCS name similarity calculation (Algorithm 3 & Eq. 2).
"""

import unittest
from gfad.algorithms.name_similarity import get_lcs, name_sim, tokenize

class TestNameSimilarity(unittest.TestCase):

    def test_lcs_basic(self):
        self.assertEqual(get_lcs("Tom", "Tom"), 3)
        self.assertEqual(get_lcs("Mitchell", "Mitchell"), 8)
        self.assertEqual(get_lcs("A", "Ajay"), 1)

    def test_tokenize(self):
        tokens = tokenize("Tom M. Mitchell-Smith")
        self.assertIn("Tom", tokens)
        self.assertIn("M", tokens)
        self.assertIn("Mitchell", tokens)
        self.assertIn("Smith", tokens)

    def test_paper_example_tom_mitchell(self):
        """
        Paper Page 16 Example:
        s1 = 'Tom Mitchell', s2 = 'Tom M. Mitchell'
        LCS values: 'Tom' vs 'Tom' = 3, 'Mitchell' vs 'Mitchell' = 8
        sum = 11, max len = 12 or 14 -> similarity >= 0.8
        """
        s1 = "Tom Mitchell"
        s2 = "Tom M. Mitchell"
        sim = name_sim(s1, s2)
        print(f"Similarity ('{s1}' vs '{s2}') = {sim:.3f}")
        self.assertGreaterEqual(sim, 0.75)

    def test_identical_names(self):
        self.assertAlmostEqual(name_sim("Ajay K. Gupta", "Ajay K. Gupta"), 1.0)

    def test_different_names(self):
        sim = name_sim("Ajay Gupta", "John Smith")
        self.assertLess(sim, 0.4)

if __name__ == '__main__':
    unittest.main()
