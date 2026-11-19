# Graph Report - mail-sense  (2026-11-19)

## Corpus Check
- 25 files · ~41,310 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 249 nodes · 419 edges · 15 communities
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- memory/HANDOFF.md
- PRODUCT.md
- docs/STATISTICAL_METHODS.md
- AGENTS.md
- docs/SETUP.md
- docs/APP_FLOW.md
- docs/UNIVERSITY_REPORT.md
- docs/ARCHITECTURE.md
- docs/RELEASE.md
- docs/PRD.md
- docs/TEST_PLAN.md
- docs/UI_VERIFICATION.md
- docs/SRS.md
- README.md
- docs/MODEL_CARD.md

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
- None detected - all connections are within the same source files.

## Communities (15 total, 0 thin omitted)

### Community 0 - "memory/HANDOFF.md"
Cohesion: 0.11
Nodes (55): MSE-101, MSE-102, MSE-103, MSE-104, MSE-105, MSE-106, MSE-201, MSE-202 (+47 more)

### Community 1 - "PRODUCT.md"
Cohesion: 0.08
Nodes (22): Evidence on Hand, Product Principles, Accessibility & Inclusion, Users, Product Purpose, Positioning, Operating Context, Platform (+14 more)

### Community 2 - "docs/STATISTICAL_METHODS.md"
Cohesion: 0.08
Nodes (22): 4. Entity `SplitManifest` (`data/processed/split_manifest.json`), 2. Entity `SourceArchive` (`data/processed/source_manifest.json`), 5. Entity `Vocabulary` (serialized with trained preprocessing pipeline), 6. Entity `TrainedModel` (`artifacts/models/{model}.joblib`, `metadata.json`), 7. Entity `ModelEvaluation` (`artifacts/reports/evaluation.json`), 8. API-view schemas (not persisted), 9. Storage layout, 10. No database / no user entity (+14 more)

### Community 3 - "AGENTS.md"
Cohesion: 0.11
Nodes (17): Start every task, Delivery sequence, Implement and verify, Handoff and persistent memory, Commit and push, Setup, Retrieve context, Update and verify (+9 more)

### Community 4 - "docs/SETUP.md"
Cohesion: 0.12
Nodes (15): Acquire the corpus, Parse the corpus, Prepare retained records, Install, Create the split, Supported baseline, Numerical verification, Train and verify local models (+7 more)

### Community 5 - "docs/APP_FLOW.md"
Cohesion: 0.15
Nodes (12): 6. Core flow F-04: Spam detection, 7. Core flow F-05: Model evaluation, 8. Recovery and operational flows, 9. Decision-point matrix, 10. Screen inventory, 11. UI state and data flow principles, 12. Flow acceptance walkthrough, 2. Navigation map (+4 more)

### Community 6 - "docs/UNIVERSITY_REPORT.md"
Cohesion: 0.15
Nodes (12): 4. Descriptive statistics, 5. Empirical probabilities and distributions, 1. Objectives and scope, 6. Statistical inference and uncertainty, 7. Both Naive Bayes classifiers, 8. Measured held-out evaluation, 9. Verification, local privacy and runtime measurements, 2. Architecture and reproducibility boundary (+4 more)

### Community 7 - "docs/ARCHITECTURE.md"
Cohesion: 0.17
Nodes (11): 5. Processing pipeline, 2. Component overview, 6. API architecture, 7. Client design and state, 8. Security, privacy and data-integrity boundaries, 9. Failure handling, 10. Observability and reproducibility, 11. Architectural acceptance criteria (+3 more)

### Community 8 - "docs/RELEASE.md"
Cohesion: 0.18
Nodes (9): Rehearsal and evidence, Release checklist and acceptance mapping, Known limitations, Recorded implementation choices, Reproduce release checks, Actual corpus and models, An honest disagreement example, Hand-checkable examples (+1 more)

### Community 9 - "docs/PRD.md"
Cohesion: 0.17
Nodes (11): 6. Explicitly out of scope, 7. User scenarios, 2. Goals and SMART objectives, 8. Non-functional requirements, 9. Dependencies and constraints, 10. Milestones and timeline, 11. Project state and change control, 3. Product success metrics (+3 more)

### Community 10 - "docs/TEST_PLAN.md"
Cohesion: 0.17
Nodes (11): 7. Manual university demonstration acceptance, 8. Defect triage and exit criteria, 9. Test execution log template, Consolidated critical acceptance, Release verification, 2. Critical release-blocking scenarios, 3. Additional numerical and edge-case tests, 4. API contract tests (+3 more)

### Community 11 - "docs/UI_VERIFICATION.md"
Cohesion: 0.18
Nodes (7): Observed behavior, Measured final release performance, Dependency advisories and reproduction, Implementation decisions, Direction contract, Reproduce, Final v1.0.0 rerun

### Community 12 - "docs/SRS.md"
Cohesion: 0.20
Nodes (9): 6. Non-functional requirements, 7. Acceptance criteria (release gates), 8. Exclusions, 9. Traceability and change control, 2. Scope and locked constraints, 3. Functional requirements, 4. External interfaces, 1. Introduction (+1 more)

### Community 13 - "README.md"
Cohesion: 0.29
Nodes (6): Measured experiment, Documentation and project memory, Local data and scope, Install and prepare, Run, Verify

### Community 14 - "docs/MODEL_CARD.md"
Cohesion: 0.33
Nodes (5): Measured results, Inference and explanations, Limitations and intended use, Reproduce, Data and experimental boundary

## Knowledge Gaps
- **178 isolated node(s):** `Delivery sequence`, `Start every task`, `Implement and verify`, `Handoff and persistent memory`, `Commit and push` (+173 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 178 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `Delivery sequence`, `Start every task`, `Implement and verify` to the rest of the system?**
  _178 weakly-connected nodes found - possible missing edges._
- **Should `memory/HANDOFF.md` be split into smaller, more focused modules?**
  _Cohesion score 0.10776942355889724 - nodes in this community are weakly interconnected._
- **Should `PRODUCT.md` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._
- **Should `docs/STATISTICAL_METHODS.md` be split into smaller, more focused modules?**
  _Cohesion score 0.08333333333333333 - nodes in this community are weakly interconnected._
- **Should `AGENTS.md` be split into smaller, more focused modules?**
  _Cohesion score 0.1111111111111111 - nodes in this community are weakly interconnected._
- **Should `docs/SETUP.md` be split into smaller, more focused modules?**
  _Cohesion score 0.125 - nodes in this community are weakly interconnected._