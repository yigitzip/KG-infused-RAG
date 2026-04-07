from __future__ import annotations

from .interfaces import LLMGateway
from .types import ExpandedQuery, Triple


class KGQueryExpander:
    """
    Module 2:
    - Build an LLM summary from selected KG triples
    - Expand the original query with graph-grounded context
    """

    def __init__(self, llm_client: LLMGateway) -> None:
        self.llm_client = llm_client

    def summarize_subgraph(self, triples: list[Triple]) -> str:
        return self.llm_client.summarize_kg_context(triples)

    def expand_query(self, original_query: str, subgraph_summary: str) -> str:
        return self.llm_client.expand_query(original_query, subgraph_summary)

    def run(self, original_query: str, triples: list[Triple]) -> ExpandedQuery:
        summary = self.summarize_subgraph(triples)
        expanded = self.expand_query(original_query, summary)
        return ExpandedQuery(
            original_query=original_query,
            expanded_query=expanded,
            summary=summary,
            supporting_triples=triples,
        )

