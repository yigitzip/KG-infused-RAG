#!/usr/bin/env python3
"""
Türkiye proje slaytlarına uygun triplet alt kümesi (Q43 + keyword + alan P-id).
Çıktı TSV → wikidata5m_triplets_to_neo4j_csv.py ile CSV.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REL_TO_DOMAIN: dict[str, str] = {
    "P54": "turkish_football",
    "P286": "turkish_football",
    "P115": "turkish_football",
    "P641": "turkish_football",
    "P118": "turkish_football",
    "P3450": "turkish_football",
    "P2094": "turkish_football",
    "P1344": "turkish_football",
    "P710": "turkish_football",
    "P57": "turkish_cinema",
    "P162": "turkish_cinema",
    "P161": "turkish_cinema",
    "P166": "turkish_cinema",
    "P136": "turkish_cinema",
    "P495": "turkish_cinema",
    "P58": "turkish_cinema",
    "P272": "turkish_cinema",
    "P86": "turkish_cinema",
    "P1040": "turkish_cinema",
    "P364": "turkish_cinema",
    "P840": "turkish_cinema",
    "P915": "turkish_cinema",
    "P112": "turkish_companies",
    "P159": "turkish_companies",
    "P749": "turkish_companies",
    "P355": "turkish_companies",
    "P127": "turkish_companies",
    "P169": "turkish_companies",
    "P452": "turkish_companies",
    "P175": "turkish_music",
    "P264": "turkish_music",
    "P1303": "turkish_music",
    "P527": "turkish_music",
    "P361": "turkish_music",
    "P437": "turkish_music",
    "P676": "turkish_music",
    "P69": "turkish_academia",
    "P108": "turkish_academia",
    "P101": "turkish_academia",
    "P463": "turkish_academia",
    "P512": "turkish_academia",
    "P184": "turkish_academia",
    "P185": "turkish_academia",
    "P17": "geo_turkey_context",
    "P27": "geo_turkey_context",
    "P19": "geo_turkey_context",
    "P20": "geo_turkey_context",
    "P131": "geo_turkey_context",
    "P150": "geo_turkey_context",
    "P36": "geo_turkey_context",
    "P6": "geo_turkey_context",
    "P47": "geo_turkey_context",
    "P530": "geo_turkey_context",
    "P31": "typing",
    "P279": "typing",
    "P106": "typing",
}

DOMAIN_RELS = frozenset(REL_TO_DOMAIN.keys())
CITY_QIDS = {
    "Q406": "Istanbul",
    "Q3640": "Ankara",
    "Q35997": "Izmir",
    "Q79846": "Bursa",
    "Q12901": "Antalya",
    "Q48338": "Adana",
}
KEYWORDS = (
    "turkey",
    "türkiye",
    "turkiye",
    "turkish republic",
    "republic of turkey",
)


def line_matches_keyword(line: str) -> bool:
    z = line.lower()
    return any(k in z for k in KEYWORDS)


def scan_text_entities(text_path: str, chunk: int = 2_000_000) -> set[str]:
    found: set[str] = set()
    n = 0
    with open(text_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            n += 1
            if n % chunk == 0:
                print(f"  text lines {n:,}  hits {len(found):,}", file=sys.stderr)
            tab = line.find("\t")
            if tab == -1:
                continue
            eid, desc = line[:tab], line[tab + 1 :]
            if eid.startswith("Q") and line_matches_keyword(desc):
                found.add(eid)
    return found


def scan_entity_alias_file(alias_path: str, chunk: int = 1_000_000) -> set[str]:
    found: set[str] = set()
    n = 0
    with open(alias_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            n += 1
            if n % chunk == 0:
                print(f"  alias lines {n:,}  hits {len(found):,}", file=sys.stderr)
            if line_matches_keyword(line):
                tab = line.find("\t")
                if tab != -1:
                    eid = line[:tab]
                    if eid.startswith("Q"):
                        found.add(eid)
    return found


def collect_q43_endpoints(triplet_path: str, turkey_id: str, chunk: int = 5_000_000) -> set[str]:
    s = {turkey_id}
    n = 0
    with open(triplet_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            n += 1
            if n % chunk == 0:
                print(f"  Q43 scan lines {n:,}", file=sys.stderr)
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            h, _, t = parts
            if h == turkey_id:
                s.add(t)
            elif t == turkey_id:
                s.add(h)
    return s


def expand_undirected(triplet_path: str, nodes: set[str], chunk: int = 5_000_000) -> set[str]:
    out = set(nodes)
    n = 0
    with open(triplet_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            n += 1
            if n % chunk == 0:
                print(f"  expand scan {n:,}", file=sys.stderr)
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            h, _, t = parts
            if h in nodes or t in nodes:
                out.add(h)
                out.add(t)
    return out


def write_filtered_triplets(
    triplet_path: str, entities: set[str], turkey_id: str, out_path: str, chunk: int = 5_000_000
) -> tuple[int, Counter[str], Counter[str], dict[str, set[str]]]:
    rel_ctr: Counter[str] = Counter()
    domain_ctr: Counter[str] = Counter()
    city_entities: dict[str, set[str]] = {q: set() for q in CITY_QIDS}
    kept = 0
    total = 0
    with open(triplet_path, "r", encoding="utf-8", errors="replace") as fin, open(
        out_path, "w", encoding="utf-8", newline=""
    ) as fout:
        for line in fin:
            total += 1
            if total % chunk == 0:
                print(f"  filter lines {total:,}  kept {kept:,}", file=sys.stderr)
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            h, r, t = parts
            touches_turkey = h == turkey_id or t == turkey_id
            domain_internal = h in entities and t in entities and r in DOMAIN_RELS
            if not (touches_turkey or domain_internal):
                continue
            fout.write(f"{h}\t{r}\t{t}\n")
            kept += 1
            rel_ctr[r] += 1
            domain_ctr[REL_TO_DOMAIN.get(r, "other_included")] += 1
            if r == "P131" and t in city_entities:
                city_entities[t].add(h)
            if r in ("P17", "P131", "P159", "P276") and t in city_entities:
                city_entities[t].add(h)
    return total, rel_ctr, domain_ctr, city_entities


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--triplets", required=True)
    ap.add_argument("--text", required=True)
    ap.add_argument("--entity-alias", required=True)
    ap.add_argument("--out-tsv", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--turkey-id", default="Q43")
    ap.add_argument("--expand-hops", type=int, default=1)
    args = ap.parse_args()

    turkey = args.turkey_id
    print("1) Keyword scan (text) …", file=sys.stderr)
    from_text = scan_text_entities(args.text)
    print("2) Keyword scan (alias) …", file=sys.stderr)
    from_alias = scan_entity_alias_file(args.entity_alias)
    print("3) Q43 endpoints …", file=sys.stderr)
    q43_endpoints = collect_q43_endpoints(args.triplets, turkey)
    entities: set[str] = {turkey} | from_text | from_alias | q43_endpoints
    if args.expand_hops > 0:
        for i in range(args.expand_hops):
            print(f"4) Expand hop {i + 1} …", file=sys.stderr)
            entities = expand_undirected(args.triplets, entities)
            print(f"   |entities|={len(entities):,}", file=sys.stderr)

    print("5) Write triples …", file=sys.stderr)
    total_lines, rel_ctr, domain_ctr, city_entities = write_filtered_triplets(
        args.triplets, entities, turkey, args.out_tsv
    )
    city_counts = {CITY_QIDS[q]: len(s) for q, s in city_entities.items()}
    report = {
        "turkey_entity_id": turkey,
        "keywords": list(KEYWORDS),
        "entity_set_size": len(entities),
        "triplet_file_lines_read": total_lines,
        "triplets_written": sum(rel_ctr.values()),
        "relation_counts": dict(rel_ctr.most_common()),
        "domain_relation_group_counts": dict(domain_ctr.most_common()),
        "city_linked_entity_counts": city_counts,
    }
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Done → {args.out_tsv}  report → {args.report}", file=sys.stderr)


if __name__ == "__main__":
    main()
