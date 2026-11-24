# MailSense presenter notes

Suggested main talk: approximately 20 minutes plus the guided demo. Timing is a delivery suggestion.


## Slide01: MailSense

Introduce the project as a probability and statistics application. The released web app has an overview and five modules. The later research paper extends the frozen comparison with paired inference; it does not train a new classifier. Five author spaces and an instructor space remain intentionally blank. Use the main slides for an approximately 20-minute explanation, then follow the demo. Duration is a suggested delivery plan, not a measured benchmark.

Sources: README.md, docs/PAPER.md


## Slide02: Accuracy is only the start

Explain the asymmetric consequences of errors. A false negative misses spam; a false positive labels legitimate email as spam. The practical preference may change with those costs. State that the study uses historical curated data. The presentation will first show the application, then explain how the paper strengthens the interpretation of its fixed results. The statistical methods answer these questions directly.

Sources: docs/paper/manuscript.json


## Slide03: One platform, six connected screens

Walk through the navigation in this order. Scope controls affect the analytical pages, not model training. Detector always uses frozen training models and Evaluation always uses held-out results. Selected words carry between Probability and Inference through local UI state. Email text does not enter URLs or persistent history. There are no accounts, inbox integrations or training buttons in the normal interface.

Sources: frontend/src/App.jsx, docs/APP_FLOW.md


## Slide04: A local, inspectable architecture

The browser runs at localhost:5173 and the API at 127.0.0.1:8000. React pages use a fixed allowlisted API client. FastAPI services compute statistics from verified artifacts and use cached frozen models. Corpus preparation and training are separate CLI operations. There is no database, cloud inference or mail service. Node 22.23.5/npm 10.9.9 and Python 3.12.15/uv 0.13.9 are pinned. The guide contains the full direct/transitive dependency inventory.

Sources: docs/ARCHITECTURE.md, frontend/package.json, backend/pyproject.toml


## Slide05: Measure what survives preparation

Use measured preparation counts rather than copying an upstream corpus total. Five canonical official archives are pinned by SHA-256. Strict MIME parsing accepts 5992 candidates; exact-text deduplication then removes 130 rows. No conflicting-label group was observed; synthetic tests cover the removal policy when conflicts occur. Five control files and directory entries are counted separately. Original mail remains local and untracked.

Sources: data/processed/source_manifest.json, data/processed/parsing_report.json, data/processed/deduplication_report.json


## Slide06: Freeze the comparison before inference

Training has 4689 records:3285 ham and 1404 spam. Test has 1173:822 ham and 351 spam. The 60135-feature vocabulary is fitted to training text only;12200 tokens occurring only in test text remain excluded. Exact IDs and content hashes are disjoint. Near duplicates can remain. The secondary paper analyzes an already inspected holdout, so additional statistical comparisons are exploratory rather than preregistered new validation.

Sources: data/processed/split_manifest.json, artifacts/reports/reproducibility.json, docs/PAPER.md


## Slide07: Dataset Explorer: inspect before modeling

Open /dataset. Confirm 5862 all-scope emails and the ham/spam counts. Expand Provenance, exclusions and reproducibility for archives, hashes and excluded counts. Measurement changes the descriptive statistics and length distribution. Chart class filters the histogram, five-number plot and document frequencies; it does not remove the other class from the comparison table. Click a word in the top 15 list to open Probability. Whiskers are min/max rather than Tukey fences.

Sources: frontend/src/pages/Dataset.jsx, docs/report/figures/manifest.json


## Slide08: Every summary needs a convention

Contrast the long-tailed actual corpus with the separate hand-checkable fixture [2,4,4,6]. That fixture has mean/median/mode 4, Q 1=3.5,Q 3=4.5 and sample variance 8/3. A tied mode returns the smallest value with a note. Empty groups have undefined summaries; sample variance and SD are undefined below n=2. The mean being above the median is descriptive evidence of skew; it does not prove class separation.

Sources: artifacts/reports/statistics_verification.json, docs/STATISTICAL_METHODS.md


## Slide09: Bayes starts with four counts

The observed table is spam-present 811, spam-absent 944, ham-present 577, ham-absent 3530. P(spam)=1755/5862; P(word)=1388/5862; P(word|spam)=811/1755. Multiplying the likelihood and prior, then dividing by the evidence, gives the same posterior as 811/1388. Each email counts once for presence. This is not the full classifier probability for a whole message. An unobserved word has an undefined posterior, not zero spam probability.

Sources: artifacts/reports/statistics_verification.json, frontend/src/pages/Probability.jsx


## Slide10: One email becomes a repeated-trial model

Use /probability with trials 10 and successes 1. The actual free document-presence p is 1388/5862≈.236779 and the UI PMF is about 20.81%. The separate synthetic p=.25 teaching example gives C(10,1)*.25*.75^9=.1877117, or 18.77%. Do not mix those settings. Trials range 1..100 and k must be 0..n. Observed word presence supplies p; corpus curation does not establish independence or stable prevalence.

Sources: docs/STATISTICAL_METHODS.md, artifacts/reports/statistics_verification.json


## Slide11: Statistical Inference: make assumptions visible

Open /statistics. The chi-square test runs only when Run chi-square test is pressed. Changing word, scope or alpha hides the previous result. Alpha must be finite and strictly between 0 and 1. Confidence can range.80 to.99. If expected counts are too small or the table is degenerate, the app withholds an automatic decision. A displayed assumption check is not proof that messages are independent.

Sources: frontend/src/pages/Statistics.jsx, docs/report/figures/manifest.json


## Slide12: A tiny p-value needs a careful explanation

The Pearson null is independence of word presence and class. Every expected cell for free exceeds 5; no Yates correction is used. The result describes association under assumptions, not causation. Wilson bounds are based on 1755 spam out of 5862. The proportion is already observed for this selected corpus; the interval illustrates a sampling model. Word/class association is a different question from Naive Bayes conditional independence among features given class.

Sources: artifacts/reports/statistics_verification.json, docs/REPRODUCIBILITY.md


## Slide13: Two event models, one feature map

For class c, prior Nc/N comes only from training. Multinomial theta_cj=(T_cj+1)/(sum T_ck+V), and its score is log prior+sum x_j log theta_cj. Bernoulli q_cj=(D_cj+1)/(N_c+2); its score includes b_j log q plus (1-b_j)log(1-q) over every feature. Repeating a word changes Multinomial evidence but does not create a new Bernoulli presence. Unknown words have no fitted weight. Scores are normalized estimates, not calibrated certainty.

Sources: docs/STATISTICAL_METHODS.md, docs/MODEL_CARD.md


## Slide14: The models can disagree on ordinary text

Open /detect and choose Load synthetic example, then Classify with both models. The project-meeting text is authored and intended ham. It demonstrates a false alarm relative to that intended label and model disagreement; it is not a corpus record. Input is transient,1..50000 trimmed Unicode characters. Blank, overlong and control-only inputs are rejected without truncation. Clear text and results or navigate away to discard content. The result heading receives keyboard focus.

Sources: artifacts/reports/reproducibility.json, frontend/src/pages/Detect.jsx


## Slide15: Explain the full score, including what is absent

Expand Inspect log-odds contributions under each model. Signed terms favor spam or ham in log posterior odds; they are not probability percentages or causal effects. The displayed top terms plus the remainder, prior and absent-feature aggregate reconstruct the full score. Multinomial weights include repetition. Bernoulli includes every absent fitted feature. Click a present token for a general vocabulary weight, which is distinct from that token’s effect on one whole message.

Sources: frontend/src/pages/Detect.jsx, backend/app/services/prediction.py


## Slide16: Compare five measures on the same test set

Open /evaluation and inspect identical 1173 test IDs. Accuracy M 98.12%, B 93.44%; precision 97.68/97.57%; recall 96.01/80.06%; F1 96.84/87.95%; FPR.97/.85%. Metrics must use their own denominators. Similar precision does not imply similar spam recall. The evaluation page blocks incompatible split identities. Displayed values come from frozen artifacts; normal navigation never trains a classifier.

Sources: artifacts/reports/evaluation.json, frontend/src/pages/Evaluation.jsx


## Slide17: False alarms and missed spam are different errors

Read the two matrices aloud. Multinomial TN 814,FP 8,FN 14,TP 337; Bernoulli TN 815,FP 7,FN 70,TP 281. Each matrix sums 1173 with 822 actual ham and 351 actual spam. Accuracy=(TP+TN)/N; recall=TP/(TP+FN); FPR=FP/(FP+TN). False positives could hide legitimate communication in a real filter. MailSense itself does not send, block or quarantine mail.

Sources: artifacts/reports/evaluation.json, docs/MODEL_CARD.md


## Slide18: The paper preserves the pairing between predictions

The paper reconstructs the joint correctness table from both predictions on each frozen test message. Separate confusion matrices do not reveal which errors overlap. Among 63 discordant pairs,59 favor Multinomial and 4 favor Bernoulli. Under equal marginal error probabilities and independent message pairs, the exact binomial McNemar comparison gives the stated p-value. This is secondary exploratory analysis of an inspected holdout, not new independent validation or a claim about all future training runs.

Sources: artifacts/reports/paper_statistics.json, docs/paper/manuscript.json


## Slide19: The advantage has a size and an uncertainty

All differences are Multinomial minus Bernoulli in percentage points. Accuracy 4.69 [3.50,5.97]; recall 15.95 [12.25,19.94]; FPR.12 [-.36,.73]. Bootstrap messages with both correctness indicators together, or equivalently draw counts over their joint cells within each class. Percentile limits condition on fitted models and the fixed class composition. They omit training variation and may be optimistic when threads or near duplicates violate exchangeability.

Sources: artifacts/reports/paper_statistics.json


## Slide20: Describe association strength as well as significance

The odds ratio is 811*3530/(944*577), using all retained records. It is not a probability ratio and does not imply 5.26 times the posterior probability of spam. Phi is sqrt(chi-square/n). These are descriptive and working-model association quantities for a known teaching word, not causal effects or a search-adjusted discovery. Word association was not used to choose vocabulary or retune the classifiers.

Sources: artifacts/reports/paper_statistics.json, docs/paper/manuscript.json


## Slide21: What if a false alarm costs more?

Let one missed spam cost 1 and one false positive cost lambda. At the existing decisions, the losses cross at 56, where both have 462 cost units. At equal cost losses are 22/77. At lambda 100 losses are 814/770. The break-even is unstable because only one net false-positive difference separates the models. The project does not estimate a user cost or recommend a production threshold. The chart’s x axis is numeric rather than equal-spaced categories.

Sources: artifacts/reports/paper_statistics.json


## Slide22: A classroom walkthrough in eight steps

Use docs/DEMO.md for the exact sequence and expected values. First show all readiness checks, then Dataset, Probability and Inference. Demonstrate the authored meeting text and both score explanations. Confirm evaluation uses identical test IDs. For recovery, stop only the API process you own with Ctrl+C, show the error, restart with the documented launcher, and retry. Do not delete working models to stage a classroom failure. Clear example text and state the limitations. Suggested demo duration 10–15 minutes.

Sources: docs/DEMO.md


## Slide23: Verification follows the evidence boundary

The deck reuses recorded evidence: release checks on Nov1 9 and secondary analysis on Nov 22,2026. No new application test run is claimed by creating this presentation. Known-answer math, safe archive handling, split isolation, artifact hashes, exact refits and confusion arithmetic were checked. Production Chromium covered six routes at 1366 x 900 and 390 x 844, keyboard focus, stale results, empty/error/retry and transient text. Fresh source-only setup and real API restart/missing-model recovery are documented. This is not a formal full accessibility audit or penetration test.

Sources: artifacts/reports/release.json, artifacts/reports/paper_document.json, docs/TEST_PLAN.md


## Slide24: Keep the demonstration on one computer

Normal runtime requests remain local. The API uses fixed host/origin policy,512 KiB wire-body and 4 KiB query bounds, no-store responses and trimmed 1..50000-character prediction input. Message HTML stays text; resources are not fetched. Only trusted project-created joblib files load after hash checks. Initial dependencies/corpus/browser downloads require internet. Offline workflow was verified in an isolated Linux child namespace with a kernel-denied external probe and unchanged parent network. No user or live message is sent through a mail system.

Sources: docs/RUNTIME_VERIFICATION.md, artifacts/reports/offline_namespace.json


## Slide25: Measure the target on documented hardware

These are recorded Nov1 9 measurements, not a new benchmark. The prediction text was 100 synthetic characters. The client measured full HTTP requests after warmup and used nearest-rank p95. Hardware had 12 visible logical CPUs; backend Python 3.12.15. RAM, cold startup, concurrent load and maximum-input latency were not benchmarked. Maximum input validity was tested separately. Do not present these numbers as universal performance.

Sources: artifacts/reports/runtime_smoke.json, docs/RUNTIME_VERIFICATION.md


## Slide26: Know where the evidence stops

The paired methods are statistically useful but depend on message independence and the experiment’s sampling boundary. No multiple-testing correction, external corpus, temporal test or calibration study is supplied. Native Windows is unsupported by the Node wrapper; macOS/arm 64 selections are untested. Chromium 143/151 on Linux are recorded, not physical mobile or assistive technology sessions. Future research should use temporal or thread-grouped independent data and a stated cost policy before selecting an operating point.

Sources: docs/RELEASE.md, docs/paper/manuscript.json


## Slide27: Count clearly. Compare fairly. Explain uncertainty.

Close with the conceptual contribution: statistical measures change how the result is interpreted. The application makes counts and assumptions inspectable, and the paper shows that the accuracy advantage comes largely from spam recall while false-positive uncertainty remains. Offer the repository, editable paper and platform guide. Invite questions on denominators, pairing, absence effects and the independent-test boundary rather than claiming production security.

Sources: README.md, docs/PAPER.md


## Slide28: Sources and further reading

The presentation is grounded in the local implementation docs, model card, measured JSON reports and the research paper. The paper’s ten numbered references cover Sahami’s cost-sensitive filtering, McCallum/Nigam event models, Metsis variants, the project, Dietterich’s comparisons, Wilson intervals, Efron bootstrap, Apache corpus provenance, scikit-learn and NIST odds-ratio inference. Full titles and clickable primary URLs are in the speaker notes and source reference list. Preserve attribution when editing slides.

Sources: docs/paper/references.json


## Slide29: The local API has twelve versioned routes

All routes use /api/v1. The twelve paths are health, dataset/summary, dataset/statistics, dataset/distributions, probability/word, probability/distributions, statistics/hypothesis-test, statistics/confidence-interval, predict, models/metrics, models/comparison and models/explanations. Only hypothesis-test and predict are POST. Data preparation and training have no API endpoint. Safe error envelopes and validation prevent bodies/paths/traces from leaking. The complete guide lists parameters and examples; local OpenAPI JSON remains available while CDN-backed Swagger/Redoc is disabled.

Sources: docs/API_CONTRACT.md, backend/app/main.py


## Slide30: Reproduce, then rehearse

Use README/SETUP for every exact command; installation alone is not data/model preparation. Node wrapper avoids a broken system Node. uv run --directory backend --frozen python -m scripts.serve starts the API, and python 3 scripts/node.py npm --prefix frontend run dev starts the UI. Use analyze_paper verify only after preparation to reproduce the secondary analysis. App datasets/models stay ignored; public manifests and aggregate reports are shareable. Fresh acquisition timestamps can change provenance identities while scientific outcomes reproduce.

Sources: README.md, docs/SETUP.md, docs/PAPER.md
