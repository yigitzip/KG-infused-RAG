from __future__ import annotations

from .interfaces import LLMGateway, Neo4jGateway
from .relation_mapper import relation_name
from .types import ActivationState, Triple


class SpreadingActivationRetriever:
    """
    Module 1:
    - Retrieve neighborhood triples from Neo4j
    - Let LLM rank/select the most relevant triples
    - Track activation memory to prevent cycles
    """

    def __init__(
        self,
        neo4j_client: Neo4jGateway,
        llm_client: LLMGateway,
        relation_map: dict[str, str],
        max_hops: int = 3,
        branch_factor: int = 5,
        candidate_limit: int = 100,
    ) -> None:
        self.neo4j_client = neo4j_client
        self.llm_client = llm_client
        self.relation_map = relation_map
        self.max_hops = max_hops
        self.branch_factor = branch_factor
        self.candidate_limit = candidate_limit

    def _filter_cycle_edges(self, candidates: list[Triple], state: ActivationState) -> list[Triple]:
        filtered: list[Triple] = []
        for triple in candidates:
            edge_key = (triple.head_qid, triple.relation, triple.tail_qid)
            if edge_key in state.visited_edges:
                continue
            filtered.append(triple)
        return filtered

    def to_llm_candidates(self, triples: list[Triple]) -> list[dict[str, str]]:
        """
        Convert triples to an LLM-friendly structure with human-readable relation names.
        """
        rendered: list[dict[str, str]] = []
        for triple in triples:
            rendered.append(
                {
                    "head_qid": triple.head_qid,
                    "head_name": triple.head_name,
                    "relation_pcode": triple.relation,
                    "relation_name": relation_name(triple.relation, self.relation_map),
                    "tail_qid": triple.tail_qid,
                    "tail_name": triple.tail_name,
                }
            )
        return rendered

    def run(self, query: str, seed_qids: list[str]) -> list[Triple]:
        state = ActivationState(frontier=list(seed_qids), visited_entities=set(seed_qids))

        for _hop in range(self.max_hops):
            if not state.frontier:
                break

            next_frontier: list[str] = []
            for entity_qid in state.frontier:
                candidates = self.neo4j_client.get_neighbors(
                    entity_qid,
                    limit=self.candidate_limit,
                )
                candidates = self._filter_cycle_edges(candidates, state)
                if not candidates:
                    continue

                selected = self.llm_client.select_triples(
                    query=query,
                    candidate_triples=candidates,
                    relation_map=self.relation_map,
                    k=self.branch_factor,
                )

                for triple in selected:
                    edge_key = (triple.head_qid, triple.relation, triple.tail_qid)
                    if edge_key in state.visited_edges:
                        continue
                    state.visited_edges.add(edge_key)
                    state.selected_triples.append(triple)

                    if triple.tail_qid not in state.visited_entities:
                        state.visited_entities.add(triple.tail_qid)
                        next_frontier.append(triple.tail_qid)

            state.frontier = next_frontier

        return state.selected_triples

