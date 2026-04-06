#!/usr/bin/env python3
"""Verify reasoning_path strings in JSON against wikidata5m_all_triplet.txt."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def parse_path_string(path_str: str) -> list[tuple[str, str, str]]:
    tokens = re.findall(r"(Q\d+|P\d+)", path_str)
    if len(tokens) < 3 or len(tokens) % 2 == 0:
        raise ValueError(f"Cannot parse path: {path_str!r}")
    triples = []
    for i in range(0, len(tokens) - 2, 2):
        triples.append((tokens[i], tokens[i + 1], tokens[i + 2]))
    return triples


def collect_needed_triples(items: list) -> set[tuple[str, str, str]]:
    needed: set[tuple[str, str, str]] = set()
    for item in items:
        raw = item.get("reasoning_path") or ""
        try:
            for tr in parse_path_string(raw):
                needed.add(tr)
        except ValueError:
            continue
    return needed


def filter_file_for_triples(path: str, needed: set[tuple[str, str, str]]) -> set[tuple[str, str, str]]:
    found: set[tuple[str, str, str]] = set()
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            tr = (parts[0], parts[1], parts[2])
            if tr in needed:
                found.add(tr)
    return found


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--triplets", required=True)
    ap.add_argument("--json", required=True)
    args = ap.parse_args()

    data = json.loads(Path(args.json).read_text(encoding="utf-8"))
    needed = collect_needed_triples(data)
    print(f"Scanning for {len(needed)} distinct edges …", file=sys.stderr)
    found = filter_file_for_triples(args.triplets, needed)
    print(f"Matched {len(found)} / {len(needed)}", file=sys.stderr)

    ok, bad = 0, []
    for item in data:
        qid = item["question_id"]
        raw = item.get("reasoning_path") or ""
        try:
            steps = parse_path_string(raw)
        except ValueError as e:
            bad.append((qid, str(e)))
            continue
        missing = [tr for tr in steps if tr not in found]
        if missing:
            bad.append((qid, f"missing {missing}"))
        else:
            ok += 1

    print(f"Verified: {ok} / {len(data)}")
    if bad:
        for qid, msg in bad[:25]:
            print(f"  {qid}: {msg}", file=sys.stderr)
        sys.exit(1)
    print("All paths verified.")


if __name__ == "__main__":
    main()
