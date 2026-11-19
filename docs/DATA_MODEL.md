# MailSense — Data Model and Local Artifact Specification

**Version:** 1.6 · **Date:** 2026-11-19 · **Status:** Acquisition, parsing, retained records, split and trusted models/evaluation implemented; API/UI integration verified
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
| `files_seen` | integer >= 0 or null | Yes | Null until parsing; then regular message candidates, excluding directories and `cmds` |
| `files_accepted` | integer >= 0 or null | Yes | Null until parsing; then count before global deduplication |
| `files_rejected` | integer >= 0 or null | Yes | Null until parsing; then count rejected by parsing/validation |

The manifest envelope has `schema_version: 1`, `dataset_source`, official index
and README URLs, `selection_policy: "one_canonical_archive_per_group"`,
`checksum_origin: "locally_computed_sha256"` and an `archives` array containing
exactly one entry for each approved group. URLs, filenames and labels must match
the fixed canonical selection; timestamps are timezone-aware UTC.

Acquisition records all three parsing counters as explicit `null` with
`processing_status: "not_started"`. MSE-104 populates integer counts and
sets `complete`; `files_seen = files_accepted + files_rejected` then applies.
This lifecycle clarification avoids reporting fabricated zero counts before
any message has been parsed. Archive byte sizes are measured independently of
email record counts. No cleaned/retained total is established by acquisition.

**Archive selection rule:** Select a coherent latest collection per group. For example, `20030228_easy_ham`, `20030228_easy_ham_2`, `20030228_hard_ham`, `20030228_spam`, and `20050311_spam_2`. Older date-prefixed archives are snapshots/revisions, **not additional independent groups**. Record exact versions/checksums at ingestion and verify official source before download. Untrusted tar members must not escape the extraction directory.

## 3. Entity `ProcessedEmail` (`data/processed/messages.csv`)

MSE-105 implements the frozen retained CSV without a split column. MSE-106's
verified ID join adds `split` to records in memory. MSE-104's ignored
`messages.parsed.jsonl` contains the same provenance
and text before deduplication, without token counts or splits. Both stages keep
sorted `parse_warnings`; JSONL stores an array and CSV a JSON-encoded array cell.
Parsing acceptance and post-deduplication retention are separate counts.

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
| `parse_warnings` | array of reason codes | Yes | Preserved from the selected parsed row; JSON array string in CSV |
| `split` | `train`/`test` | In joined records | Loaded from SplitManifest by ID; frozen CSV stays unchanged |

Rules:
- `model_text` cannot be blank after normalization; a blank-message record is rejected.
- `source_file` must be a safe relative path; never accept paths supplied to API.
- The combination of source group and original filename is **provenance only**, never a feature.
- `message_id` stays stable for identical canonical input and archive selection; split assignment saved separately and deterministic.
- If an identical normalized text appears under conflicting labels, exclude the conflicting group and log the count; do not leak duplicates across train and test or silently pick a label.
- Do not store model predictions as a new field on `ProcessedEmail`; predictions are computed on demand.
- The UI can inspect aggregates but should not expose complete raw source bodies as a browsing feature.

### Implemented parsing contract (`mime-v1`)

`message_id` is SHA-256 of the UTF-8 archive SHA-256, NUL, source group, NUL,
safe relative member name. Distinct provenance IDs may share content hashes at
this stage. `content_sha256` hashes the UTF-8 normalized `model_text`.
Normalize subject and body separately with Unicode NFC, replace control and
surrogate characters with spaces, collapse whitespace, and join nonempty
subject/body with one LF. `character_count` includes that LF.

Decode encoded subjects and MIME transfer encodings using the declared charset;
on failure try UTF-8, then Windows-1252 with replacement and warning codes.
Use the first subject when duplicated. Prefer nonblank plain text in
multipart/alternative; otherwise strip HTML to text. Related MIME uses its
declared root or first part; mixed MIME combines inline text. Ignore named
parts, attachment dispositions and message/* parts. HTML scripts, styles,
head/template/embedded objects and resource attributes contribute no text;
the parser never renders, executes or fetches resources. Transport headers and
source metadata never enter `model_text`.

Severe MIME structural defects (including missing separators or multipart
boundaries), empty text and exceeded message limits reject the whole candidate.
Other defects and decoding fallbacks produce fixed warning codes. This
conservative policy can exclude some partially readable historical mail.

### Parsing report (`data/processed/parsing_report.json`)

The shareable report pins schema version 1, stage
`parsed_before_deduplication`, parser/runtime versions, all resource limits,
private JSONL path, byte size and SHA-256. Per archive it records members,
ignored directories/control files, candidates/accepted/rejected, warning and
rejection counts, and rejected hashed IDs with reason codes. It contains no
message text, addresses or per-message filenames. Warnings count accepted
messages having that warning, not occurrences within a message.

For each source, candidates = accepted + rejected. Archive members equal
candidates plus ignored directories and ignored metadata files. Global totals sum the five
sources. `verify` rechecks source hashes, private record IDs/text hashes,
normalization, warnings, output digest and all report/manifest counts. A
`complete` source status means parsing completed, not deduplication or readiness
for training. Current measured totals are 6,046 candidates, 5,992 accepted,
54 malformed-MIME rejections, five ignored directories and five ignored `cmds`.

### Implemented retained dataset (`exact-text-v1`)

Group by `content_sha256` and check actual `model_text` equality within each
group; a hash collision aborts. If a group has both labels, exclude all its
rows, including any repeats within either label. Otherwise retain the smallest
lexicographic `message_id` and exclude the remaining same-label duplicates.
Comparison is exact after `mime-v1` normalization, preserving case and
punctuation. Approximate/near-duplicate detection is outside this stage.

The representative keeps all original provenance/text/hash/character-count and
warning fields. `token_count` uses the fixed `unicode-word-v1` definition in
[STATISTICAL_METHODS.md](STATISTICAL_METHODS.md#canonical-tokenization-unicode-word-v1),
without fitting any vocabulary. Nonblank records with zero tokens are retained.
CSV rows sort by `message_id`, use fixed header order, UTF-8, LF record endings
and standard CSV quoting. Embedded model-text LF is preserved; warnings use a
compact JSON array cell. CSV readers must support fields up to the parser's
1,000,000-character bound. The ignored file has owner-only permissions.

### Deduplication report (`data/processed/deduplication_report.json`)

Schema version 1, stage `retained_before_split`, pins the parser/deduplication/
tokenizer configuration, Python runtime, input file hashes/sizes and CSV output
hash/size. `dataset_id` hashes UTF-8 compact sorted-key JSON containing
`schema_version`, `preprocessing_version`, `deduplication_version`,
`representative_policy`, `tokenizer` and `records_sha256`. Thus dataset identity
depends on canonical retained records/configuration, not input row ordering or
run time; input serialization changes are separately pinned by the report.

The report includes parsed input/retained class counts, per-source counts,
duplicate/conflicting group counts and every excluded hashed ID/content hash,
reason and retained representative ID (`null` for label conflicts). It contains
no message text, per-member filenames or addresses. All original provenance is
recoverable locally from the unchanged parsed records and this ID mapping.
Parse exclusions remain in the parsing report; `parse_rejections` references
their count without mixing them into deduplication denominators.

`input_records = retained_records + duplicate_records_excluded +
conflicting_records_excluded`, globally and per source. Conflict exclusions
take precedence and are not double-counted as duplicates. Class counts sum to
retained records. `verify` rederives selection, exact CSV bytes, complete report
and dataset identity from verified parser inputs. Missing/changed inputs,
tampered output or unknown report fields fail verification. Publication shares
the preparation lock and rollback helper; an abrupt interrupted artifact set
requires verification/rerun. Current measured retention is 5,862 of 5,992 rows:
4,107 ham, 1,755 spam, 130 duplicate exclusions in 96 groups, zero label conflicts.

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

### Implemented split contract (`stratified-v1`)

Sort verified retained records by `message_id`, then call
`train_test_split(test_size=0.2, random_state=42, stratify=labels, shuffle=True)`.
Sort each resulting ID list before persistence. Test size is `ceil(0.2 × N)`
and train takes the remainder; class allocation uses the pinned sklearn
stratifier's integer allocation. Both classes must have at least two records
and appear in both resulting partitions. Empty, single-class, too-small or
extremely imbalanced inputs fail with `insufficient_class_support`; fractions
and seed are never silently changed. Ordering at the caller does not change
membership after canonical sorting.

The manifest additionally records `schema_version: 1`, `split_version`,
algorithm, shuffle/order/rounding policies, Python/NumPy/sklearn runtime versions,
tokenizer configuration, every upstream input file's SHA-256/size,
`total_records`, `train_records`, `test_records` and `total_counts`.
`train_ids_sha256`/`test_ids_sha256` hash sorted IDs encoded as UTF-8, one per
line, each including a trailing LF. `split_id` hashes compact sorted-key JSON
of schema/split/dataset/configuration/runtime/parser/tokenizer fields plus both
sorted membership lists; it excludes input provenance hashes and derived
counts/list digests. The identity keys are `schema_version`, `split_version`,
`dataset_id`, `seed`, `train_fraction`, `test_fraction`, `stratified_by`,
`shuffle`, `canonical_order`, `algorithm`, `rounding_policy`, `runtime`,
`preprocessing_version`, `tokenizer`, `train_ids` and `test_ids`.

Publication uses the shared preparation lock and rollback helper. Manifest
reads/writes are bounded to 16 MiB; unknown fields, wrong types/config/runtime,
altered membership/counts/hash or stale inputs fail complete rederivation.
The artifact contains only metadata and hashed IDs, never text or per-message
filenames. A standalone manifest does not prove readiness without local verified
upstream files.

`corpus_dataset.load_dataset(root)` returns freshly rederived typed retained
rows and their verified report, after checking the exact CSV hash against those
rows. `corpus_split.load_split_dataset(root, scope="all")` returns fresh rows
with split joined by ID and the verified manifest; `train`/`test` scopes filter
membership. This avoids rewriting the frozen CSV or duplicating private text.
All consumers must use the verified split join before fitting training features.

Observed counts: train 4,689 (3,285 ham, 1,404 spam), test 1,173 (822 ham,
351 spam). IDs are disjoint with complete retained coverage and no shared exact
content hashes. Dataset identity stays unchanged from MSE-105.

## 5. Entity `Vocabulary` (serialized with trained preprocessing pipeline)

| Field | Type | Required | Notes |
|---|---|---|---|
| `token_to_index` | map[string,int] | Yes | Learned on train only |
| `tokenizer_config` | object | Yes | Case-folding, regex/tokenization, stopword policy |
| `vocab_size` | integer >= 1 | Yes | Number of retained features |
| `min_df` | integer | Yes | Default `1`, documented in training config |
| `ngram_range` | pair | Yes | v1.0 default `(1,1)` unigrams |

MSE-301 implements `model_features.build_features` on verified split rows. The shared vectorizer has 60,135 training-derived features for this corpus; its hash and IDs are verified without committing the learned vocabulary. Training fits a single `CountVectorizer` on training text; MultinomialNB consumes count vectors and BernoulliNB consumes binary presence (`counts > 0`). Both thus share feature names and train/test boundaries. BernoulliNB's score additionally accounts for absence of known features.

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

MSE-304 implements fixed local `vectorizer.joblib`, `multinomial.joblib`, `bernoulli.joblib` and `metadata.json` under ignored `artifacts/models/`, all owner-only. The metadata envelope carries schema/pipeline/runtime, UTC training time, dataset/split/membership/input hashes, shared feature configuration/hash and per-model descriptors. `artifact_id` hashes the full canonical payload excluding its own ID and timestamp. Identical deterministic retraining reuses the original verified artifacts and timestamp. Binary files are bounded to 64 MiB, metadata to 128 KiB; all hashes are checked before deserializing the exact verified bytes. Loaded estimator types/classes/feature dimensions/priors and vectorizer configuration must agree. Staged publication rolls back ordinary failures. Checksums detect corruption; they do not authenticate an untrusted pickle.

Model files serialized using joblib/pickle must be loaded **only from project-created, trusted local artifacts**; never load uploaded/untrusted pickle files. Fail safely if expected metadata/checksum mismatch.

## 7. Entity `ModelEvaluation` (`artifacts/reports/evaluation.json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `model` | enum | Yes | `multinomial` / `bernoulli` |
| `dataset_id` | string | Yes | Same source for both models |
| `split_id` | string | Yes | Same held-out test IDs |
| `positive_class` | string | Yes | Always `spam` |
| `test_count` | integer | Yes | Number of evaluated test messages |
| `confusion_matrix{tp,tn,fp,fn}` | integer >= 0 | Yes | Confusion matrix cells |
| `accuracy`, `precision`, `recall`, `f1`, `false_positive_rate` | float | Yes | Rates in [0,1] |
| `zero_division_policy` | string | Yes | Set undefined precision/recall conventions explicitly |
| `test_ids_sha256` | string | Yes | Same for both models |

Rules: `tp+tn+fp+fn=test_count`; `accuracy=(tp+tn)/test_count`; and all saved model metrics reconcile against confusion counts (with documented zero-denominator policy). The evaluation file contains results **only after real training**, not fabricated scores.

MSE-305 writes the aggregate evaluation envelope with dataset/split/artifact/test-set identity, explicit positive class and a `models` map of per-model metrics. Ratios with zero denominators are `null` plus notes. Verification rederives predictions without fitting/tuning, uses the same sorted held-out IDs for both models and rejects stale/mismatched reports. No per-message predictions or text are published.

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
    messages.parsed.jsonl # implemented private intermediate; gitignored
    messages.csv        # gitignored; includes textual email content
    source_manifest.json
    parsing_report.json # implemented aggregate/hash diagnostics; shareable
    deduplication_report.json # implemented retained counts/hash exclusion ledger
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
