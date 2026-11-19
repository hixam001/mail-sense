# Eight-step classroom demonstration

Prepare the corpus/models using [SETUP](SETUP.md), start the API and UI using
[README](../README.md), and open `http://localhost:5173/`. Use the authored example
below rather than personal email. Allow roughly 10–15 minutes; this is a suggested
presentation duration, not a measured runtime benchmark.

1. **Establish readiness.** On Overview, show dataset, Multinomial, Bernoulli and
   evaluation all ready. Explain that runtime processing stays local and frozen
   artifacts are prepared by CLI. A clone without preparation is degraded.
2. **Inspect the data.** Open Dataset Explorer with all scope: 5,862 emails,
   4,107 ham and 1,755 spam. Expand provenance/exclusions: 54 malformed-MIME and
   130 duplicate exclusions. Compare token-count summaries and histogram, then
   change measurement to character count and explain units. Box whiskers are
   minimum/maximum. For a hand check, show `[2,4,4,6]`: mean/median/mode=4,
   variance=8/3, SD≈1.633, Q1=3.5 and Q3=4.5. This fixture is separate from corpus
   summaries; details are in [reproducibility](REPRODUCIBILITY.md).
3. **Count before using Bayes.** Open Probability, analyze `free` in all scope.
   Read the table: spam 811/944 present/absent; ham 577/3530. Compute
   P(spam|free)=811/(811+577)=.584294. Show the five numerator/denominator pairs
   and Bayes' identity. An unseen token gives an undefined empirical posterior.
4. **Explain the distribution model.** On that page set n=10,k=1. A success
   means word presence, irrespective of class. Bernoulli has mean p and variance
   p(1−p); binomial assumes independent trials with constant p. The actual
   p=1388/5862 differs from the synthetic p=.25 example whose PMF is .1877117.
5. **Question association and uncertainty.** Follow the association link, run
   Pearson at α=.05 and inspect expected counts. For actual `free`, χ²≈703.783,
   df=1 and p≈4.499085×10⁻¹⁵⁵, with every expected cell≥5. This is association
   under assumptions, not causation. The 95% Wilson interval for 1755/5862 is
   approximately [.287796,.311238]; curated historical data do not establish
   current inbox prevalence. This test is different from Naive Bayes' conditional
   independence assumption among features given class.
6. **Compare predictions and explanations.** In Spam Detector choose **Load
   synthetic example**, then **Classify with both models**. The authored project
   meeting example below is intended ham. The frozen Multinomial predicts spam
   (P≈.638553); Bernoulli predicts ham (P≈1.670165×10⁻¹²). Discuss the disagreement
   and expand both log-odds explanations. Bernoulli includes absent features;
   the estimates are not calibrated certainty. Clear the text afterward.
7. **Interpret held-out errors.** Open Model Evaluation: 1,173 identical test
   IDs, training-only vocabulary, seed42 and α=1. Multinomial has TN814/FP8/FN14/TP337;
   Bernoulli has TN815/FP7/FN70/TP281. Verify accuracy and recall using these
   counts. Explain the cost of hiding legitimate mail (FP) versus missing spam
   (FN). Scores apply to this holdout, not modern email generally.
8. **Show validation and recovery, then state limits.** Return to the detector,
   submit blank text and read the validation. Stop only your API process with
   Ctrl+C in its terminal; submit the synthetic text and show the connection
   error. Restart the API with the same command and retry; both results recover.
   State corpus age, residual near duplicates/dependence, one holdout,
   uncalibrated estimates and untested modern phishing/attachments. No live mail
   or original corpus messages are sent during the demonstration.

```text
Subject: Project meeting
Hello team, please review the project notes before our meeting tomorrow. Thank you.
```

## Rehearsal and evidence

The source-only installation rehearsal runs every preparation stage and its
verifier, then the production browser walkthrough and real failure-recovery
checks. See [fresh-install results](../artifacts/reports/fresh_install.json).
The automated equivalent uses:

```bash
python3 scripts/browser_check.py --production
python3 scripts/release_check.py
```

Run them with existing servers stopped. Step1 and the five pages are exercised
by `frontend/tests/browser.mjs`, including desktop/mobile and keyboard navigation.
The statistical hand examples are independently reconciled by
`backend/scripts/verify_science.py`. Step8 uses actual API stop/restart and a
missing-model fixture under `frontend/tests/failures.mjs`; this fixture has its
own temporary private copy and leaves the working corpus/models unchanged.
These checks verify the actions and expected results; no attended classroom
presentation or external examiner signoff is claimed.

If readiness is degraded, complete preparation or follow the relevant setup
recovery instructions. If the port is occupied, stop only the process you own.
Keep the fixed loopback ports; changing them breaks the documented API/CORS flow.
