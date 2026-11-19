# MailSense — Data Model and Local Artifact Specification

**Version:** 1.1 · **Date:** 2026-11-19 · **Status:** Source acquisition implemented; processing/model artifacts remain planned  
**Storage choice:** Local files (CSV + JSON metadata + trusted joblib model artifacts). **No database.**

## 1. Design principles

The term *data model* means canonical records and saved artifacts, **not SQL tables**. Source emails may contain personally identifiable information and executable-looking HTML/attachments. Keep raw data local and avoid committing it to a shared repository. The frontend receives only aggregated results and model predictions, never direct raw MIME payloads.

Relationships:
```text
source_archive (1) ──> (many) processed_email
processed_email ──> exact-text deduplication ──> train/test split
train split ──> shared vocabulary ──> MultinomialNB + BernoulliNB
both models + shared test IDs ──> model_evaluation
```

## 2. Entity `SourceArchive` (`data/processed/source_manifest.json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `archive_name` | string | Yes | e.g. `20030228_easy_ham.tar.bz2` |
| `source_url` | string | Yes | Trusted official corpus URL; ingestion does not fetch arbitrary user URLs |
| `source_group` | enum | Yes | `easy_ham`, `easy_ham_2`, `hard_ham`, `spam`, `spam_2` |
| `label` | enum | Yes | `spam` for `spam*`, else `ham` |
| `sha256` | string | Yes | Checksum of downloaded archive bytes |
| `size_bytes` | integer > 0 | Yes | Downloaded compressed archive size |
| `acquired_at` | ISO timestamp | Yes | When downloaded locally |
| `processing_status` | enum | Yes | `not_started` after acquisition; `complete` after parsing |
| `files_seen` | integer >= 0 or null | Yes | Null until parsing; then count before validation |
| `files_accepted` | integer >= 0 or null | Yes | Null until parsing; then count before global deduplication |
| `files_rejected` | integer >= 0 or null | Yes | Null until parsing; then count rejected by parsing/validation |

The manifest envelope has `schema_version: 1`, `dataset_source`, official index
and README URLs, `selection_policy: "one_canonical_archive_per_group"`,
`checksum_origin: "locally_computed_sha256"` and an `archives` array containing
exactly one entry for each approved group. URLs, filenames and labels must match
the fixed canonical selection; timestamps are timezone-aware UTC.

Acquisition records all three parsing counters as explicit `null` with
`processing_status: "not_started"`. MSE-104 will populate integer counts and
set `complete`; `files_seen = files_accepted + files_rejected` then applies.
This lifecycle clarification avoids reporting fabricated zero counts before
any message has been parsed. Archive byte sizes are measured independently of
email record counts. No cleaned/retained total is established by acquisition.

**Archive selection rule:** Select a coherent latest collection per group. For example, `20030228_easy_ham`, `20030228_easy_ham_2`, `20030228_hard_ham`, `20030228_spam`, and `20050311_spam_2`. Older date-prefixed archives are snapshots/revisions, **not additional independent groups**. Record exact versions/checksums at ingestion and verify official source before download. Untrusted tar members must not escape the extraction directory.

## 3. Entity `ProcessedEmail` (`data/processed/messages.csv`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `message_id` | string | Yes | Stable hash-based ID, unique after dedup |
| `source_group` | enum | Yes | One of the five corpus groups |
| `source_archive` | string | Yes | References manifest `archive_name` |
| `source_file` | string | Yes | Relative member name, never API-exposed |
| `label` | `spam`/`ham` | Yes | Class truth from source group |
| `subject_text` | string | Yes | Decoded/cleaned subject, may be empty |
| `body_text` | string | Yes | Decoded/cleaned textual body, may be empty if subject nonempty |
| `model_text` | string | Yes | Consistent concatenation of subject + body |
| `character_count` | integer >= 0 | Yes | Unicode characters in normalized model text |
| `token_count` | integer >= 0 | Yes | Count after the canonical tokenizer |
| `content_sha256` | string | Yes | Hash of normalized model text for deduplication |
| `split` | `train`/`test` | Yes | Assigned after deduplication |

Rules:
- `model_text` cannot be blank after normalization; a blank-message record is rejected.
- `source_file` must be a safe relative path; never accept paths supplied to API.
- The combination of source group and original filename is **provenance only**, never a feature.
- `message_id` stays stable for identical canonical input and archive selection; split assignment saved separately and deterministic.
- If an identical normalized text appears under conflicting labels, exclude the conflicting group and log the count; do not leak duplicates across train and test or silently pick a label.
- Do not store model predictions as a new field on `ProcessedEmail`; predictions are computed on demand.
- The UI can inspect aggregates but should not expose complete raw source bodies as a browsing feature.

## 4. Entity `SplitManifest` (`data/processed/split_manifest.json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `dataset_id` | string | Yes | Hash over canonical retained records/config |
| `split_id` | string | Yes | Stable identifier of partition |
| `seed` | integer | Yes | `42` |
| `train_fraction` | float | Yes | `0.8` |
| `test_fraction` | float | Yes | `0.2` |
| `stratified_by` | string | Yes | `label` |
| `train_ids` | array of string | Yes | Unique, disjoint |
| `test_ids` | array of string | Yes | Unique, disjoint |
| `train_counts` | map | Yes | Includes `spam`, `ham` |
| `test_counts` | map | Yes | Includes `spam`, `ham` |
| `preprocessing_version` | string | Yes | Stable version identifier |

Invariants: `train_ids ∩ test_ids = ∅`; union equals the retained dataset IDs; the same corpus/config/seed yields identical membership. Perform split prior to fitting CountVectorizer vocabulary; do not re-fit it using the test set.

## 5. Entity `Vocabulary` (serialized with trained preprocessing pipeline)

| Field | Type | Required | Notes |
|---|---|---|---|
| `token_to_index` | map[string,int] | Yes | Learned on train only |
| `tokenizer_config` | object | Yes | Case-folding, regex/tokenization, stopword policy |
| `vocab_size` | integer >= 1 | Yes | Number of retained features |
| `min_df` | integer | Yes | Default `1`, documented in training config |
| `ngram_range` | pair | Yes | v1.0 default `(1,1)` unigrams |

Training fits a single `CountVectorizer` on training text; MultinomialNB consumes count vectors and BernoulliNB consumes binary presence (`counts > 0`). Both thus share feature names and train/test boundaries. BernoulliNB's score additionally accounts for absence of known features.

## 6. Entity `TrainedModel` (`artifacts/models/{model}.joblib`, `metadata.json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `model_id` | enum | Yes | `multinomial` or `bernoulli` |
| `algorithm` | string | Yes | scikit-learn estimator identity |
| `alpha` | number > 0 | Yes | `1.0` approved baseline |
| `dataset_id` | string | Yes | Matches split manifest |
| `split_id` | string | Yes | Must match both models |
| `trained_at` | ISO timestamp | Yes | Local training time |
| `feature_count` | integer | Yes | Shared vocabulary size |
| `pipeline_version` | string | Yes | For compatibility checks |
| `classes` | array of string | Yes | Contains `ham`, `spam` exactly |
| `training_record_count` | integer | Yes | Matches split manifest |
| `artifact_sha256` | string | Yes | Validate loaded file integrity |

Model files serialized using joblib/pickle must be loaded **only from project-created, trusted local artifacts**; never load uploaded/untrusted pickle files. Fail safely if expected metadata/checksum mismatch.

## 7. Entity `ModelEvaluation` (`artifacts/reports/evaluation.json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `model_id` | enum | Yes | `multinomial` / `bernoulli` |
| `dataset_id` | string | Yes | Same source for both models |
| `split_id` | string | Yes | Same held-out test IDs |
| `positive_class` | string | Yes | Always `spam` |
| `test_count` | integer | Yes | Number of evaluated test messages |
| `tp`, `tn`, `fp`, `fn` | integer >= 0 | Yes | Confusion matrix cells |
| `accuracy`, `precision`, `recall`, `f1`, `false_positive_rate` | float | Yes | Rates in [0,1] |
| `zero_division_policy` | string | Yes | Set undefined precision/recall conventions explicitly |
| `test_ids_hash` | string | Yes | Same for both models |

Rules: `tp+tn+fp+fn=test_count`; `accuracy=(tp+tn)/test_count`; and all saved model metrics reconcile against confusion counts (with documented zero-denominator policy). The evaluation file contains results **only after real training**, not fabricated scores.

## 8. API-view schemas (not persisted)

### `ProbabilityWordResult`
`word`, `scope`, `total`, `counts{spam_present, spam_absent, ham_present, ham_absent}`, `probabilities{p_spam, p_word, p_spam_and_word, p_word_given_spam, p_spam_given_word}`, `notes`.

### `HypothesisTestResult`
`word`, `scope`, `observed`, `expected`, `null_hypothesis`, `alternative_hypothesis`, `test`, `chi_square`, `degrees_of_freedom`, `p_value`, `alpha`, `assumptions_satisfied`, `warnings`, `reject_null`.

### `PredictionResult`
`input{character_count,recognized_token_count}`, `models{multinomial,bernoulli}`, `agreement`, `warnings`. Each model contains `prediction`, `spam_probability`, `top_contributions[]`; Bernoulli additionally reports absent-term handling.

These schemas must match `API_CONTRACT.md`. API responses should use aggregate data or in-memory inference, not raw email records.

## 9. Storage layout

```text
data/
  raw/                  # official tar.bz2 downloads; gitignored
  processed/
    messages.csv        # gitignored; includes textual email content
    source_manifest.json
    split_manifest.json
artifacts/
  models/
    multinomial.joblib
    bernoulli.joblib
    vectorizer.joblib
    metadata.json
  reports/
    evaluation.json
```

## 10. No database / no user entity

MailSense v1.0 has no `users`, `sessions`, `roles`, `workspaces`, stored predictions or SQL migrations. There are no foreign-key enforcement requirements. File consistency checks and manifest IDs replace relational constraints; do not implement a database solely for this project.

## 11. Data provenance and rights

Original corpus description: `https://spamassassin.apache.org/old/publiccorpus/readme.html`. It warns against sending corpus mail to live systems and notes copyrights in original message texts belong to senders. Keep extracted emails off public repos, avoid displaying personal addresses unnecessarily, and cite the dataset in the university report.
