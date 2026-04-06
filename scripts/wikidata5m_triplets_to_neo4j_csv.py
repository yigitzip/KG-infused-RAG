#!/usr/bin/env python3
"""
Convert Wikidata5M triplet TSV into CSV files for `neo4j-admin database import`.

Input: head_id \\t property_id \\t tail_id
Outputs: entities.csv, relationships.csv (UTF-8)

Usage:
  python3 scripts/wikidata5m_triplets_to_neo4j_csv.py \\
    --triplets PATH \\
    --text PATH \\
    --out-dir DIR

Requires: Unix `sort` for entity-id pipeline.
"""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
import tempfile


def sanitize_node_name(desc: str, max_len: int) -> str:
    if not desc:
        return ""
    s = desc.replace("\r\n", "\n").replace("\r", "\n")
    s = " ".join(s.split())
    return s[:max_len]


def write_relationships_and_entity_ids(
    triplet_path: str, rel_csv_path: str, ids_temp_path: str, chunk_lines: int = 5_000_000
) -> int:
    n = 0
    with open(triplet_path, "r", encoding="utf-8", errors="replace") as fin, open(
        rel_csv_path, "w", encoding="utf-8", newline=""
    ) as fout, open(ids_temp_path, "w", encoding="utf-8") as fid:
        fout.write(":START_ID(Entity),:END_ID(Entity),:TYPE\n")
        for line in fin:
            n += 1
            if n % chunk_lines == 0:
                print(f"  triplets processed: {n:,}", file=sys.stderr)
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            h, r, t = parts
            if not h or not r or not t:
                continue
            fout.write(f"{h},{t},{r}\n")
            fid.write(h + "\n" + t + "\n")
    return n


def sort_unique_ids(ids_path: str, sorted_ids_path: str) -> None:
    subprocess.run(["sort", "-u", "-o", sorted_ids_path, ids_path], check=True)


def merge_sorted_ids_with_text(
    sorted_ids_path: str, sorted_text_path: str, nodes_csv_path: str
) -> None:
    max_desc = 512

    def read_id_line(f) -> str | None:
        line = f.readline()
        if not line:
            return None
        return line.rstrip("\n")

    def read_text_record(f) -> tuple[str | None, str | None]:
        line = f.readline()
        if not line:
            return None, None
        line = line.rstrip("\n")
        tab = line.find("\t")
        if tab == -1:
            return line, ""
        eid, desc = line[:tab], line[tab + 1 :]
        return eid, desc

    with open(sorted_ids_path, "r", encoding="utf-8", errors="replace") as f_ids, open(
        sorted_text_path, "r", encoding="utf-8", errors="replace"
    ) as f_txt, open(nodes_csv_path, "w", encoding="utf-8", newline="") as fout:
        fout.write("entityId:ID(Entity),name,:LABEL\n")
        row_writer = csv.writer(
            fout,
            quoting=csv.QUOTE_MINIMAL,
            doublequote=True,
            escapechar=None,
            lineterminator="\n",
        )
        cur_id = read_id_line(f_ids)
        txt_id, txt_desc = read_text_record(f_txt)
        while cur_id is not None:
            while txt_id is not None and txt_id < cur_id:
                txt_id, txt_desc = read_text_record(f_txt)
            if txt_id == cur_id and txt_desc is not None:
                row_writer.writerow([cur_id, sanitize_node_name(txt_desc, max_desc), "Entity"])
            else:
                row_writer.writerow([cur_id, "", "Entity"])
            cur_id = read_id_line(f_ids)


def sort_text_file(text_path: str, sorted_text_path: str) -> None:
    subprocess.run(
        ["sort", "-t", "\t", "-k1,1", "-o", sorted_text_path, text_path],
        check=True,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--triplets", required=True)
    ap.add_argument("--text", help="wikidata5m_text.txt")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--skip-text", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    rel_path = os.path.join(args.out_dir, "relationships.csv")
    nodes_path = os.path.join(args.out_dir, "entities.csv")

    tmpdir = tempfile.mkdtemp(prefix="wikidata5m_neo4j_")
    ids_raw = os.path.join(tmpdir, "ids_raw.txt")
    ids_sorted = os.path.join(tmpdir, "ids_sorted.txt")
    text_sorted = os.path.join(tmpdir, "text_sorted.txt")

    try:
        print("Pass 1: relationships + entity id collection …", file=sys.stderr)
        n = write_relationships_and_entity_ids(args.triplets, rel_path, ids_raw)
        print(f"Done. {n:,} lines read from triplets.", file=sys.stderr)

        print("Sorting unique entity IDs …", file=sys.stderr)
        sort_unique_ids(ids_raw, ids_sorted)

        if args.skip_text or not args.text:
            print("Writing nodes without text labels …", file=sys.stderr)
            with open(ids_sorted, "r", encoding="utf-8", errors="replace") as fin, open(
                nodes_path, "w", encoding="utf-8", newline=""
            ) as fout:
                fout.write("entityId:ID(Entity),name,:LABEL\n")
                for line in fin:
                    eid = line.rstrip("\n")
                    if eid:
                        fout.write(f"{eid},,Entity\n")
        else:
            print("Sorting text file by entity id …", file=sys.stderr)
            sort_text_file(args.text, text_sorted)
            print("Merging ids with text …", file=sys.stderr)
            merge_sorted_ids_with_text(ids_sorted, text_sorted, nodes_path)

        print(f"Wrote:\n  {nodes_path}\n  {rel_path}", file=sys.stderr)
    finally:
        for p in (ids_raw, ids_sorted, text_sorted):
            if os.path.isfile(p):
                os.remove(p)
        os.rmdir(tmpdir)


if __name__ == "__main__":
    main()
