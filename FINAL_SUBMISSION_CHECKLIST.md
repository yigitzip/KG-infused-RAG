# Final Submission Checklist (Target: Full Score)

## Phase 1-2
- [ ] Türkiye entity analysis report is complete.
- [ ] Selected domain and justification are documented.
- [ ] Entity-relation map/figure is included.

## Phase 3
- [ ] `data/verified_questions.generated.json` contains exactly 50 questions.
- [ ] Distribution is exactly 30 (2-hop), 15 (3-hop), 5 (comparison).
- [ ] Every question has `reasoning_path`, `gold_answer`, `verification_cypher`, and `is_verified=true`.

## Phase 4
- [ ] Separate module files exist (`module1`, `module2`, `module3`).
- [ ] `pipeline.py` orchestrates end-to-end flow.
- [ ] P-code mapper from `wikidata5m_relation.txt` is used in Module 1 prompts/logs.
- [ ] `requirements.txt` is included.
- [ ] README contains run commands.

## Phase 5
- [ ] Method comparison table includes: NoR, Vanilla RAG, Vanilla QE, KG-Infused RAG.
- [ ] Metrics include Acc, F1, EM, Retrieval Recall.
- [ ] Domain-based and question-type analyses are reported.

## Phase 6
- [ ] At least 5 successful case studies.
- [ ] At least 5 unsuccessful case studies.
- [ ] Error categories and frequencies are reported.
- [ ] Improvement recommendations are included.

## Packaging
- [ ] Final report (IEEE format) added.
- [ ] Source code + sample I/O + README are packaged.
- [ ] Presentation/demo materials are prepared.

