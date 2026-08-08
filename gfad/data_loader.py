"""
Shared loading of the cleaned DBLP dataset into CitationRecord objects.
"""

import json
import os
from typing import List

from gfad.config import CLEANED_DATASET_JSON
from gfad.models.citation import CitationRecord


def load_dataset(json_path: str = CLEANED_DATASET_JSON) -> List[CitationRecord]:
    """
    Loads the cleaned dataset JSON produced by clean_dataset.py.
    Raises FileNotFoundError if the file does not exist; callers decide how to
    surface the error (the CLI exits with a message, library users handle it).
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(
            f"Dataset not found at '{json_path}'. Please run clean_dataset.py first."
        )
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [CitationRecord.from_dict(d) for d in data]
