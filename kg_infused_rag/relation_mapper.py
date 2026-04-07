from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional


def load_relation_map(relation_file: str | Path) -> Dict[str, str]:
    """
    Load wikidata5m_relation.txt into a {P-code: relation_name} map.

    Supported robustly:
    - P17\\tcountry
    - P17 country
    - <extra_col>\\tP17\\tcountry
    """
    path = Path(relation_file)
    if not path.exists():
        raise FileNotFoundError(f"Relation file not found: {path}")

    relation_map: Dict[str, str] = {}

    with path.open("r", encoding="utf-8", errors="replace") as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            parts = [p.strip() for p in line.split("\t") if p.strip()]
            if len(parts) < 2:
                parts = line.split()

            pcode_index: Optional[int] = next(
                (
                    idx
                    for idx, token in enumerate(parts)
                    if token.startswith("P") and token[1:].isdigit()
                ),
                None,
            )
            if pcode_index is None:
                continue
            if pcode_index + 1 >= len(parts):
                continue

            pcode = parts[pcode_index]
            if "\t" in line:
                relation_name = parts[pcode_index + 1]
            else:
                relation_name = " ".join(parts[pcode_index + 1 :])

            relation_map[pcode] = relation_name

    return relation_map


def relation_name(pcode: str, relation_map: Dict[str, str]) -> str:
    """Resolve a relation label; fallback to P-code itself."""
    return relation_map.get(pcode, pcode)


def humanize_path(path_relations: list[str], relation_map: Dict[str, str]) -> list[str]:
    """Convert relation list like ['P17','P36'] to readable names."""
    return [relation_name(rel, relation_map) for rel in path_relations]

