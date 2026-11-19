# Graph Report - mail-sense  (2026-11-19)

## Corpus Check
- 16 files · ~29,184 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 206 nodes · 340 edges · 15 communities
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- README.md
- docs/SETUP.md
- docs/DATA_MODEL.md
- PRODUCT.md
- docs/IMPLEMENTATION_PLAN.md
- memory/HANDOFF.md
- docs/APP_FLOW.md
- docs/PRD.md
- MSE-403
- docs/SRS.md
- docs/TEST_PLAN.md
- MSE-601
- docs/SRD.md
- Analyze with Gravitas
- MSE-404

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
- `Next task` --next_task--> `MSE-301`  [EXTRACTED]
  memory/HANDOFF.md → docs/IMPLEMENTATION_PLAN.md

## Communities (15 total, 0 thin omitted)

### Community 0 - "README.md"
Cohesion: 0.09
Nodes (21): Start every task, Delivery sequence, Implement and verify, Handoff and persistent memory, Commit and push, Parse the corpus, Prepare retained records, Create the split (+13 more)

### Community 1 - "docs/SETUP.md"
Cohesion: 0.08
Nodes (22): 5. Processing pipeline, 2. Component overview, 6. API architecture, 7. Client design and state, 8. Security, privacy and data-integrity boundaries, 9. Failure handling, 10. Observability and reproducibility, 11. Architectural acceptance criteria (+14 more)

### Community 2 - "docs/DATA_MODEL.md"
Cohesion: 0.08
Nodes (22): 4. Entity `SplitManifest` (`data/processed/split_manifest.json`), 2. Entity `SourceArchive` (`data/processed/source_manifest.json`), 5. Entity `Vocabulary` (serialized with trained preprocessing pipeline), 6. Entity `TrainedModel` (`artifacts/models/{model}.joblib`, `metadata.json`), 7. Entity `ModelEvaluation` (`artifacts/reports/evaluation.json`), 8. API-view schemas (not persisted), 9. Storage layout, 10. No database / no user entity (+14 more)

### Community 3 - "PRODUCT.md"
Cohesion: 0.12
Nodes (15): Evidence on Hand, Product Principles, Accessibility & Inclusion, Users, Product Purpose, Positioning, Operating Context, Platform (+7 more)

### Community 4 - "docs/IMPLEMENTATION_PLAN.md"
Cohesion: 0.17
Nodes (15): MSE-101, MSE-102, MSE-103, MSE-104, MSE-105, MSE-106, MSE-401, MSE-602 (+7 more)

### Community 5 - "memory/HANDOFF.md"
Cohesion: 0.17
Nodes (15): MSE-301, MSE-302, MSE-303, MSE-603, MSE-604, MSE-605, MSE-606, Next task (+7 more)

### Community 6 - "docs/APP_FLOW.md"
Cohesion: 0.15
Nodes (12): 6. Core flow F-04: Spam detection, 7. Core flow F-05: Model evaluation, 8. Recovery and operational flows, 9. Decision-point matrix, 10. Screen inventory, 11. UI state and data flow principles, 12. Flow acceptance walkthrough, 2. Navigation map (+4 more)

### Community 7 - "docs/PRD.md"
Cohesion: 0.17
Nodes (11): 6. Explicitly out of scope, 7. User scenarios, 2. Goals and SMART objectives, 8. Non-functional requirements, 9. Dependencies and constraints, 10. Milestones and timeline, 11. Project state and change control, 3. Product success metrics (+3 more)

### Community 8 - "MSE-403"
Cohesion: 0.38
Nodes (11): MSE-201, MSE-202, MSE-203, MSE-204, MSE-205, MSE-206, MSE-207, MSE-402 (+3 more)

### Community 9 - "docs/SRS.md"
Cohesion: 0.20
Nodes (9): 6. Non-functional requirements, 7. Acceptance criteria (release gates), 8. Exclusions, 9. Traceability and change control, 2. Scope and locked constraints, 3. Functional requirements, 4. External interfaces, 1. Introduction (+1 more)

### Community 10 - "docs/TEST_PLAN.md"
Cohesion: 0.20
Nodes (9): 7. Manual university demonstration acceptance, 8. Defect triage and exit criteria, 9. Test execution log template, 2. Critical release-blocking scenarios, 3. Additional numerical and edge-case tests, 4. API contract tests, 1. Test philosophy, 5. Model evaluation integrity checklist (+1 more)

### Community 11 - "MSE-601"
Cohesion: 0.61
Nodes (8): MSE-501, MSE-502, MSE-503, MSE-504, MSE-505, MSE-506, MSE-507, MSE-601

### Community 12 - "docs/SRD.md"
Cohesion: 0.25
Nodes (7): Users, Primary end-to-end workflow, Must-have, Not in v1.0, Acceptance check, Build notes, Goal

### Community 13 - "Analyze with Gravitas"
Cohesion: 0.25
Nodes (8): Analyze with Gravitas, map the task, implement, test, update handoff, final checks, commit, push

### Community 14 - "MSE-404"
Cohesion: 0.80
Nodes (5): MSE-304, MSE-305, MSE-306, MSE-307, MSE-404

## Knowledge Gaps
- **143 isolated node(s):** `Delivery sequence`, `Start every task`, `Implement and verify`, `Handoff and persistent memory`, `Commit and push` (+138 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 143 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MSE-601` connect `MSE-601` to `MSE-403`?**
  _High betweenness centrality (0.004) - this node is a cross-community bridge._
- **What connects `Delivery sequence`, `Start every task`, `Implement and verify` to the rest of the system?**
  _143 weakly-connected nodes found - possible missing edges._
- **Should `README.md` be split into smaller, more focused modules?**
  _Cohesion score 0.09057971014492754 - nodes in this community are weakly interconnected._
- **Why does `MSE-603` connect `memory/HANDOFF.md` to `MSE-601`?**
  _High betweenness centrality (0.002) - this node is a cross-community bridge._
- **Should `docs/SETUP.md` be split into smaller, more focused modules?**
  _Cohesion score 0.08333333333333333 - nodes in this community are weakly interconnected._
- **Should `docs/DATA_MODEL.md` be split into smaller, more focused modules?**
  _Cohesion score 0.08333333333333333 - nodes in this community are weakly interconnected._
- **Should `PRODUCT.md` be split into smaller, more focused modules?**
  _Cohesion score 0.11764705882352941 - nodes in this community are weakly interconnected._