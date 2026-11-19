"""Completed memory must never hide pending work or invent a next ticket."""

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "memory_graph", Path(__file__).resolve().parents[2] / "memory/graph.py"
)
memory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(memory)


def inventory(first="Complete — verified", second="Complete — verified"):
    return {
        "MSE-101": (1, ["First task", first]),
        "MSE-102": (2, ["Second task", second]),
    }


def test_next_task_when_work_remains():
    assert (
        memory.planned_next(
            "Next implementation ticket: **MSE-102**.",
            inventory(second="Not started — next"),
        )
        == "MSE-102"
    )


def test_completed_backlog_has_no_next_ticket():
    assert (
        memory.planned_next("Next implementation ticket: **None** — v1.0 complete.", inventory())
        is None
    )


@pytest.mark.parametrize("status", ["Not started", "In progress", "Blocked", "Complete-ish"])
def test_no_next_rejects_any_unfinished_task(status):
    with pytest.raises(ValueError, match="all tickets are complete"):
        memory.planned_next("Next implementation ticket: **None**.", inventory(first=status))


def test_empty_inventory_is_not_completion():
    with pytest.raises(ValueError, match="all tickets are complete"):
        memory.planned_next("Next implementation ticket: **None**.", {})


@pytest.mark.parametrize("ticket", ["MSE-101", "MSE-102", "MSE-999"])
def test_next_must_be_known_and_marked_pending(ticket):
    with pytest.raises(ValueError, match="known pending ticket"):
        memory.planned_next(f"Next implementation ticket: **{ticket}**.", inventory())


def test_missing_explicit_next_state_is_invalid():
    with pytest.raises(ValueError, match="explicitly name"):
        memory.planned_next("All done", inventory())
