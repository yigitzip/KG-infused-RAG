# KG-infused-RAG

Knowledge graph–infused retrieval-augmented generation (RAG) experiments and tooling.

## Overview

This repository explores combining structured knowledge graphs with RAG pipelines to improve grounding, explainability, and multi-hop reasoning.

## Getting started

Details will be added as the project grows.

## Phase 4 Modular Pipeline (Python)

New modular scaffolding is available under `kg_infused_rag/`:

- `relation_mapper.py`: maps Wikidata P-codes from `wikidata5m_relation.txt` into readable labels.
- `module1_spreading_activation.py`: Neo4j triple retrieval + LLM-based selection + activation memory.
- `module2_query_expansion.py`: subgraph summarization and query expansion.
- `module3_generation.py`: fact-enhanced note generation.
- `pipeline.py`: end-to-end orchestration for the 3 modules.

## Data Generation Artifacts

- `data/verified_questions.3hop.sample.json`: sample 3-hop entry with verification Cypher.
- `scripts/verify_single_3hop_question.py`: helper script to execute the sample Cypher against Neo4j.
- `scripts/generate_verified_questions_from_neo4j.py`: auto-generates 50 verified Türkiye questions from Neo4j.
- `ERROR_ANALYSIS_TEMPLATE.md`: structured report template for failure categories:
  Data Deficiency, Entity Linking Error, Retrieval Error.

## Neo4j Desktop Workflow

Yes, Neo4j Desktop is the correct way for this project.

1. Start your local DB in Neo4j Desktop (default bolt: `bolt://localhost:7687`).
2. Install dependencies:
   - `python3 -m pip install -r requirements.txt`
3. Generate verified 50-question dataset:
   - `python3 scripts/generate_verified_questions_from_neo4j.py --password "<YOUR_NEO4J_PASSWORD>" --relation-map "/path/to/wikidata5m_relation.txt" --output-json data/verified_questions.generated.json`
4. (Optional) Verify one sample manually:
   - `python3 scripts/verify_single_3hop_question.py --json data/verified_questions.3hop.sample.json --uri bolt://localhost:7687 --user neo4j --password "<YOUR_NEO4J_PASSWORD>"`

If generation reports insufficient paths, increase seed search:
- `--max-seeds 3000`
