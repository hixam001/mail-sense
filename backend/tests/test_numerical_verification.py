import sys

from test_corpus_dataset import mail, prepare

from app.services.corpus_dataset import prepare_dataset
from app.services.corpus_split import prepare_split
from app.services.numerical_verification import build_verification
from scripts import verify_statistics as cli


def test_three_worked_examples_and_t05_domain_results():
    report = build_verification()
    assert report["passed"] and len(report["checks"]) == 13
    assert report["measured"] is None
    assert report["synthetic_examples"]["descriptive"]["mean"] == 4
    assert report["synthetic_examples"]["contingency"]["total"] == 1000
    assert report["synthetic_examples"]["chi_square"]["chi_square"] == 280
    assert report["synthetic_examples"]["wilson"]["point_estimate"] == 0.3
    p_check = next(item for item in report["checks"] if item["name"] == "pearson_p_value")
    assert p_check["absolute_tolerance"] == 0


def test_cli_report_reproducible_private_safe_and_tampering_detected(tmp_path, monkeypatch, capsys):
    messages = {
        group: [mail(f"{group} {i}") for i in range(5)]
        for group in ("easy_ham", "easy_ham_2", "hard_ham", "spam", "spam_2")
    }
    prepare(tmp_path, messages)
    prepare_dataset(tmp_path)
    prepare_split(tmp_path)
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["verify_statistics", "run"])
    assert cli.main() == 0
    path = tmp_path / cli.REPORT
    first = path.read_bytes()
    assert b"private@example.invalid" not in first and b"private-member-" not in first
    assert cli.main() == 0 and path.read_bytes() == first
    monkeypatch.setattr(sys, "argv", ["verify_statistics", "verify"])
    assert cli.main() == 0
    path.write_text("tampered")
    assert cli.main() == 1
    assert "missing_invalid_or_stale_artifacts" in capsys.readouterr().err


def test_missing_dataset_is_safe(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["verify_statistics", "verify"])
    assert cli.main() == 1
    assert "Traceback" not in capsys.readouterr().err
