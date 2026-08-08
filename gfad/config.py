"""
Central configuration for the GFAD framework: file locations, algorithm
thresholds, and the 14 DBLP benchmark author groups (Shin et al., 2014).
"""

# --- Data locations (relative to the project root; forward slashes work on all platforms) ---
ORIGINAL_DATA_DIR = "data/original"
CLEANED_DATA_DIR = "data/cleaned"

BENCHMARK_SOURCE_FILE = f"{ORIGINAL_DATA_DIR}/DBLP_labeled_data.txt"
EXPANDED_SOURCE_FILE = f"{ORIGINAL_DATA_DIR}/DBLP name disambiguation dataset.txt"

CLEANED_DATASET_JSON = f"{CLEANED_DATA_DIR}/cleaned_dblp_dataset.json"
CLEANED_DATASET_CSV = f"{CLEANED_DATA_DIR}/cleaned_dblp_dataset.csv"

BENCHMARK_RESULTS_FILE = "experiments/benchmark_results.json"

# --- Algorithm thresholds (paper defaults) ---
# Minimum tokenized-LCS name similarity for two names to be heteronym candidates (Eq. 2).
LCS_SIMILARITY_THRESHOLD = 0.8
# Relaxed name-similarity threshold used when searching merge candidates for outliers (Alg. 6).
OUTLIER_NAME_SIMILARITY_THRESHOLD = 0.5
# Maximum BFS hop depth when checking whether two vertices share a co-author (Alg. 4).
SHARED_COAUTHOR_MAX_DEPTH = 3

# --- The 14 core DBLP benchmark groups: file label prefix -> display name ---
BENCHMARK_GROUP_MAP = {
    'agupta': 'A. Gupta',
    'akumar': 'A. Kumar',
    'cchen': 'C. Chen',
    'djohnson': 'D. Johnson',
    'jlee': 'J. Lee',
    'jmartin': 'J. Martin',
    'jrobinson': 'J. Robinson',
    'jsmith': 'J. Smith',
    'ktanaka': 'K. Tanaka',
    'mbrown': 'M. Brown',
    'mjones': 'M. Jones',
    'mmiller': 'M. Miller',
    'slee': 'S. Lee',
    'ychen': 'Y. Chen'
}

BENCHMARK_GROUPS = sorted(BENCHMARK_GROUP_MAP.values())
