---
type: user
name: mail-sense-delivery-workflow
description: Persistent task planning, handoff, testing and Git delivery preferences
created: 2026-11-19
updated: 2026-11-19
---

The user requires the entire requested task to be analyzed with Gravitas and
mapped before implementation. After implementation, update the project handoff,
verify the final state, commit the files and push the completed work. Run the
tests and checks needed to establish that the implemented scope works before
every push. Do not claim application tests passed when no implementation exists.

The handoff at [docs/HANDOFF.md](../../docs/HANDOFF.md) is the single progress
record: include completed and remaining work, verification, blockers and the
exact next task so every session can resume without rediscovery. Read it first;
keep this memory focused on enduring preferences rather than duplicating status.

Use consistent Jira-style commit subjects: `MSE-<ticket>: <imperative summary>`,
matching documented backlog IDs. Preserve the configured Git identity. Add no
contributor attribution, co-author trailers, sign-offs or AI credits. The user's
ordinary author/committer metadata is still required.

Routine commits and pushes for completed, verified tasks are authorized; do not
ask again unless a new action is destructive, authorization changes, or a real
permission boundary requires it. A failed or unavailable required check prevents
claiming verified completion and pushing that work as complete. Report any
blockage honestly and retain a resumable state.

**Why:** The user wants reliable continuity, consistent ticket traceability and
tested delivery across sessions.

**How to apply:** Follow [AGENTS.md](../../AGENTS.md) for every repository task.
Read the handoff before choosing work; update it before the commit; rerun checks
after relevant final edits; verify the push rather than assuming it succeeded.
