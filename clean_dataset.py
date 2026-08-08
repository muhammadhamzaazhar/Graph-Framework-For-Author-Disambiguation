"""
Data Cleaning and Merging Script for GFAD (Graph Framework for Author Disambiguation)
Paper: Author name disambiguation using a graph model with node splitting and merging
based on bibliographic information (Shin et al., 2014)

Reads (from data/original/):
  - DBLP_labeled_data.txt (14 DBLP core benchmark author groups)
  - DBLP name disambiguation dataset.txt (668 expanded DBLP author groups)

Generates (into data/cleaned/):
  - cleaned_dblp_dataset.json (Structured JSON format)
  - cleaned_dblp_dataset.csv (Tabular CSV format)
"""

import csv
import html
import json
import os
import re
from typing import List, Optional

from gfad.config import (
    BENCHMARK_GROUP_MAP,
    BENCHMARK_SOURCE_FILE,
    CLEANED_DATA_DIR,
    CLEANED_DATASET_CSV,
    CLEANED_DATASET_JSON,
    EXPANDED_SOURCE_FILE,
)

CSV_FIELDNAMES = [
    "paper_id", "ambiguous_group", "author_name", "coauthors",
    "title", "abstract", "keywords", "venue", "year",
    "ground_truth_label", "source_dataset"
]


def clean_text(text: str) -> str:
    if not text:
        return ""
    # Unescape HTML entities (e.g. &uuml; -> ü, &amp; -> &)
    text = html.unescape(text)
    # Collapse excessive whitespace
    return re.sub(r'\s+', ' ', text).strip()


def clean_coauthors(raw_coauthors: List[str], target_author: str) -> List[str]:
    """Cleans co-author names, title-cases them, and drops the target author."""
    coauthors = []
    for ca in raw_coauthors:
        ca_clean = clean_text(ca)
        if ca_clean and ca_clean.lower() != target_author.lower():
            coauthors.append(ca_clean.title())
    return coauthors


def make_record(
    paper_id: str,
    ambiguous_group: str,
    author_name: str,
    coauthors: List[str],
    title: str,
    ground_truth_label: str,
    source_dataset: str,
    abstract: str = "",
    keywords: Optional[List[str]] = None,
    venue: str = "",
    year: str = ""
) -> dict:
    return {
        "paper_id": paper_id,
        "ambiguous_group": ambiguous_group,
        "author_name": author_name,
        "coauthors": coauthors,
        "title": title,
        "abstract": abstract,
        "keywords": keywords or [],
        "venue": venue,
        "year": year,
        "ground_truth_label": ground_truth_label,
        "source_dataset": source_dataset
    }


def parse_benchmark_dataset(file_path: str) -> List[dict]:
    """
    Parse DBLP_labeled_data.txt (7 tab-separated fields per row).
    Format: author_name \t cluster_label \t paper_id \t coauthors(|) \t year \t venue \t title
    """
    records = []
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found.")
        return records

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line_str = line.strip('\r\n')
            if not line_str:
                continue
            parts = line_str.split('\t')
            if len(parts) < 7:
                continue

            raw_author = clean_text(parts[0])
            cluster_label = clean_text(parts[1])
            group_code = cluster_label.split('-')[0] if '-' in cluster_label else cluster_label
            ambiguous_group = BENCHMARK_GROUP_MAP.get(group_code, group_code.upper())
            paper_id = clean_text(parts[2])

            # Co-authors separated by pipe '|'
            coauthors = clean_coauthors(parts[3].split('|') if parts[3] else [], raw_author)

            records.append(make_record(
                paper_id=f"P2-{paper_id}",
                ambiguous_group=ambiguous_group,
                author_name=raw_author.title(),
                coauthors=coauthors,
                title=clean_text(parts[6]),
                venue=clean_text(parts[5]).title(),
                year=clean_text(parts[4]),
                ground_truth_label=cluster_label,
                source_dataset="DBLP_benchmark_14"
            ))

    print(f"Parsed {len(records)} records from {file_path}")
    return records


def _reassemble_rows(lines: List[str]) -> List[tuple]:
    """
    Reassembles logical (group, row) tuples from the expanded dataset, where a
    record may wrap across physical lines and author-group headers delimit sections.
    """
    parsed_rows = []
    current_group = ""
    buf = ""

    for line in lines:
        line_s = line.strip('\r\n')
        if not line_s:
            continue

        # A new record starts with a digit + tab (e.g. '1\tAbdul Sattar\t...')
        if re.match(r'^\d+\t', line_s):
            if buf:
                parsed_rows.append((current_group, buf))
            buf = line_s
        elif '\t' not in line_s and not line_s[0].isdigit() and not line_s.startswith('Label'):
            # Author group header
            if buf:
                parsed_rows.append((current_group, buf))
                buf = ""
            current_group = clean_text(line_s)
        else:
            # Continuation of the current record
            if buf:
                buf += " " + line_s.strip()

    if buf:
        parsed_rows.append((current_group, buf))

    return parsed_rows


def parse_expanded_dataset(file_path: str) -> List[dict]:
    """
    Parse DBLP name disambiguation dataset.txt.
    9 tab fields: Label \t Name \t Author List \t Title \t Abstract \t Keywords \t Venue \t Download links \t Publish Year
    """
    records = []
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found.")
        return records

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        parsed_rows = _reassemble_rows(f.read().split('\n'))

    rec_id_counter = 1
    for grp, r_str in parsed_rows:
        parts = r_str.split('\t')
        if len(parts) != 9 or not parts[0].isdigit():
            continue

        label_num = parts[0].strip()
        raw_author = clean_text(parts[1])
        ambiguous_group = grp if grp else raw_author.title()

        # Co-authors and keywords separated by semicolon ';'
        coauthors = clean_coauthors(parts[2].split(';') if parts[2] else [], raw_author)
        keywords = [k for k in (clean_text(kw) for kw in parts[5].split(';')) if k] if parts[5] else []

        records.append(make_record(
            paper_id=f"P1-{rec_id_counter}",
            ambiguous_group=ambiguous_group,
            author_name=raw_author.title(),
            coauthors=coauthors,
            title=clean_text(parts[3]),
            abstract=clean_text(parts[4]),
            keywords=keywords,
            venue=clean_text(parts[6]),
            year=clean_text(parts[8]),
            ground_truth_label=f"{ambiguous_group.replace(' ', '_')}-{label_num}",
            source_dataset="DBLP_expanded_668"
        ))
        rec_id_counter += 1

    print(f"Parsed {len(records)} records from {file_path}")
    return records


def deduplicate_records(records: List[dict]) -> List[dict]:
    """
    Deduplicate records based on (ambiguous_group, title_lower, year).
    The first occurrence wins; later duplicates only enrich missing abstract/keywords.
    """
    seen = {}
    deduped = []

    for r in records:
        key = (r["ambiguous_group"].lower(), r["title"].lower(), r["year"])
        if key not in seen:
            seen[key] = len(deduped)
            deduped.append(r)
        else:
            existing_rec = deduped[seen[key]]
            # Enrich abstract/keywords if missing
            if not existing_rec["abstract"] and r["abstract"]:
                existing_rec["abstract"] = r["abstract"]
            if not existing_rec["keywords"] and r["keywords"]:
                existing_rec["keywords"] = r["keywords"]

    print(f"Total records after deduplication: {len(deduped)} (removed {len(records) - len(deduped)} duplicates)")
    return deduped


def save_json(records: List[dict], file_path: str):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    print(f"Saved JSON dataset to {file_path}")


def save_csv(records: List[dict], file_path: str):
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        for r in records:
            row = dict(r)
            row["coauthors"] = "; ".join(r["coauthors"])
            row["keywords"] = "; ".join(r["keywords"])
            writer.writerow(row)
    print(f"Saved CSV dataset to {file_path}")


def print_group_summary(records: List[dict]):
    benchmark_counts = {}
    for r in records:
        grp = r["ambiguous_group"]
        benchmark_counts[grp] = benchmark_counts.get(grp, 0) + 1

    print("\n--- Benchmark 14 Ambiguous Groups Summary ---")
    for grp in sorted(BENCHMARK_GROUP_MAP.values()):
        print(f"  {grp:15s}: {benchmark_counts.get(grp, 0)} records")


def main():
    benchmark_records = parse_benchmark_dataset(BENCHMARK_SOURCE_FILE)
    expanded_records = parse_expanded_dataset(EXPANDED_SOURCE_FILE)

    combined = benchmark_records + expanded_records
    print(f"Combined total raw records: {len(combined)}")

    cleaned = deduplicate_records(combined)
    print_group_summary(cleaned)

    os.makedirs(CLEANED_DATA_DIR, exist_ok=True)
    save_json(cleaned, CLEANED_DATASET_JSON)
    save_csv(cleaned, CLEANED_DATASET_CSV)


if __name__ == '__main__':
    main()
