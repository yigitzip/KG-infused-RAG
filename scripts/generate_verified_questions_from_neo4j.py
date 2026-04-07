#!/usr/bin/env python3
"""Generate verified Türkiye-focused multi-hop QA dataset from Neo4j."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

try:
    from neo4j import GraphDatabase
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: neo4j. Install with `pip install neo4j`.") from exc


REL_TO_DOMAIN: dict[str, str] = {
    "P54": "football",
    "P286": "football",
    "P115": "football",
    "P57": "cinema",
    "P161": "cinema",
    "P495": "cinema",
    "P166": "cinema",
    "P112": "company",
    "P159": "company",
    "P749": "company",
    "P355": "company",
    "P175": "music",
    "P264": "music",
    "P136": "music",
    "P69": "academia",
    "P108": "academia",
    "P101": "academia",
    "P17": "geo",
    "P27": "geo",
    "P19": "geo",
    "P131": "geo",
}

TURKEY_ANCHOR_RELATIONS = ("P17", "P27", "P131", "P495", "P159", "P19")
ALLOWED_RELATIONS = {
    "P54",   # member of sports team
    "P286",  # head coach
    "P115",  # home venue
    "P57",   # director
    "P161",  # cast member
    "P166",  # award received
    "P495",  # country of origin
    "P175",  # performer
    "P264",  # record label
    "P136",  # genre
    "P17",   # country
    "P27",   # country of citizenship
    "P19",   # place of birth
    "P131",  # located in administrative territorial entity
}
FIRST_HOP_RELATIONS = {
    "P54",
    "P57",
    "P161",
    "P495",
    "P112",
    "P159",
    "P175",
    "P69",
    "P108",
    "P17",
    "P27",
    "P19",
    "P131",
}
DOMAIN_START_RELATIONS = {"P54", "P57", "P161", "P112", "P175", "P69", "P108", "P159", "P495"}
DOMAIN_RELATIONS: dict[str, set[str]] = {
    "cinema": {"P57", "P161", "P495", "P166"},
    "football": {"P54", "P286", "P115"},
    "music": {"P175", "P264", "P136"},
}


@dataclass
class QuestionItem:
    question_id: str
    question_text: str
    reasoning_path: str
    gold_answer: str
    difficulty: str
    domain: str
    verification_cypher: str
    is_verified: bool


def load_relation_map(path: str | Path | None) -> Dict[str, str]:
    if path is None:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    out: Dict[str, str] = {}
    for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = [x.strip() for x in line.split("\t") if x.strip()]
        if len(parts) < 2:
            parts = line.split()
        pcode_idx = next(
            (
                i
                for i, token in enumerate(parts)
                if token.startswith("P") and token[1:].isdigit()
            ),
            None,
        )
        if pcode_idx is None or pcode_idx + 1 >= len(parts):
            continue
        code = parts[pcode_idx]
        label = parts[pcode_idx + 1] if "\t" in line else " ".join(parts[pcode_idx + 1 :])
        out[code] = label
    return out


def rel_name(pcode: str, relation_map: Dict[str, str]) -> str:
    return relation_map.get(pcode, pcode)


def clean_name(name: str | None, fallback: str) -> str:
    value = (name or "").strip()
    if not value:
        return fallback
    value = re.sub(r"\s+", " ", value)
    value = re.split(r"[.(,:;]| is | was | are ", value, maxsplit=1)[0].strip()
    if len(value) < 3:
        return fallback
    return value[:70]


def infer_domain(*relations: str) -> str:
    for rel in relations:
        if rel in REL_TO_DOMAIN:
            return REL_TO_DOMAIN[rel]
    return "mixed"


def get_turkiye_seeds(
    session,
    turkey_qid: str,
    max_seeds: int,
    start_rels: set[str] | None = None,
) -> List[str]:
    query = """
    MATCH (e:Entity)-[r]->(t:Entity {entityId: $turkey_qid})
    WHERE type(r) IN $anchor_rels
      AND e.entityId IS NOT NULL
      AND e.entityId <> $turkey_qid
      AND EXISTS {
        MATCH (e)-[r0]->(:Entity)
        WHERE type(r0) IN $start_rels
      }
    WITH DISTINCT e
    OPTIONAL MATCH (e)-[r2]->(:Entity)
    WHERE type(r2) STARTS WITH 'P'
    WITH e, count(r2) AS out_deg
    ORDER BY out_deg DESC
    RETURN e.entityId AS qid
    LIMIT $max_seeds
    """
    rows = session.run(
        query,
        turkey_qid=turkey_qid,
        max_seeds=max_seeds,
        anchor_rels=list(TURKEY_ANCHOR_RELATIONS),
        start_rels=list(start_rels or DOMAIN_START_RELATIONS),
    )
    return [r["qid"] for r in rows if r.get("qid")]


def has_turkey_anchor(session, qid: str, turkey_qid: str) -> bool:
    query = """
    MATCH (e:Entity {entityId:$qid})-[r]->(t:Entity {entityId:$turkey_qid})
    WHERE type(r) IN $anchor_rels
    RETURN count(*) AS c
    """
    c = session.run(
        query,
        qid=qid,
        turkey_qid=turkey_qid,
        anchor_rels=list(TURKEY_ANCHOR_RELATIONS),
    ).single()["c"]
    return int(c) > 0


def generate_2hop_items(
    session,
    seeds: Iterable[str],
    relation_map: Dict[str, str],
    limit: int,
    turkey_qid: str,
    first_hop_rels: set[str] | None = None,
) -> List[QuestionItem]:
    items: List[QuestionItem] = []
    seen: Set[Tuple[str, str, str, str, str]] = set()
    for seed in seeds:
        if len(items) >= limit:
            break
        if not has_turkey_anchor(session, seed, turkey_qid):
            continue
        query = """
        MATCH (a:Entity {entityId:$seed})-[r1]->(b:Entity)-[r2]->(c:Entity)
        WHERE a.entityId <> b.entityId
          AND b.entityId <> c.entityId
          AND type(r1) IN $first_hop_rels
          AND type(r2) IN $allowed_rels
          AND (
              a.entityId = $turkey_qid OR b.entityId = $turkey_qid OR c.entityId = $turkey_qid
              OR EXISTS {
                  MATCH (a)-[ta]->(:Entity {entityId:$turkey_qid})
                  WHERE type(ta) IN $anchor_rels
              }
              OR EXISTS {
                  MATCH (b)-[tb]->(:Entity {entityId:$turkey_qid})
                  WHERE type(tb) IN $anchor_rels
              }
              OR EXISTS {
                  MATCH (c)-[tc]->(:Entity {entityId:$turkey_qid})
                  WHERE type(tc) IN $anchor_rels
              }
          )
        RETURN a.entityId AS a_id, a.name AS a_name,
               type(r1) AS r1,
               b.entityId AS b_id, b.name AS b_name,
               type(r2) AS r2,
               c.entityId AS c_id, c.name AS c_name
        LIMIT 80
        """
        for row in session.run(
            query,
            seed=seed,
            first_hop_rels=list(first_hop_rels or FIRST_HOP_RELATIONS),
            allowed_rels=list(ALLOWED_RELATIONS),
            turkey_qid=turkey_qid,
            anchor_rels=list(TURKEY_ANCHOR_RELATIONS),
        ):
            if len(items) >= limit:
                break
            key = (row["a_id"], row["r1"], row["b_id"], row["r2"], row["c_id"])
            if key in seen:
                continue
            seen.add(key)

            a_name = clean_name(row["a_name"], row["a_id"])
            c_name = clean_name(row["c_name"], row["c_id"])
            r1 = row["r1"]
            r2 = row["r2"]
            question = (
                f"What is the {rel_name(r2, relation_map)} of the "
                f"{rel_name(r1, relation_map)} of {a_name}?"
            )
            verify = (
                f"MATCH (a:Entity {{entityId:'{row['a_id']}'}})-[:{r1}]->"
                f"(b:Entity {{entityId:'{row['b_id']}'}})-[:{r2}]->"
                f"(c:Entity {{entityId:'{row['c_id']}'}}) "
                "RETURN a.name AS a, b.name AS b, c.name AS c LIMIT 1"
            )
            item = QuestionItem(
                question_id=f"TR_2H_{len(items)+1:03d}",
                question_text=question,
                reasoning_path=(
                    f"{row['a_id']} -> {r1} -> {row['b_id']} -> {r2} -> {row['c_id']}"
                ),
                gold_answer=f"{c_name} ({row['c_id']})",
                difficulty="2-hop",
                domain=infer_domain(r1, r2),
                verification_cypher=verify,
                is_verified=True,
            )
            items.append(item)
    return items


def generate_3hop_items(
    session,
    seeds: Iterable[str],
    relation_map: Dict[str, str],
    limit: int,
    turkey_qid: str,
    first_hop_rels: set[str] | None = None,
) -> List[QuestionItem]:
    items: List[QuestionItem] = []
    seen: Set[Tuple[str, str, str, str, str, str, str]] = set()
    for seed in seeds:
        if len(items) >= limit:
            break
        if not has_turkey_anchor(session, seed, turkey_qid):
            continue
        query = """
        MATCH (a:Entity {entityId:$seed})-[r1]->(b:Entity)-[r2]->(c:Entity)-[r3]->(d:Entity)
        WHERE a.entityId <> b.entityId
          AND b.entityId <> c.entityId
          AND c.entityId <> d.entityId
          AND type(r1) IN $first_hop_rels
          AND type(r2) IN $allowed_rels
          AND type(r3) IN $allowed_rels
          AND (
              a.entityId = $turkey_qid OR b.entityId = $turkey_qid OR c.entityId = $turkey_qid OR d.entityId = $turkey_qid
              OR EXISTS {
                  MATCH (a)-[ta]->(:Entity {entityId:$turkey_qid})
                  WHERE type(ta) IN $anchor_rels
              }
              OR EXISTS {
                  MATCH (b)-[tb]->(:Entity {entityId:$turkey_qid})
                  WHERE type(tb) IN $anchor_rels
              }
              OR EXISTS {
                  MATCH (c)-[tc]->(:Entity {entityId:$turkey_qid})
                  WHERE type(tc) IN $anchor_rels
              }
              OR EXISTS {
                  MATCH (d)-[td]->(:Entity {entityId:$turkey_qid})
                  WHERE type(td) IN $anchor_rels
              }
          )
        RETURN a.entityId AS a_id, a.name AS a_name,
               type(r1) AS r1,
               b.entityId AS b_id, b.name AS b_name,
               type(r2) AS r2,
               c.entityId AS c_id, c.name AS c_name,
               type(r3) AS r3,
               d.entityId AS d_id, d.name AS d_name
        LIMIT 120
        """
        for row in session.run(
            query,
            seed=seed,
            first_hop_rels=list(first_hop_rels or FIRST_HOP_RELATIONS),
            allowed_rels=list(ALLOWED_RELATIONS),
            turkey_qid=turkey_qid,
            anchor_rels=list(TURKEY_ANCHOR_RELATIONS),
        ):
            if len(items) >= limit:
                break
            key = (
                row["a_id"],
                row["r1"],
                row["b_id"],
                row["r2"],
                row["c_id"],
                row["r3"],
                row["d_id"],
            )
            if key in seen:
                continue
            seen.add(key)

            a_name = clean_name(row["a_name"], row["a_id"])
            d_name = clean_name(row["d_name"], row["d_id"])
            r1 = row["r1"]
            r2 = row["r2"]
            r3 = row["r3"]
            question = (
                f"What is the {rel_name(r3, relation_map)} of the "
                f"{rel_name(r2, relation_map)} of the "
                f"{rel_name(r1, relation_map)} of {a_name}?"
            )
            verify = (
                f"MATCH (a:Entity {{entityId:'{row['a_id']}'}})-[:{r1}]->"
                f"(b:Entity {{entityId:'{row['b_id']}'}})-[:{r2}]->"
                f"(c:Entity {{entityId:'{row['c_id']}'}})-[:{r3}]->"
                f"(d:Entity {{entityId:'{row['d_id']}'}}) "
                "RETURN a.name AS a, b.name AS b, c.name AS c, d.name AS d LIMIT 1"
            )
            item = QuestionItem(
                question_id=f"TR_3H_{len(items)+1:03d}",
                question_text=question,
                reasoning_path=(
                    f"{row['a_id']} -> {r1} -> {row['b_id']} -> "
                    f"{r2} -> {row['c_id']} -> {r3} -> {row['d_id']}"
                ),
                gold_answer=f"{d_name} ({row['d_id']})",
                difficulty="3-hop",
                domain=infer_domain(r1, r2, r3),
                verification_cypher=verify,
                is_verified=True,
            )
            items.append(item)
    return items


def generate_comparison_items(
    session,
    seeds: Iterable[str],
    relation_map: Dict[str, str],
    limit: int,
    turkey_qid: str,
    allowed_rels: set[str] | None = None,
) -> List[QuestionItem]:
    items: List[QuestionItem] = []
    seen: Set[Tuple[str, str, str, str]] = set()
    for seed in seeds:
        if len(items) >= limit:
            break
        if not has_turkey_anchor(session, seed, turkey_qid):
            continue
        query = """
        MATCH (a:Entity {entityId:$seed})-[r]->(z:Entity)<-[r2]-(x:Entity)
        WHERE a.entityId < x.entityId
          AND type(r) = type(r2)
          AND type(r) IN $allowed_rels
          AND (
              a.entityId = $turkey_qid OR x.entityId = $turkey_qid OR z.entityId = $turkey_qid
              OR EXISTS {
                  MATCH (a)-[ta]->(:Entity {entityId:$turkey_qid})
                  WHERE type(ta) IN $anchor_rels
              }
              OR EXISTS {
                  MATCH (x)-[tx]->(:Entity {entityId:$turkey_qid})
                  WHERE type(tx) IN $anchor_rels
              }
              OR EXISTS {
                  MATCH (z)-[tz]->(:Entity {entityId:$turkey_qid})
                  WHERE type(tz) IN $anchor_rels
              }
          )
        RETURN a.entityId AS a_id, a.name AS a_name,
               x.entityId AS x_id, x.name AS x_name,
               z.entityId AS z_id, z.name AS z_name,
               type(r) AS rel
        LIMIT 100
        """
        for row in session.run(
            query,
            seed=seed,
            allowed_rels=list(allowed_rels or ALLOWED_RELATIONS),
            turkey_qid=turkey_qid,
            anchor_rels=list(TURKEY_ANCHOR_RELATIONS),
        ):
            if len(items) >= limit:
                break
            key = (row["a_id"], row["x_id"], row["rel"], row["z_id"])
            if key in seen:
                continue
            seen.add(key)

            a_name = clean_name(row["a_name"], row["a_id"])
            x_name = clean_name(row["x_name"], row["x_id"])
            z_name = clean_name(row["z_name"], row["z_id"])
            rel = row["rel"]
            question = (
                f"Do {a_name} and {x_name} share the same "
                f"{rel_name(rel, relation_map)}?"
            )
            verify = (
                f"MATCH (a:Entity {{entityId:'{row['a_id']}'}})-[:{rel}]->"
                f"(z:Entity {{entityId:'{row['z_id']}'}})<-[:{rel}]-(x:Entity {{entityId:'{row['x_id']}'}}) "
                "RETURN a.name AS a, x.name AS x, z.name AS z LIMIT 1"
            )
            item = QuestionItem(
                question_id=f"TR_CMP_{len(items)+1:03d}",
                question_text=question,
                reasoning_path=(
                    f"{row['a_id']} -> {rel} -> {row['z_id']} <- {rel} <- {row['x_id']}"
                ),
                gold_answer=f"Yes; shared entity is {z_name} ({row['z_id']}).",
                difficulty="comparison",
                domain=infer_domain(rel),
                verification_cypher=verify,
                is_verified=True,
            )
            items.append(item)
    return items


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", default="bolt://localhost:7687")
    parser.add_argument("--user", default="neo4j")
    parser.add_argument("--password", required=True)
    parser.add_argument("--turkey-qid", default="Q43")
    parser.add_argument("--relation-map", help="Path to wikidata5m_relation.txt")
    parser.add_argument("--output-json", default="data/verified_questions.generated.json")
    parser.add_argument("--n-2hop", type=int, default=30)
    parser.add_argument("--n-3hop", type=int, default=15)
    parser.add_argument("--n-comparison", type=int, default=5)
    parser.add_argument("--max-seeds", type=int, default=1000)
    args = parser.parse_args()

    relation_map = load_relation_map(args.relation_map)
    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    with driver.session() as session:
        all_seeds = get_turkiye_seeds(
            session=session,
            turkey_qid=args.turkey_qid,
            max_seeds=args.max_seeds,
        )
        cinema_seeds = get_turkiye_seeds(
            session=session,
            turkey_qid=args.turkey_qid,
            max_seeds=args.max_seeds,
            start_rels=DOMAIN_RELATIONS["cinema"],
        )
        football_seeds = get_turkiye_seeds(
            session=session,
            turkey_qid=args.turkey_qid,
            max_seeds=args.max_seeds,
            start_rels=DOMAIN_RELATIONS["football"],
        )
        music_seeds = get_turkiye_seeds(
            session=session,
            turkey_qid=args.turkey_qid,
            max_seeds=args.max_seeds,
            start_rels=DOMAIN_RELATIONS["music"],
        )

        q2 = []
        q2 += generate_2hop_items(
            session, cinema_seeds, relation_map, min(10, args.n_2hop), args.turkey_qid, DOMAIN_RELATIONS["cinema"]
        )
        q2 += generate_2hop_items(
            session,
            football_seeds,
            relation_map,
            min(10, max(0, args.n_2hop - len(q2))),
            args.turkey_qid,
            DOMAIN_RELATIONS["football"],
        )
        q2 += generate_2hop_items(
            session,
            music_seeds,
            relation_map,
            min(10, max(0, args.n_2hop - len(q2))),
            args.turkey_qid,
            DOMAIN_RELATIONS["music"],
        )
        if len(q2) < args.n_2hop:
            q2 += generate_2hop_items(session, all_seeds, relation_map, args.n_2hop - len(q2), args.turkey_qid)
        q2 = q2[: args.n_2hop]

        q3 = []
        q3 += generate_3hop_items(
            session, cinema_seeds, relation_map, min(6, args.n_3hop), args.turkey_qid, DOMAIN_RELATIONS["cinema"]
        )
        q3 += generate_3hop_items(
            session,
            football_seeds,
            relation_map,
            min(6, max(0, args.n_3hop - len(q3))),
            args.turkey_qid,
            DOMAIN_RELATIONS["football"],
        )
        q3 += generate_3hop_items(
            session,
            music_seeds,
            relation_map,
            min(3, max(0, args.n_3hop - len(q3))),
            args.turkey_qid,
            DOMAIN_RELATIONS["music"],
        )
        if len(q3) < args.n_3hop:
            q3 += generate_3hop_items(session, all_seeds, relation_map, args.n_3hop - len(q3), args.turkey_qid)
        q3 = q3[: args.n_3hop]

        qcmp = []
        qcmp += generate_comparison_items(
            session, cinema_seeds, relation_map, min(2, args.n_comparison), args.turkey_qid, DOMAIN_RELATIONS["cinema"]
        )
        qcmp += generate_comparison_items(
            session,
            football_seeds,
            relation_map,
            min(2, max(0, args.n_comparison - len(qcmp))),
            args.turkey_qid,
            DOMAIN_RELATIONS["football"],
        )
        qcmp += generate_comparison_items(
            session,
            music_seeds,
            relation_map,
            min(1, max(0, args.n_comparison - len(qcmp))),
            args.turkey_qid,
            DOMAIN_RELATIONS["music"],
        )
        if len(qcmp) < args.n_comparison:
            qcmp += generate_comparison_items(
                session, all_seeds, relation_map, args.n_comparison - len(qcmp), args.turkey_qid
            )
        qcmp = qcmp[: args.n_comparison]

        for idx, item in enumerate(q2, 1):
            item.question_id = f"TR_2H_{idx:03d}"
        for idx, item in enumerate(q3, 1):
            item.question_id = f"TR_3H_{idx:03d}"
        for idx, item in enumerate(qcmp, 1):
            item.question_id = f"TR_CMP_{idx:03d}"

    driver.close()

    if len(q2) < args.n_2hop or len(q3) < args.n_3hop or len(qcmp) < args.n_comparison:
        raise SystemExit(
            "Insufficient verified paths found for required counts. "
            f"Found: 2-hop={len(q2)}, 3-hop={len(q3)}, comparison={len(qcmp)}"
        )

    all_items = [asdict(x) for x in (q2 + q3 + qcmp)]
    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(all_items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Generated {len(all_items)} verified questions "
        f"(2-hop={len(q2)}, 3-hop={len(q3)}, comparison={len(qcmp)}) -> {output_path}"
    )


if __name__ == "__main__":
    main()

