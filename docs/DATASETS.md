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
inferred from anonymized ULB features. Graph entity case-linking is planned;
scored transactions already support persistent investigation links.


## Verified benchmark input

Actual official CSV: 150,828,752 bytes; SHA-256
`76274b691b16a6c49d3f159c883398e03ccd6d1ee12d9d8ee38f4b4b98551a89`.
Training removed 1,081 duplicate feature rows, including duplicated fraud records,
leaving 283,726 unique rows / 473 frauds. Derived reports and source metadata are
tracked under `docs/research/`; source CSV, archive and trained binaries remain
ignored. No full dataset is redistributed.
