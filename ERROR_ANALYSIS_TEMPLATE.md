# Error Analysis Report - KG-Infused RAG (Turkiye Domain)

## 1) Run Metadata
- Date:
- Experiment ID:
- KG Snapshot:
- Neo4j DB Name:
- LLM Model(s):
- Total Questions:
- Split: 2-hop / 3-hop / comparison

## 2) Aggregate Metrics
- Exact Match:
- Path Verification Success Rate:
- Retrieval Precision@k:
- Retrieval Recall@k:
- Hallucination Rate:

## 3) Failure Categories

### A. Data Deficiency
Definition: Required fact/path does not exist in loaded KG (or is too sparse/outdated).

- Count:
- Percentage:
- Typical symptoms:
  - No valid Cypher path for expected hop pattern
  - Expected relation missing although entity exists
- Example cases:
  1. Question ID:
     - Expected path:
     - Observed issue:
     - Cypher evidence:
- Suggested actions:
  - Expand relation alternatives
  - Add domain seeds
  - Refresh KG snapshot / augment external source

### B. Entity Linking Error
Definition: Mention resolution maps to incorrect QID, causing wrong traversal.

- Count:
- Percentage:
- Typical symptoms:
  - Ambiguous Turkish name linked to incorrect entity
  - Gold path exists for intended QID but not selected QID
- Example cases:
  1. Question ID:
     - Mention:
     - Predicted QID:
     - Gold QID:
     - Downstream impact:
- Suggested actions:
  - Add TR/EN alias table
  - Add confidence threshold and fallback
  - Rerank with local context

### C. Retrieval Error
Definition: Correct path exists, but retrieval/selection fails to include it.

- Count:
- Percentage:
- Typical symptoms:
  - Candidate pruning too aggressive
  - LLM triple selection drops critical edge
  - Activation memory over-prunes useful branch
- Example cases:
  1. Question ID:
     - Gold path:
     - Retrieved path:
     - Missing hop:
- Suggested actions:
  - Increase branch factor or hop budget
  - Improve relation name prompting with P-code map
  - Tune cycle-control policy

## 4) Category Distribution
| Category | Count | % | Primary Root Cause |
|---|---:|---:|---|
| Data Deficiency |  |  |  |
| Entity Linking Error |  |  |  |
| Retrieval Error |  |  |  |

## 5) Next Iteration Plan
- [ ] Highest-impact fix #1
- [ ] Highest-impact fix #2
- [ ] Re-run on fixed 50-question set
- [ ] Compare category-wise delta

