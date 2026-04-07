from __future__ import annotations

from typing import Protocol

from .types import Triple


class Neo4jGateway(Protocol):
    def get_neighbors(self, entity_qid: str, limit: int = 100) -> list[Triple]:
        ...


class LLMGateway(Protocol):
    def select_triples(
        self,
        query: str,
        candidate_triples: list[Triple],
        relation_map: dict[str, str],
        k: int = 5,
    ) -> list[Triple]:
        ...

    def summarize_kg_context(self, triples: list[Triple]) -> str:
        ...

    def expand_query(self, original_query: str, kg_summary: str) -> str:
        ...

    def generate_fact_note(
        self,
        question: str,
        expanded_query: str,
        triples: list[Triple],
    ) -> str:
        ...


class EntityLinkerGateway(Protocol):
    def link(self, question: str) -> list[str]:
        ...

