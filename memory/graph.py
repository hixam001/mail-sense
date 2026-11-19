#!/usr/bin/env python3
"""Build/check explicit project memory with Graphify; no external model calls."""

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "memory/graphify-out"
PLAN = "docs/IMPLEMENTATION_PLAN.md"
HANDOFF = "memory/HANDOFF.md"
VERSION = "0.9.112"


def documents():
    paths = ["AGENTS.md", "PRODUCT.md", "DESIGN.md", "README.md", "memory/README.md", HANDOFF]
    paths += [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / "docs").glob("*.md"))]
    return {p: (ROOT / p).read_text(encoding="utf-8") for p in sorted(paths)}


def fingerprints():
    paths = [*documents(), "memory/graph.py", "memory/requirements.txt"]
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}


def rows(text):
    return {
        cells[0]: (line, cells[1:])
        for line, raw in enumerate(text.splitlines(), 1)
        if raw.startswith("| MSE-")
        and (cells := [c.strip() for c in raw.strip("|").split("|")])
    }


def prerequisites(value, known):
    result = set()
    for first, last in re.findall(r"MSE-(\d+)(?:[–-](\d+))?", value):
        for number in range(int(first), int(last or first) + 1):
            ticket = f"MSE-{number}"
            if ticket in known:
                result.add(ticket)
    return sorted(result)


def planned_next(handoff, states):
    """Allow a terminal handoff only after the entire inventory is complete."""
    match = re.search(
        r"^Next implementation ticket: \*\*(MSE-\d+|None)\*\*", handoff, re.M
    )
    if not match:
        raise ValueError("Handoff must explicitly name its next ticket or None")
    ticket = match.group(1)
    if ticket == "None":
        if not states or not all(
            cells[1].split(" — ", 1)[0] == "Complete" for _, cells in states.values()
        ):
            raise ValueError("No next task is valid only when all tickets are complete")
        return None
    if ticket not in states or not states[ticket][1][1].startswith("Not started — next"):
        raise ValueError("Next ticket must be a known pending ticket marked next")
    return ticket


def extraction():
    docs = documents()
    nodes, edges = {}, {}

    def node(key, label, source, line, **attrs):
        nodes[key] = dict(id=key, label=label, source_file=source,
                          source_location=f"L{line}", file_type="concept",
                          _origin="semantic", **attrs)
        return key

    def edge(source, target, relation, path, line):
        key = (source, target)
        if key in edges and edges[key]["relation"] != relation:
            raise ValueError(f"Conflicting relations for {key}")
        edges[key] = dict(source=source, target=target, relation=relation,
                          confidence="EXTRACTED", weight=1.0, source_file=path,
                          source_location=f"L{line}")

    for path, text in docs.items():
        doc = node(f"document:{path}", path, path, 1, kind="document")
        lines = text.splitlines()
        headings = [(i, raw[3:].strip()) for i, raw in enumerate(lines) if raw.startswith("## ")]
        for index, (start, label) in enumerate(headings):
            stop = headings[index + 1][0] if index + 1 < len(headings) else len(lines)
            section = node(f"section:{path}:{start + 1}", label, path, start + 1,
                           kind="section", summary="\n".join(lines[start + 1:stop]).strip())
            edge(doc, section, "contains", path, start + 1)
        for line, raw in enumerate(lines, 1):
            for target in re.findall(r"\[[^\]\n]+\]\(([^)]+)\)", raw):
                if "://" in target or target.startswith(("#", "mailto:")):
                    continue
                dest = ((ROOT / path).parent / unquote(target.split("#")[0])).resolve()
                relative = dest.relative_to(ROOT).as_posix()
                if relative in docs and relative != path:
                    edge(doc, f"document:{relative}", "references", path, line)

    tickets, states = rows(docs[PLAN]), rows(docs[HANDOFF])
    if tickets.keys() != states.keys():
        raise ValueError("Handoff and implementation plan ticket inventories differ")
    for ticket, (line, cells) in tickets.items():
        node(ticket, ticket, PLAN, line, kind="task", task_id=ticket,
             summary=cells[0], acceptance=cells[2], status=states[ticket][1][1])
        edge(f"document:{PLAN}", ticket, "defines", PLAN, line)
        edge(f"document:{HANDOFF}", ticket, "tracks", HANDOFF, states[ticket][0])
        for dependency in prerequisites(cells[1], tickets):
            edge(ticket, dependency, "requires", PLAN, line)

    next_ticket = planned_next(docs[HANDOFF], states)
    next_node = next(n["id"] for n in nodes.values()
                     if n["source_file"] == HANDOFF and n["label"] == "Next task")
    if next_ticket is not None:
        edge(next_node, next_ticket, "next_task", HANDOFF,
             int(nodes[next_node]["source_location"][1:]))

    workflow_line, sequence = next((i, s) for i, s in enumerate(docs["AGENTS.md"].splitlines(), 1) if " → " in s)
    previous = None
    for index, action in enumerate(sequence.rstrip(".").split(" → "), 1):
        key = node(f"workflow:{index}", action, "AGENTS.md", workflow_line, kind="workflow_step")
        if previous:
            edge(previous, key, "followed_by", "AGENTS.md", workflow_line)
        previous = key
    edge("document:AGENTS.md", "workflow:1", "starts_with", "AGENTS.md", workflow_line)
    return dict(nodes=list(nodes.values()), edges=list(edges.values()))


def build():
    from graphify.analyze import god_nodes, suggest_questions, surprising_connections
    from graphify.build import build_from_json
    from graphify.cluster import cluster, label_communities_by_hub, score_all
    from graphify.export import to_html, to_json
    from graphify.report import generate

    if importlib.metadata.version("graphifyy") != VERSION:
        raise ValueError("Install the pinned memory/requirements.txt before rebuilding")
    docs = documents()
    graph = build_from_json(extraction(), directed=True, root=ROOT, dedup=False)
    graph.graph.update(source_hashes=fingerprints(), extraction="explicit-document-and-ticket-structure")
    communities = cluster(graph)
    labels = label_communities_by_hub(graph, communities)
    OUT.mkdir(parents=True, exist_ok=True)
    if not to_json(graph, communities, str(OUT / "graph.json"), force=True,
                   built_at_commit="", community_labels=labels):
        raise RuntimeError("Graphify JSON export failed")
    if not to_html(graph, communities, str(OUT / "graph.html"), community_labels=labels):
        raise RuntimeError("Graphify HTML export failed")
    report = generate(graph, communities, score_all(graph, communities), labels,
                      god_nodes(graph), surprising_connections(graph, communities),
                      {"total_files": len(docs), "total_words": sum(len(t.split()) for t in docs.values())},
                      {"input": 0, "output": 0}, root="mail-sense",
                      suggested_questions=suggest_questions(graph, communities, labels))
    (OUT / "GRAPH_REPORT.md").write_text(report, encoding="utf-8")
    print(f"Graphify {VERSION}: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} directed edges, {len(communities)} communities")


def check():
    import networkx as nx

    data = json.loads((OUT / "graph.json").read_text(encoding="utf-8"))
    assert data["directed"] and data["graph"]["graphify_version"] == VERSION
    assert data["graph"]["source_hashes"] == fingerprints(), "Stale graph: rebuild after source changes"
    nodes = {n["id"]: n for n in data["nodes"]}
    assert len(nodes) == len(data["nodes"]), "Duplicate node IDs"
    edges = data.get("links", data.get("edges", []))
    graph = nx.DiGraph()
    graph.add_nodes_from(nodes)
    for item in [*nodes.values(), *edges]:
        source = ROOT / item["source_file"]
        assert source.is_file(), f"Missing source: {source}"
        line = int(item["source_location"][1:])
        assert 1 <= line <= len(source.read_text(encoding="utf-8").splitlines())
    for e in edges:
        assert e["source"] in nodes and e["target"] in nodes, "Dangling graph edge"
        assert e["confidence"] == "EXTRACTED"
        graph.add_edge(e["source"], e["target"], relation=e["relation"])
    docs = documents()
    tickets, states = rows(docs[PLAN]), rows(docs[HANDOFF])
    task_nodes = {n["task_id"]: n for n in nodes.values() if n.get("kind") == "task"}
    assert task_nodes.keys() == tickets.keys() == states.keys()
    for ticket, (_, cells) in tickets.items():
        assert task_nodes[ticket]["status"] == states[ticket][1][1]
        dependencies = {nodes[v]["task_id"] for u, v, d in graph.edges(data=True)
                        if u == task_nodes[ticket]["id"] and d["relation"] == "requires"}
        assert dependencies == set(prerequisites(cells[1], tickets))
    next_edges = [e for e in edges if e["relation"] == "next_task"]
    expected_next = planned_next(docs[HANDOFF], states)
    if expected_next is None:
        assert not next_edges, "A completed backlog must not invent another task"
    else:
        assert len(next_edges) == 1 and next_edges[0]["target"] == expected_next
    dependencies = nx.DiGraph((u, v) for u, v, d in graph.edges(data=True) if d["relation"] == "requires")
    assert nx.is_directed_acyclic_graph(dependencies), "Cyclic ticket prerequisites"
    assert nx.has_path(dependencies, task_nodes["MSE-106"]["id"], task_nodes["MSE-101"]["id"])
    workflow = [(u, v) for u, v, d in graph.edges(data=True) if d["relation"] == "followed_by"]
    assert len(workflow) == 7 and nx.is_directed_acyclic_graph(nx.DiGraph(workflow))
    assert "vis.Network" in (OUT / "graph.html").read_text(encoding="utf-8")
    assert "Community" in (OUT / "GRAPH_REPORT.md").read_text(encoding="utf-8")
    for path, text in docs.items():
        for target in re.findall(r"\[[^\]\n]+\]\(([^)]+)\)", text):
            if "://" not in target and not target.startswith(("#", "mailto:")):
                assert ((ROOT / path).parent / unquote(target.split("#")[0])).exists(), (path, target)
    for legacy in ["GRAVITAS_MEMORY.md", ".gravitas/memory/workflow.md", "docs/HANDOFF.md"]:
        assert not (ROOT / legacy).exists(), f"Redundant legacy file: {legacy}"
        assert not any(legacy in t for t in docs.values()), f"Stale legacy reference: {legacy}"
    assert subprocess.run(["git", "check-ignore", "-q", "memory/.venv/bin/python"], cwd=ROOT).returncode == 0
    paths = ["AGENTS.md", "README.md", ".gitignore", "docs/IMPLEMENTATION_PLAN.md", "memory"]
    for stage in [[], ["--cached"]]:
        subprocess.run(["git", "-c", "core.whitespace=-blank-at-eol,blank-at-eof,space-before-tab",
                        "diff", *stage, "--check", "--", *paths], cwd=ROOT, check=True)
    print(f"PASS: {len(nodes)} nodes, {len(edges)} sourced edges, {len(task_nodes)} ticket statuses/dependencies; source freshness, next task, workflow, links and cleanup verified")
    print("VERDICT: PASS")


def main():
    # Graphify's Louvain fallback traverses sets: pin their iteration order.
    if os.environ.get("PYTHONHASHSEED") != "0":
        os.execve(sys.executable, [sys.executable, *sys.argv], {**os.environ, "PYTHONHASHSEED": "0"})
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build", "check"])
    args = parser.parse_args()
    try:
        {"build": build, "check": check}[args.command]()
    except (AssertionError, ValueError, RuntimeError) as error:
        print(f"VERDICT: FAIL -- {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
