from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple


@dataclass(frozen=True)
class Triple:
    head_qid: str
    relation: str
    tail_qid: str
    head_name: str = ""
    tail_name: str = ""


@dataclass
class ActivationState:
    frontier: List[str] = field(default_factory=list)
    visited_entities: Set[str] = field(default_factory=set)
    visited_edges: Set[Tuple[str, str, str]] = field(default_factory=set)
    selected_triples: List[Triple] = field(default_factory=list)


@dataclass
class ExpandedQuery:
    original_query: str
    expanded_query: str
    summary: str
    supporting_triples: List[Triple]


@dataclass
class GeneratedNote:
    question: str
    note: str
    evidence: List[Triple]
    metadata: Dict[str, str] = field(default_factory=dict)

