// Q43 (Türkiye) — import sonrası Browser'da çalıştırın
MATCH (t:Entity {entityId: 'Q43'})
RETURN t.entityId AS id, t.name AS name
LIMIT 1;

MATCH (t:Entity {entityId: 'Q43'})-[r]->(n:Entity)
RETURN type(r) AS relation_type, count(*) AS cnt
ORDER BY cnt DESC
LIMIT 40;

MATCH (t:Entity {entityId: 'Q43'})-[r:P150]->(c:Entity)
RETURN c.entityId AS region, c.name AS label
LIMIT 50;
