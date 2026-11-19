# MailSense working instructions

## Start every task

1. Read [GRAVITAS_MEMORY.md](GRAVITAS_MEMORY.md) and its relevant memory entries.
2. Read [docs/HANDOFF.md](docs/HANDOFF.md), especially **Next task**, current
   progress, verification evidence and blockers. Confirm the recorded state
   against the working tree and Git history; do not rely on stale notes.
3. Read [PRODUCT.md](PRODUCT.md), the relevant requirements and the acceptance
   criteria in [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md).
   `docs/SRS.md` remains the locked technical baseline.
4. Apply [.agents/skills/gravitas/SKILL.md](.agents/skills/gravitas/SKILL.md).
   Analyze the whole requested task and map its requirements, dependencies,
   affected files, implementation steps, risks and verification before editing.
   Record the planning policy and, for complex work, a scoped task contract.
   Scale the plan to the task; do not skip analysis for implementation work.

## Implement and verify

- Implement the mapped task, keeping unrelated work intact. Update the plan when
  evidence changes the scope or approach.
- Use the relevant installed skills, including Impeccable for interface work.
- Run the applicable tests and checks after the final relevant edits and before
  pushing: affected unit/integration tests, lint, type checks, builds and runtime
  checks as the implemented scope requires. Discover actual project commands;
  never invent a passing test or treat zero discovered tests as a passing suite.
- Resolve failures before pushing. If verification cannot run, record the exact
  limitation, leave the task incomplete and do not push it as verified work.
- For documentation-only work, validate changed references, backlog/status
  consistency and Git diff hygiene. State that app tests were not applicable.
- Do not mark a feature implemented until its acceptance criteria have observed
  evidence. Keep planned, synthetic and measured results distinct.

## Handoff and persistent memory

- Update [docs/HANDOFF.md](docs/HANDOFF.md) after each implementation task and
  before its commit. Record everything completed, everything remaining,
  in-progress work, changed files, commands/results, blockers and the exact next
  Jira-style ticket with its first action and acceptance criteria.
- Keep the full remaining ticket inventory synchronized with
  `docs/IMPLEMENTATION_PLAN.md`. Do not lose deferred work at a session boundary.
- Keep durable user preferences in
  [.gravitas/memory/workflow.md](.gravitas/memory/workflow.md), indexed by
  `GRAVITAS_MEMORY.md`. The handoff owns changing progress; avoid conflicting
  copies in memory files. Record failed approaches and useful recovery details.
- Revalidate the final files after the handoff update. Future sessions must read
  the handoff before selecting their next task.

## Commit and push

- The user has authorized committing and pushing completed, verified work as
  part of this workflow. Do so without repeatedly asking for routine approval.
  Respect any later instruction to pause, avoid a commit or withhold a push.
- Use consistent commit subjects: `MSE-<ticket number>: <imperative summary>`.
  Example: `MSE-101: Initialize React and FastAPI project structure`.
  Use a real backlog ticket; assign and document a ticket before committing
  newly discovered work. Never claim Jira records were created remotely.
- Use the existing configured user identity. Do not add `Co-authored-by`,
  `Signed-off-by`, AI/contributor trailers or other contributor credits, and do
  not change authorship settings or forge an author. The user's normal author
  and committer metadata remains intact.
- Inspect the staged diff, include the updated handoff, and exclude secrets,
  raw corpus messages, trained models and local runtime output. Stage intended
  paths explicitly; never discard unrelated user changes.
- Push to the configured upstream without force or history rewriting. If the
  remote has changed, integrate safely and rerun affected checks. If pushing is
  blocked, report the reason and preserve the local work for recovery.
- Verify the resulting commit, remote branch and working-tree state; report the
  commit ID, push outcome and next task. Never infer push success from a note.
