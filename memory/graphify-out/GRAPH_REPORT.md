# Graph Report - mail-sense  (2026-11-19)

## Corpus Check
- 22 files · ~36,488 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 231 nodes · 369 edges · 11 communities
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- memory/HANDOFF.md
- README.md
- PRODUCT.md
- docs/DATA_MODEL.md
- docs/SETUP.md
- docs/TEST_PLAN.md
- docs/APP_FLOW.md
- docs/ARCHITECTURE.md
- docs/PRD.md
- docs/SRS.md
- Analyze with Gravitas

## God Nodes (most connected - your core abstractions)
1. `MSE-601` - 13 edges
2. `MSE-403` - 10 edges
3. `MSE-404` - 10 edges
4. `MSE-501` - 10 edges
5. `MSE-207` - 8 edges
6. `MSE-405` - 8 edges
7. `MSE-507` - 8 edges
8. `MSE-201` - 7 edges
9. `MSE-203` - 7 edges
10. `MSE-304` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Next task` --next_task--> `MSE-604`  [EXTRACTED]
  memory/HANDOFF.md → docs/IMPLEMENTATION_PLAN.md

## Communities (11 total, 0 thin omitted)

### Community 0 - "memory/HANDOFF.md"
Cohesion: 0.11
Nodes (54): MSE-101, MSE-102, MSE-103, MSE-104, MSE-105, MSE-106, MSE-201, MSE-202 (+46 more)

### Community 1 - "README.md"
Cohesion: 0.08
Nodes (23): Start every task, Delivery sequence, Implement and verify, Handoff and persistent memory, Commit and push, Parse the corpus, Prepare retained records, Create the split (+15 more)

### Community 2 - "PRODUCT.md"
Cohesion: 0.08
Nodes (22): Evidence on Hand, Product Principles, Accessibility & Inclusion, Users, Product Purpose, Positioning, Operating Context, Platform (+14 more)

### Community 3 - "docs/DATA_MODEL.md"
Cohesion: 0.08
Nodes (22): 4. Entity `SplitManifest` (`data/processed/split_manifest.json`), 2. Entity `SourceArchive` (`data/processed/source_manifest.json`), 5. Entity `Vocabulary` (serialized with trained preprocessing pipeline), 6. Entity `TrainedModel` (`artifacts/models/{model}.joblib`, `metadata.json`), 7. Entity `ModelEvaluation` (`artifacts/reports/evaluation.json`), 8. API-view schemas (not persisted), 9. Storage layout, 10. No database / no user entity (+14 more)

### Community 4 - "docs/SETUP.md"
Cohesion: 0.09
Nodes (18): Measured performance, Dependency advisories and reproduction, Observed behavior, Acquire the corpus, Parse the corpus, Prepare retained records, Install, Create the split (+10 more)

### Community 5 - "docs/TEST_PLAN.md"
Cohesion: 0.09
Nodes (19): Measured results, Inference and explanations, Limitations and intended use, Reproduce, Data and experimental boundary, Actual corpus and models, An honest disagreement example, Hand-checkable examples (+11 more)

### Community 6 - "docs/APP_FLOW.md"
Cohesion: 0.15
Nodes (12): 6. Core flow F-04: Spam detection, 7. Core flow F-05: Model evaluation, 8. Recovery and operational flows, 9. Decision-point matrix, 10. Screen inventory, 11. UI state and data flow principles, 12. Flow acceptance walkthrough, 2. Navigation map (+4 more)

### Community 7 - "docs/ARCHITECTURE.md"
Cohesion: 0.17
Nodes (11): 5. Processing pipeline, 2. Component overview, 6. API architecture, 7. Client design and state, 8. Security, privacy and data-integrity boundaries, 9. Failure handling, 10. Observability and reproducibility, 11. Architectural acceptance criteria (+3 more)

### Community 8 - "docs/PRD.md"
Cohesion: 0.17
Nodes (11): 6. Explicitly out of scope, 7. User scenarios, 2. Goals and SMART objectives, 8. Non-functional requirements, 9. Dependencies and constraints, 10. Milestones and timeline, 11. Project state and change control, 3. Product success metrics (+3 more)

### Community 9 - "docs/SRS.md"
Cohesion: 0.20
Nodes (9): 6. Non-functional requirements, 7. Acceptance criteria (release gates), 8. Exclusions, 9. Traceability and change control, 2. Scope and locked constraints, 3. Functional requirements, 4. External interfaces, 1. Introduction (+1 more)

### Community 10 - "Analyze with Gravitas"
Cohesion: 0.25
Nodes (8): Analyze with Gravitas, map the task, implement, test, update handoff, final checks, commit, push

## Knowledge Gaps
- **162 isolated node(s):** `Delivery sequence`, `Start every task`, `Implement and verify`, `Handoff and persistent memory`, `Commit and push` (+157 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 163 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `Delivery sequence`, `Start every task`, `Implement and verify` to the rest of the system?**
  _162 weakly-connected nodes found - possible missing edges._
- **Should `memory/HANDOFF.md` be split into smaller, more focused modules?**
  _Cohesion score 0.11168831168831168 - nodes in this community are weakly interconnected._
- **Should `README.md` be split into smaller, more focused modules?**
  _Cohesion score 0.08307692307692308 - nodes in this community are weakly interconnected._
- **Should `PRODUCT.md` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._
- **Should `docs/DATA_MODEL.md` be split into smaller, more focused modules?**
  _Cohesion score 0.08333333333333333 - nodes in this community are weakly interconnected._
- **Should `docs/SETUP.md` be split into smaller, more focused modules?**
  _Cohesion score 0.09090909090909091 - nodes in this community are weakly interconnected._
- **Should `docs/TEST_PLAN.md` be split into smaller, more focused modules?**
  _Cohesion score 0.09090909090909091 - nodes in this community are weakly interconnected._