from __future__ import annotations

from neo4j import GraphDatabase

from .types import Triple


class Neo4jClient:
    """Concrete Neo4j gateway for spreading activation retrieval."""

    def __init__(self, uri: str, user: str, password: str) -> None:
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        self.driver.close()

    def get_neighbors(self, entity_qid: str, limit: int = 100) -> list[Triple]:
        query = """
        MATCH (h:Entity {entityId:$qid})-[r]->(t:Entity)
        WHERE type(r) STARTS WITH 'P'
        RETURN h.entityId AS h_qid, h.name AS h_name,
               type(r) AS rel,
               t.entityId AS t_qid, t.name AS t_name
        LIMIT $limit
        """
        with self.driver.session() as session:
            rows = session.run(query, qid=entity_qid, limit=limit)
            return [
                Triple(
                    head_qid=row["h_qid"],
                    relation=row["rel"],
                    tail_qid=row["t_qid"],
                    head_name=(row["h_name"] or "").strip(),
                    tail_name=(row["t_name"] or "").strip(),
                )
                for row in rows
            ]

    def search_entities(self, keyword: str, limit: int = 10) -> list[tuple[str, str]]:
        query = """
        MATCH (e:Entity)
        WHERE e.name IS NOT NULL
          AND toLower(e.name) CONTAINS toLower($keyword)
        RETURN e.entityId AS qid, e.name AS name
        LIMIT $limit
        """
        with self.driver.session() as session:
            rows = session.run(query, keyword=keyword, limit=limit)
            return [(row["qid"], row["name"]) for row in rows]

