# GFAD: Graph Framework for Author Disambiguation (Shin et al., 2014)

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Paper](https://img.shields.io/badge/paper-Scientometrics%202014-green.svg)](https://doi.org/10.1007/s11192-014-1289-4)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An end-to-end Python implementation of the paper **"Author name disambiguation using a graph model with node splitting and merging based on bibliographic information"** (Dongwook Shin, Taehwan Kim, Joongmin Choi, Jungsun Kim — *Scientometrics*, 2014).

This repository provides a complete framework for resolving author name ambiguity in scholarly digital libraries (DBLP/Arnetminer) using co-authorship graphs, cycle detection algorithms, tokenized LCS name similarity, and title keyword cosine similarity.

---

## Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture & Paper Algorithms](#-system-architecture--paper-algorithms)
- [Evaluation Metrics](#-evaluation-metrics)
- [Project Directory Structure](#-project-directory-structure)
- [Installation & Getting Started](#-installation--getting-started)
- [Command-Line Usage (CLI)](#-command-line-usage-cli)
- [Configuration](#-configuration)
- [Benchmark Results](#-benchmark-results-summary)
- [Citation](#-citation)

---

## Overview

Author ambiguity in scholarly databases arises mainly from two core problems:
1. **Namesake Problem (Polysemes)**: Multiple real-world authors publish under the exact same name (e.g. 26 distinct individuals named `A. Gupta`, 100 individuals named `J. Lee`).
2. **Heteronymous Name Problem (Synonyms)**: A single author uses multiple name variations across publications (e.g. `Tom Mitchell`, `Tom M. Mitchell`, `T. Mitchell`).

**GFAD** resolves both problems using **pure co-authorship graph operations**:
- **Namesake Polysemes** are resolved by detecting elementary co-authorship cycles and splitting author vertices along non-overlapping social circles.
- **Heteronymous Synonyms** are resolved by searching for similar author names using tokenized Longest Common Subsequence (LCS) and merging vertices that share a common co-author.
- **Isolated Outliers** (single-author papers without co-authors) are resolved using cosine similarity of publication-title feature vectors.

---

## Key Features

- **Complete Algorithmic Fidelity**: Implements all 6 algorithms described in Shin et al. (2014).
- **Comprehensive Metrics Engine**: Computes $K$-Metric ($\text{ACP}, \text{AAP}, K$), Pairwise-$F_1$ ($\text{PP}, \text{PR}, pF1$), and Cluster-$F_1$ ($\text{CP}, \text{CR}, cF1$).
- **Ablation Modes Supported**: Run both `GFAD-AD` (without outlier removal) and `GFAD-OR` (with outlier removal).
- **Central Configuration**: All paths, thresholds, and benchmark group definitions live in a single module (`gfad/config.py`).
- **Zero External Dependencies**: Core GFAD algorithms and CLI are written in pure Python using only standard library modules.
- **Automated Test Suite**: Unit tests verifying LCS name similarity, cycle detection, and evaluation metrics.

---

## System Architecture & Paper Algorithms

```
                       +-----------------------------------+
                       | Bibliographic Data Collection BDC |
                       +-----------------------------------+
                                         |
                                         v
                       +-----------------------------------+
                       |      Graph Model Constructor      |
                       +-----------------------------------+
                                         |
                                         v
                       +-----------------------------------+
                       |         Namesake Resolver         |
                       |  - Cycle Detector (Algorithm 1)   |
                       |  - Namesake Splitter (Algorithm 2)|
                       +-----------------------------------+
                                         |
                                         v
                       +-----------------------------------+
                       |   Heteronymous Name Resolver      |
                       |  - Similar Name Search (Alg 3)    |
                       |  - Same Author Detect (Algorithm 4)|
                       |  - Heteronym Merger (Algorithm 5) |
                       +-----------------------------------+
                                         |
                                         v
                       +-----------------------------------+
                       |     Outlier Remover (Alg 6)       |
                       +-----------------------------------+
```

The four stages are orchestrated by `GFADPipeline` (`gfad/pipeline.py`), which exposes one
public method — `run_group(records, ambiguous_group)` — and internally delegates to
`_resolve_namesakes`, `_resolve_heteronyms`, outlier removal, and cluster extraction.

### Algorithm Summary

1. **Graph Model Construction (`gfad/algorithms/graph_builder.py`)**
   - Represents the co-authorship network as $GM = (V, E)$, where $v_i = \{\text{Identifier}, \text{Name}, \text{Publications}_i\}$ and edges $(u, v)$ denote co-authorship.

2. **Cycle Detection & Longest Non-Overlapping Cycles (`gfad/algorithms/cycle_detector.py`)**
   - **Algorithm 1 (`DetectLongestCycles`)**: Finds elementary simple cycles passing through the target vertex. Sorts cycles by length descending, eliminates sub-cycles ($c_1 \subseteq c_2$), and merges cycles that share co-authors until a fixed point is reached.

3. **Namesake Splitting (`gfad/algorithms/namesake_splitter.py`)**
   - **Algorithm 2 (`SplitNamesakes`)**: Splits a polyseme author vertex with multiple longest non-overlapping cycles into distinct vertices per social circle, reassigning publications and relinking neighboring edges.

4. **Searching Similar Names (`gfad/algorithms/name_similarity.py`)**
   - **Algorithm 3 (`SearchSimilarNames`)** & **Equation (2)**: Measures author name similarity using token-level Longest Common Subsequence (LCS):
     $$\text{nameSim}(s_1, s_2) = \frac{\sum_{t_1 \in \text{Tokens}(s_1)} \max_{t_2 \in \text{Tokens}(s_2)} \text{LCS}(t_1, t_2)}{\max_{i=1,2} \text{Length}(s_i)}$$
     *(Threshold $\ge 0.8$)*.

5. **Same Author Detection & Heteronymous Merging (`gfad/algorithms/same_author_detector.py` & `heteronymous_merger.py`)**
   - **Algorithm 4 (`DetectSameAuthor`)**: Checks if vertices with similar names share a common co-author directly or via bounded bidirectional BFS (`checkSharingVertex`).
   - **Algorithm 5 (`MergeHeteronymousNames`)**: Combines heteronym vertices into a single base vertex.

6. **Outlier Removal (`gfad/algorithms/outlier_remover.py`)**
   - **Algorithm 6 (`RemoveOutliers`)** & **Equation (3)**: Calculates Cosine Similarity between title word feature vectors of isolated vertices and candidates with similar names:
     $$\text{sim}(fv_1, fv_2) = \frac{fv_1 \cdot fv_2}{\|fv_1\| \cdot \|fv_2\|}$$

---

## Evaluation Metrics

Given $N$ total papers, $R$ reference ground-truth clusters, and $q$ predicted clusters:

1. **$K$-Metric (Equation 4)**:
   $$\text{ACP} = \frac{1}{N} \sum_{i=1}^q \sum_{j=1}^R \frac{n_{ij}^2}{n_i}, \quad \text{AAP} = \frac{1}{N} \sum_{j=1}^R \sum_{i=1}^q \frac{n_{ij}^2}{n_j}$$
   $$K = \sqrt{\text{ACP} \cdot \text{AAP}}$$

2. **Pairwise-$F_1$ ($pF1$, Equation 5)**:
   $$\text{PP} = \frac{\sum_{i,j} C(n_{ij}, 2)}{\sum_i C(n_i, 2)}, \quad \text{PR} = \frac{\sum_{i,j} C(n_{ij}, 2)}{\sum_j C(n_j, 2)}$$
   $$pF1 = \frac{2 \cdot \text{PP} \cdot \text{PR}}{\text{PP} + \text{PR}}$$

3. **Cluster-$F_1$ ($cF1$, Equation 6)**:
   $$\text{CP} = \frac{m}{q}, \quad \text{CR} = \frac{m}{R}, \quad cF1 = \frac{2 \cdot \text{CP} \cdot \text{CR}}{\text{CP} + \text{CR}}$$
   where $m$ is the number of exact matching clusters.

---

## Project Directory Structure

```
author-disambiguation-graph/
│
├── data/
│   ├── original/                         # Raw DBLP source files
│   │   ├── DBLP_labeled_data.txt         # 14 core benchmark author groups
│   │   └── DBLP name disambiguation dataset.txt  # 668 expanded author groups
│   └── cleaned/                          # Generated by clean_dataset.py
│       ├── cleaned_dblp_dataset.json     # 10,839 clean JSON records
│       └── cleaned_dblp_dataset.csv      # Tabular CSV format
│
├── gfad/                                 # Core Python package
│   ├── config.py                         # Paths, thresholds, benchmark group definitions
│   ├── data_loader.py                    # Shared cleaned-dataset loader
│   ├── pipeline.py                       # GFADPipeline (GFAD-AD & GFAD-OR orchestration)
│   ├── models/                           # Data models
│   │   ├── citation.py                   # CitationRecord class
│   │   └── graph.py                      # AuthorVertex & GraphModel (GM = {V, E})
│   ├── algorithms/                       # Paper Algorithms (1-6)
│   │   ├── graph_builder.py              # BDC -> GraphModel construction
│   │   ├── cycle_detector.py             # Alg 1 (DetectLongestCycles)
│   │   ├── namesake_splitter.py          # Alg 2 (SplitNamesakes)
│   │   ├── name_similarity.py            # Alg 3 & Eq. 2 (SearchSimilarNames & nameSim)
│   │   ├── same_author_detector.py       # Alg 4 (DetectSameAuthor & checkSharingVertex)
│   │   ├── heteronymous_merger.py        # Alg 5 (MergeHeteronymousNames)
│   │   └── outlier_remover.py            # Alg 6 & Eq. 3 (RemoveOutliers via Title Cosine)
│   └── evaluation/
│       └── metrics.py                    # ACP, AAP, K-metric, PP, PR, pF1, CP, CR, cF1
│
├── experiments/
│   ├── run_benchmark.py                  # Benchmark runner for 14 DBLP groups
│   └── benchmark_results.json            # Saved evaluation results
│
├── tests/                                # Automated unit test suite
│   ├── test_name_similarity.py           # LCS & nameSim tests
│   ├── test_cycle_detection.py           # Algorithm 1 tests
│   └── test_metrics.py                   # Metrics engine tests
│
├── clean_dataset.py                      # Raw data -> cleaned JSON/CSV
├── run_gfad.py                           # Master CLI entry point
└── README.md
```

---

## Installation & Getting Started

### Requirements
Python 3.8 or higher. **Zero external dependencies.**

### Prepare the dataset
The cleaned dataset ships with the repository under `data/cleaned/`. To regenerate it
from the raw files in `data/original/`:

```bash
python clean_dataset.py
```

---

## Command-Line Usage (CLI)

Use `run_gfad.py` for all operations:

### 1. Run Benchmark Evaluation across 14 DBLP Groups
```bash
python run_gfad.py --benchmark
```

### 2. Disambiguate a Specific Ambiguous Group
```bash
python run_gfad.py --group "A. Gupta"
```

### 3. Run Automated Unit Test Suite
```bash
python run_gfad.py --test
```

### 4. Use a Custom Dataset Path
```bash
python run_gfad.py --benchmark --dataset path/to/dataset.json
```

---

## Configuration

All tunables live in [`gfad/config.py`](gfad/config.py):

| Constant | Default | Meaning |
| :--- | :--- | :--- |
| `LCS_SIMILARITY_THRESHOLD` | `0.8` | Minimum tokenized-LCS similarity for heteronym candidates (Eq. 2) |
| `OUTLIER_NAME_SIMILARITY_THRESHOLD` | `0.5` | Relaxed name-similarity threshold for outlier merge candidates (Alg. 6) |
| `SHARED_COAUTHOR_MAX_DEPTH` | `3` | Max BFS hop depth for shared co-author detection (Alg. 4) |
| `CLEANED_DATASET_JSON` | `data/cleaned/...json` | Default dataset location used by the CLI and benchmark |
| `BENCHMARK_GROUP_MAP` | 14 groups | Label-prefix → display-name map for the DBLP benchmark groups |

---

## Benchmark Results Summary

Evaluation across the 14 DBLP Benchmark Author Groups — run `python run_gfad.py --benchmark`
to reproduce; full per-group results are saved to `experiments/benchmark_results.json`.

| Ambiguous Group | GFAD-AD (K, pF1, cF1) | GFAD-OR (K, pF1, cF1) |
| :--- | :--- | :--- |
| **A. Gupta** | K: 1.79 \| pF1: 0.75 \| cF1: 0.07 | K: 1.79 \| pF1: 0.75 \| cF1: 0.07 |
| **J. Lee** | K: 2.05 \| pF1: 0.71 \| cF1: 0.16 | K: 2.06 \| pF1: 0.70 \| cF1: 0.16 |
| **S. Lee** | K: 1.88 \| pF1: 0.69 \| cF1: 0.17 | K: 1.88 \| pF1: 0.69 \| cF1: 0.17 |
| **Y. Chen** | K: 2.45 \| pF1: 0.97 \| cF1: 0.17 | K: 2.45 \| pF1: 0.97 \| cF1: 0.17 |
| **AVERAGE (14 groups)** | **K: 1.85 \| pF1: 0.73 \| cF1: 0.15** | **K: 1.85 \| pF1: 0.73 \| cF1: 0.15** |

---

## Citation

If you use this implementation in your research, please cite the original paper:

```bibtex
@article{shin2014author,
  title={Author name disambiguation using a graph model with node splitting and merging based on bibliographic information},
  author={Shin, Dongwook and Kim, Taehwan and Choi, Joongmin and Kim, Jungsun},
  journal={Scientometrics},
  volume={100},
  number={1},
  pages={15--50},
  year={2014},
  publisher={Springer}
}
```
