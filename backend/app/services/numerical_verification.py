"""Reproducible academic examples and aggregate-only measured verification report."""

import math
import platform

import numpy as np
import scipy

from app.services.corpus_split import load_split_dataset
from app.services.descriptive import descriptive_statistics, summarize
from app.services.inference import confidence_interval, hypothesis_test, pearson_table, wilson_score
from app.services.probability import bernoulli_binomial, word_contingency


def teaching_records():
    rows = []
    for label, present, absent in (("spam", 180, 120), ("ham", 70, 630)):
        for index in range(present + absent):
            rows.append(
                dict(
                    label=label,
                    model_text="free free" if index < present else "meeting",
                    split="test" if index % 5 == 0 else "train",
                )
            )
    return rows


def build_verification(root=None):
    checks = []

    def check(name, actual, expected, relative=1e-12, absolute=0):
        checks.append(
            dict(
                name=name,
                actual=actual,
                expected=expected,
                relative_tolerance=relative,
                absolute_tolerance=absolute,
                passed=math.isclose(actual, expected, rel_tol=relative, abs_tol=absolute),
            )
        )

    descriptive = summarize([2, 4, 4, 6])
    check("descriptive_mean", descriptive["mean"], 4)
    check("sample_variance", descriptive["sample_variance"], 8 / 3)
    check("sample_standard_deviation", descriptive["sample_std"], math.sqrt(8 / 3))
    check("linear_q1", descriptive["q1"], 3.5)
    check("linear_q3", descriptive["q3"], 4.5)
    empirical = word_contingency(teaching_records(), "free")
    check("empirical_prior", empirical["probabilities"]["p_spam"]["value"], 0.3)
    check("word_probability", empirical["probabilities"]["p_word"]["value"], 0.25)
    check("empirical_posterior", empirical["probabilities"]["p_spam_given_word"]["value"], 0.72)
    binomial = bernoulli_binomial(0.25, 10, 1)
    check("binomial_pmf", binomial["binomial_pmf"], 0.1877117156982422)
    pearson = pearson_table([[180, 120], [70, 630]])
    check("pearson_statistic", pearson["chi_square"], 280)
    check("pearson_p_value", pearson["p_value"], 7.50924e-63, relative=1e-6)
    wilson = wilson_score(300, 1000)
    check("wilson_lower_rounded", wilson["lower"], 0.2724, relative=0, absolute=0.00005)
    check("wilson_upper_rounded", wilson["upper"], 0.3291, relative=0, absolute=0.00005)
    report = dict(
        schema_version=1,
        runtime=dict(
            python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__
        ),
        passed=all(item["passed"] for item in checks),
        checks=checks,
        synthetic_examples=dict(
            descriptive=descriptive,
            contingency=empirical,
            binomial=binomial,
            chi_square=pearson,
            wilson=wilson,
        ),
        measured=None,
    )
    if root is not None:
        rows, manifest = load_split_dataset(root)
        report["measured"] = dict(
            dataset_id=manifest["dataset_id"],
            split_id=manifest["split_id"],
            inputs=manifest["inputs"],
            scopes={},
        )
        for scope in ("all", "train", "test"):
            report["measured"]["scopes"][scope] = {
                "character_statistics": descriptive_statistics(rows, scope, "character_count"),
                "token_statistics": descriptive_statistics(rows, scope, "token_count"),
                "free_word": word_contingency(rows, "free", scope),
                "free_chi_square": hypothesis_test(rows, "free", scope),
                "spam_interval": confidence_interval(rows, scope),
            }
    return report
