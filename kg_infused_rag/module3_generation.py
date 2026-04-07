from __future__ import annotations

from .interfaces import LLMGateway
from .types import ExpandedQuery, GeneratedNote


class FactEnhancedGenerator:
    """
    Module 3:
    - Produce fact-enhanced notes from expanded query + evidence triples
    """

    def __init__(self, llm_client: LLMGateway) -> None:
        self.llm_client = llm_client

    def build_note(self, question: str, expanded_query: str, evidence) -> str:
        return self.llm_client.generate_fact_note(
            question=question,
            expanded_query=expanded_query,
            triples=evidence,
        )

    def run(self, question: str, expanded_query_obj: ExpandedQuery) -> GeneratedNote:
        note = self.build_note(
            question=question,
            expanded_query=expanded_query_obj.expanded_query,
            evidence=expanded_query_obj.supporting_triples,
        )
        return GeneratedNote(
            question=question,
            note=note,
            evidence=expanded_query_obj.supporting_triples,
            metadata={"module": "generation"},
        )

