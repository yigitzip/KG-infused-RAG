#!/usr/bin/env python3
"""Verify one 3-hop question entry against Neo4j."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from neo4j import GraphDatabase
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency: neo4j. Install with `pip install neo4j`."
    ) from exc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True, help="Path to sample JSON entry file.")
    parser.add_argument("--uri", required=True, help="Neo4j URI, e.g., bolt://localhost:7687")
    parser.add_argument("--user", required=True, help="Neo4j username")
    parser.add_argument("--password", required=True, help="Neo4j password")
    args = parser.parse_args()

    payload = json.loads(Path(args.json).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        if not payload:
            print("JSON list is empty.", file=sys.stderr)
            sys.exit(1)
        entry = payload[0]
    else:
        entry = payload

    cypher = entry.get("verification_cypher", "").strip()
    if not cypher:
        print("Missing verification_cypher in JSON entry.", file=sys.stderr)
        sys.exit(1)

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    with driver.session() as session:
        records = list(session.run(cypher))
    driver.close()

    is_verified = len(records) > 0
    print(f"rows={len(records)}")
    print(f"is_verified={is_verified}")


if __name__ == "__main__":
    main()

