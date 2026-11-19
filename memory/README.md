# Project memory

Read [HANDOFF.md](HANDOFF.md) for completed work, remaining tickets, verification,
recovery notes and the next task. [AGENTS.md](../AGENTS.md) holds the standing
workflow preferences. [PRODUCT.md](../PRODUCT.md) and the requirements in
`docs/` remain the product authority. There are no separate copies of the
workflow or memory index elsewhere in the repository.

## Graph memory

[graphify-out/graph.json](graphify-out/graph.json) is a Graphify-generated directed
knowledge graph of the maintained documents, their sections, workflow policies,
all implementation tickets, statuses, prerequisites and the explicit next task. A completed backlog records **None**; the graph
contains no next-task edge until a new ticket is assigned.
Each node and edge has a source file/location. `EXTRACTED` relationships come
from explicit document structure, links or ticket records; no speculative
semantic relationships are added. The source hashes detect changes and removals.
This graph is a retrieval aid: follow the source before acting on a fact.

Open [graph.html](graphify-out/graph.html) in a browser to search and explore
connections, or read the generated [graph report](graphify-out/GRAPH_REPORT.md).
The HTML viewer loads Graphify's pinned visualization library from a CDN;
graph generation and CLI retrieval run locally without network access after setup.

## Setup

From the repository root, with Python 3.12 available:

```bash
uv venv --python 3.12 memory/.venv
uv pip install --python memory/.venv/bin/python -r memory/requirements.txt
```

This isolated environment is ignored by Git. Do not add it to commits or mix its
dependencies into the MailSense application environment. Graphify does
not need a separate API key for this explicit document/task extraction.

## Retrieve context

From the repository root:

```bash
memory/.venv/bin/graphify query "Next task" --graph memory/graphify-out/graph.json
memory/.venv/bin/graphify explain "MSE-101" --graph memory/graphify-out/graph.json
memory/.venv/bin/graphify path "MSE-106" "MSE-101" --graph memory/graphify-out/graph.json
```

The dependency direction is **task → prerequisite**. Check the handoff directly
for authoritative progress, especially when starting a new session.

## Update and verify

1. Update the actual requirements or instructions when needed, then update the
   handoff with progress, verification, blockers and the next ticket.
2. Rebuild and check the graph:

```bash
memory/.venv/bin/python memory/graph.py build
memory/.venv/bin/python memory/graph.py check
```

3. Run applicable project tests and inspect the diff. Commit the changed sources
   and all three generated graph artifacts together using the ticket notation
   in `AGENTS.md`, then push. A source edit after generation requires a rebuild.

`graph.py` extracts only an explicit allowlist: root agent/product/design/README
documents, `docs/*.md`, this guide and the handoff. It excludes corpus messages,
credentials, installed agent skills, session logs, virtual environments and
generated graph outputs. It uses Graphify's builder, clustering, analysis and
exporters; it does not run an LLM extraction pass. When new kinds of memory
relationships are needed, update the extractor and its checks together.


When all 39 implementation tickets are complete, the handoff records
`Next implementation ticket: **None**`. The extractor rejects this terminal
state if any task is unfinished. Do not invent a next ticket after release;
record and analyze a new user-requested task before changing the completed scope.
