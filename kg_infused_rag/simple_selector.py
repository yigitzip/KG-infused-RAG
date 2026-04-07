from __future__ import annotations

from .types import Triple


class HeuristicLLMSelector:
    """
    Lightweight stand-in for LLM selection.
    Scores triples by question-relation relevance for demo use.
    """

    KEYWORD_TO_RELATIONS: dict[str, set[str]] = {
        "coach": {"P286"},
        "manager": {"P286"},
        "stadium": {"P115"},
        "venue": {"P115"},
        "team": {"P54"},
        "club": {"P54"},
        "director": {"P57"},
        "cast": {"P161"},
        "actor": {"P161"},
        "award": {"P166"},
        "birth": {"P19"},
        "born": {"P19"},
        "citizenship": {"P27"},
        "country": {"P17", "P27"},
        "record": {"P264"},
        "label": {"P264"},
        "music": {"P175", "P136"},
        "genre": {"P136"},
    }

    def _target_relations(self, query: str) -> set[str]:
        q = query.lower()
        targets: set[str] = set()
        for token, rels in self.KEYWORD_TO_RELATIONS.items():
            if token in q:
                targets.update(rels)
        return targets

    def select_triples(
        self,
        query: str,
        candidate_triples: list[Triple],
        relation_map: dict[str, str],
        k: int = 5,
    ) -> list[Triple]:
        q = query.lower()
        targets = self._target_relations(query)
        scored: list[tuple[float, Triple]] = []

        for triple in candidate_triples:
            score = 0.0
            rel_label = relation_map.get(triple.relation, "").lower()
            if triple.relation in targets:
                score += 5.0
            if rel_label and any(tok in rel_label for tok in q.split()):
                score += 2.0
            if triple.head_name and any(tok in triple.head_name.lower() for tok in q.split()):
                score += 1.0
            if triple.tail_name and any(tok in triple.tail_name.lower() for tok in q.split()):
                score += 1.0
            scored.append((score, triple))

        scored.sort(key=lambda x: x[0], reverse=True)
        selected = [item[1] for item in scored[:k]]
        return selected if selected else candidate_triples[:k]

    def summarize_kg_context(self, triples: list[Triple]) -> str:
        if not triples:
            return "No KG evidence selected."
        lines = []
        for triple in triples[:8]:
            h = triple.head_name or triple.head_qid
            t = triple.tail_name or triple.tail_qid
            lines.append(f"{h} -[{triple.relation}]-> {t}")
        return " ; ".join(lines)

    def expand_query(self, original_query: str, kg_summary: str) -> str:
        return f"{original_query}\nRelevant KG facts: {kg_summary}"

    def generate_fact_note(self, question: str, expanded_query: str, triples: list[Triple]) -> str:
        return f"Question: {question}\nExpanded: {expanded_query}\nEvidence triples: {len(triples)}"

