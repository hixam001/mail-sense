# MailSense — Software Requirements Definition (SRD)

**Version:** 1.0 · **Date:** 2026-11-19 · **Status:** Approved baseline, not yet built

> Concise statement of scope. Detailed requirements live in `SRS.md`; this document changes only when project scope changes.

## Goal
Help a student investigate whether an email is spam using **probability and statistics first**, followed by **two Naive Bayes classifiers** as practical applications. MailSense runs locally with a React/Vite interface, FastAPI API, and the historical Apache SpamAssassin Public Corpus.

## Users
- **Student/presenter:** explores distributions, computes probabilities, performs hypothesis tests and classifies example emails.
- **Instructor/reviewer:** verifies the underlying counts, statistical assumptions, reproducibility and comparison metrics.

No registration, login or role-based permissions exist in version 1.0.

## Primary end-to-end workflow
1. Developer prepares the SpamAssassin corpus and pretrains two models using offline scripts.
2. User launches the local frontend and backend; dashboard confirms dataset and model readiness.
3. User explores spam/ham counts and descriptive statistics.
4. User selects a word, sees contingency counts and empirical prior/joint/conditional/posterior probabilities.
5. User applies a chi-square independence test and examines a spam-proportion confidence interval.
6. User pastes example email text and sees **Multinomial** and **Bernoulli** Naive Bayes predictions plus estimated probabilities and explanations.
7. User compares both models on a shared held-out test set using confusion matrices and evaluation metrics.

## Must-have
- Dataset parsing, validation, deduplication, source manifest and a deterministic stratified 80/20 train/test split (seed 42).
- Descriptive statistics: mean, median, mode, quartiles, variance, standard deviation, frequency displays, histograms and box plots.
- Probability: marginal/prior, joint, conditional and Bayes posterior; explicit frequencies/denominators; Bernoulli and binomial educational demonstrations.
- Inference: chi-square independence test with assumption checks and confidence interval for spam proportion.
- Machine learning: both Multinomial and Bernoulli Naive Bayes trained from training-only vocabulary, Laplace smoothing (`alpha=1.0`).
- Predictions: one local text input, both labels and estimated spam probabilities, faithful explanations.
- Evaluation: accuracy, precision, recall, F1, confusion matrices and false-positive rate for both models on the **same untouched test set**.
- React + Vite pages for Dataset Explorer, Probability Analysis, Statistical Inference, Spam Detector and Model Evaluation; FastAPI REST endpoints, loading/empty/error states.
- Offline use after initial setup; no external inference or message transmission.

## Not in v1.0
Gmail/Outlook connections; mail sending or receiving; accounts/authentication; database or cloud sync; production filtering; external DNS/URL checks; deep-learning models; arbitrary upload UI; automatic model retraining; user prediction history.

## Acceptance check
On one laptop, an examiner can open MailSense, inspect the retained dataset and statistical summaries, validate a word's empirical Bayes calculation and chi-square test, paste an email, receive both classifiers' results, then verify each model's evaluation metrics on the identical held-out split. Empty input, missing artifacts and backend failure produce truthful errors instead of misleading results.

## Build notes
**Locked:** React/Vite frontend; Python/FastAPI backend; Apache SpamAssassin corpus; SciPy/Pandas/NumPy; scikit-learn; Recharts; local files; no DB; local deployment. Raw archive provenance and final record counts are established during ingestion, not guessed in advance. No implementation has been completed at the time of this baseline.
