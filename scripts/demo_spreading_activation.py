#!/usr/bin/env python3
"""Terminal demo for Module 1 spreading activation retrieval."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from kg_infused_rag.module1_spreading_activation import SpreadingActivationRetriever
from kg_infused_rag.neo4j_gateway import Neo4jClient
from kg_infused_rag.relation_mapper import load_relation_map, relation_name
from kg_infused_rag.simple_selector import HeuristicLLMSelector


def guess_keyword(question: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", question)
    long_words = [w for w in words if len(w) >= 5]
    return long_words[0] if long_words else words[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", required=True)
    parser.add_argument("--seed-qid", help="Optional seed QID (e.g., Q495299).")
    parser.add_argument("--uri", default="bolt://localhost:7687")
    parser.add_argument("--user", default="neo4j")
    parser.add_argument("--password", required=True)
    parser.add_argument("--relation-map", required=True)
    parser.add_argument("--max-hops", type=int, default=3)
    parser.add_argument("--branch-factor", type=int, default=4)
    parser.add_argument("--candidate-limit", type=int, default=60)
    args = parser.parse_args()

    relation_map = load_relation_map(args.relation_map)
    neo4j_client = Neo4jClient(args.uri, args.user, args.password)
    llm_selector = HeuristicLLMSelector()

    try:
        seed_qids: list[str]
        if args.seed_qid:
            seed_qids = [args.seed_qid]
        else:
            keyword = guess_keyword(args.question)
            matches = neo4j_client.search_entities(keyword, limit=5)
            if not matches:
                raise SystemExit("No seed entity found. Please pass --seed-qid explicitly.")
            seed_qids = [matches[0][0]]
            print(f"[seed-search] keyword='{keyword}' -> {matches[0][0]} | {matches[0][1]}")

        retriever = SpreadingActivationRetriever(
            neo4j_client=neo4j_client,
            llm_client=llm_selector,
            relation_map=relation_map,
            max_hops=args.max_hops,
            branch_factor=args.branch_factor,
            candidate_limit=args.candidate_limit,
        )

        selected = retriever.run(args.question, seed_qids)
        print(f"\nQuestion: {args.question}")
        print(f"Seeds: {seed_qids}")
        print(f"Selected triples: {len(selected)}")
        for idx, triple in enumerate(selected, 1):
            h = triple.head_name or triple.head_qid
            t = triple.tail_name or triple.tail_qid
            rel = relation_name(triple.relation, relation_map)
            print(f"{idx:02d}. {h} -[{triple.relation} | {rel}]-> {t}")
    finally:
        neo4j_client.close()


if __name__ == "__main__":
    main()

