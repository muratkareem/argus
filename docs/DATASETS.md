# Datasets and provenance

## ULB benchmark (official authorized source)

Source: [Kaggle / mlg-ulb creditcardfraud](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud).
The source describes 284,807 transactions, 492 frauds, anonymized V1–V28,
Time, Amount, and binary Class. Verify the current source terms yourself before
access, publication, or redistribution. No source data is committed here.

The official download was publicly accessible on 26 October 2026. The helper
`uv run python scripts/download_ulb.py` downloads only from that route, checks ZIP
content and size, writes a fixed destination, refuses overwrite, and records the
CSV SHA-256. If access is unavailable, it stops without using a mirror or bypass.
The full CSV is about 144 MiB; the bounded API upload limit is 192 MiB.

1. Review the source terms. Use the helper, or sign in to Kaggle and obtain
   `creditcard.csv` through the source's authorized download route.
2. Store it at `data/private/creditcard.csv` (ignored by Git). Do not put Kaggle
   credentials or downloaded archives in tracked folders.
3. From the repository root, train:

   ```sh
   PYTHONPATH=backend uv run python -m app.ml --csv data/private/creditcard.csv
   ```

4. Start the API, choose **Import dataset → ULB benchmark data**, then upload
   the same schema. Training and uploads are separate operations; importing
   labeled data does not train a model or make its dashboard metrics held-out.
5. For a temporal sensitivity run, use `--split chronological`. This creates a
   new experiment and activates its selected model; old stored scores retain
   their versions until explicitly rescored.

The schema permits Time and Amount in any column order; V1–V28 are required.
Class is required for training and optional for ingestion/inference. Numeric
finite values only; Time/Amount cannot be negative. Unexpected columns are
rejected rather than silently interpreted. Custom schemas need an explicit
future mapping implementation. Files are never saved under user-provided names.

## Synthetic transaction fixtures

`app.ml.synthetic` independently generates 28 normal features; a Bernoulli target
with p=.06 adds shifts to V4 (+2.8), V14 (−3.5), and V17 (−2.5). Sorted uniform
Time spans 172,800 seconds. Amount is lognormal and rounded to 2 decimal places.
This is an artificial classification problem, not a realistic ULB replacement.
Amounts have unspecified units; the UI does not invent a currency.

- Seed 42, 2,000 rows: training/validation/test fixture, generated locally.
- Seed 2026, 600 rows: independent demonstration, persisted by bootstrap.
- Seed 4401, 40 rows: `data/samples/synthetic-transactions.csv`, tracked under MIT.
- Tests use additional seeds and intentionally modified synthetic amounts.

Uploads explicitly declare `synthetic` or `ulb`. A model can only score data
with its own training provenance. Provenance is supplied by the analyst, not
cryptographically verified. Do not label real data synthetic to bypass the guard.

Duplicate fingerprints cover normalized feature values plus declared provenance,
not the filename or label. Identical rows within/across uploads are skipped;
subsequent uploads are not a mechanism for changing a stored label. An all-duplicate
upload records a dataset with zero new rows and its duplicate count.

## Separate relational graph

`seed_graph` creates six Accounts, six Cards, four Devices, three Merchants,
and twelve synthetic Transactions (31 entities, 36 relationships). Accounts 1–3
share Device 1; each account owns a card that initiates two transactions targeting
an artificial merchant. All entities and edges persist in relationship tables.

These graph transaction nodes are **not** ULB transactions or the scored synthetic
CSV records. No geographical, account, card, device, or merchant evidence is
inferred from anonymized ULB features. Graph entities and scored transactions support persistent case links, with
separate provenance. An analyst association does not establish a relationship
between a synthetic entity and an ULB transaction.


## Verified benchmark input

Actual official CSV: 150,828,752 bytes; SHA-256
`76274b691b16a6c49d3f159c883398e03ccd6d1ee12d9d8ee38f4b4b98551a89`.
Training removed 1,081 duplicate feature rows, including duplicated fraud records,
leaving 283,726 unique rows / 473 frauds. Derived reports and source metadata are
tracked under `docs/research/`; source CSV, archive and trained binaries remain
ignored. No full dataset is redistributed.

## Multi-dataset offline evaluation

The Laboratory's **Dataset** selector separates active workspace artifacts from
published ULB, IEEE-CIS and PaySim research. External benchmarks do not activate a
model, import transaction records, or change the ULB prediction/SHAP contract.
`GET /api/v1/benchmarks` serves completed reports and explicit access statuses;
`GET /api/v1/models` retains its original contract. `ARGUS_BENCHMARK_DIR` optionally
points to another server-owned research directory containing `benchmarks/*.json`.
Only completed experiment reports belong in that subdirectory.

| Dataset | Nature | Source size / positives measured here | Executed scope | Terms |
|---|---|---|---|---|
| ULB / Worldline | Real card transactions | 284,807 / 492 raw; 283,726 / 473 deduplicated | Existing full-data stratified and chronological reports reused | ODbL database / DbCL contents |
| IEEE-CIS / Vesta | Real e-commerce transactions | Not measured: official download requires authorization | Adapter and training integration fixture-tested; no real-data results | Competition rules, noncommercial academic use; rule acceptance required |
| PaySim | Synthetic mobile money simulation | 6,362,620 / 8,213 (0.1291%); 493,534,783 bytes | Seeded uniform 200,000-row sample / 241 positives (0.1205%); both split designs | CC BY-SA 4.0 |

### PaySim: official author-linked source

The [PaySim authors' repository](https://github.com/EdgarLopezPhD/PaySim) links to
[the canonical Kaggle dataset](https://www.kaggle.com/datasets/ealaxi/paysim1).
Its [official metadata](https://www.kaggle.com/api/v1/datasets/view/ealaxi/paysim1)
identifies **CC BY-SA 4.0**. This is a simulator dataset built from aggregate
patterns, not a second real credit card dataset. Attribution: E. A. Lopez-Rojas,
A. Elmir and S. Axelsson, *PaySim: A financial mobile money simulator for fraud
detection*, EMSS, 2016. See [license notices](DATASET_LICENSE.md).

The official source warns that detected frauds are canceled and **all four
balance fields must not be used for detection**. ARGUS therefore excludes
`oldbalanceOrg`, `newbalanceOrig`, `oldbalanceDest`, `newbalanceDest`, the policy
output `isFlaggedFraud`, and raw identifiers `nameOrig` / `nameDest`. Predictors
are `amount`, deterministic `log1p(amount)`, and one-hot encoded `type`. `step`
is the split clock (hours), not a predictor. The eleven-column raw schema is
required; IDs are used only in event deduplication signatures. Distinct payments
sharing amount/type are retained. No outcome-derived balance-error features are
constructed. This deliberately conservative baseline cannot be compared directly
with published experiments using those balance fields.

```sh
# Once only; ignored private directory, official route, bounded ZIP, no overwrite
uv run python scripts/download_paysim.py

# CPU-bounded reproducible sample; output refuses overwrite, no production activation
PYTHONPATH=backend uv run python -m app.benchmarks \
  --dataset paysim --csv data/private/paysim/paysim.csv --max-rows 200000 \
  --split chronological --output docs/research/benchmarks/paysim-chronological.json
PYTHONPATH=backend uv run python -m app.benchmarks \
  --dataset paysim --csv data/private/paysim/paysim.csv --max-rows 200000 \
  --split stratified --output docs/research/benchmarks/paysim-stratified.json
```

The published outputs already exist: do not rerun them just to start the app.
For a deliberate replication, choose a **new output filename** or an ignored
`.local/` output. Omitting `--max-rows` trains on the full source and can require
substantially more memory/compute; no full-source training claim is made here.
The sampler scans all records, assigns independent seed-42 random priorities,
retains the smallest 200,000, then restores source order. Sampling is independent
of label/time, without prevalence balancing. The full-source row/label counts,
SHA-256, sampling policy and per-partition counts are in every report.
[Download evidence](research/paysim-source.json) records the source CSV SHA-256
`16910f90577b0d981bf8ff289714510bb89bc71bff7d3f220f024e287e4eea6b`.

### IEEE-CIS: complete adapter, authorized data still required

Official [competition](https://www.kaggle.com/competitions/ieee-fraud-detection)
and [rules](https://www.kaggle.com/c/ieee-fraud-detection/rules). The rules permit
noncommercial research/education subject to their conditions. The official
competition API returned **HTTP 401** without credentials on 15 November 2026;
no account credentials/rule acceptance were available and no mirror or bypass
was used. [Access evidence](research/ieee-cis-access.json) has null metrics.

To unblock: sign in to Kaggle, join/accept the competition rules, use its Download
Data control (or your authorized Kaggle CLI), and store the extracted labeled
`train_transaction.csv` plus optional `train_identity.csv` in
`data/private/ieee_cis/`. Keep credentials outside Git. An authorized CLI example
(after separately installing/configuring Kaggle) is:

```sh
kaggle competitions download -c ieee-fraud-detection -p data/private/ieee_cis
# Extract the authorized archive locally; then:
PYTHONPATH=backend uv run python -m app.benchmarks \
  --dataset ieee_cis --csv data/private/ieee_cis/train_transaction.csv \
  --identity data/private/ieee_cis/train_identity.csv --max-rows 200000 \
  --split chronological --output docs/research/benchmarks/ieee-cis-chronological.json
# Repeat with --split stratified and a different output for sensitivity analysis.
```

The transaction table requires `TransactionID`, `TransactionDT`, `TransactionAmt`,
`ProductCD`, `isFraud`; official C/D/V numeric fields, card/address/email/M
categories, distances and optional device/identity features are supported.
Identity joins are left, one-to-one on unique nonmissing `TransactionID`; missing
identity records are allowed and imputed using training-only transformations.
Overlapping columns/duplicate IDs are rejected. TransactionID is never a predictor;
TransactionDT is used only for splitting. Only labeled competition training data
is split; Kaggle's unlabeled competition test is never treated as labeled evidence.
Review whether anonymized engineered fields would actually be available at the
operational decision time before extending research claims.
