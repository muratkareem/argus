# ML methodology

Research topic: Development of a Machine Learning System for Credit Card Fraud
Detection Using Transaction Data.

## Source and validation

The intended benchmark is the [ULB / Worldline credit card fraud dataset](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud).
The official public Kaggle download was successfully retrieved on 26 October
2026 without credentials. The CSV stays in ignored `data/private/`; no mirror or
access bypass was used. This repository publishes derived evaluation reports
and source checksum metadata, not the dataset.

Features are `Time`, `V1`–`V28`, `Amount`; target `Class` is binary. Training
rejects absent/extra columns, nonnumeric/missing/nonfinite values, negative
Time/Amount, and invalid target values. Feature-identical rows with conflicting
labels are rejected. Other feature-identical duplicates are removed before
splitting. Reports record counts, SHA-256 of the normalized dataset, partition
sizes and fraud counts, partition index digests, seed, parameters, environment,
versions, and duration. SHA-256 here is a reproducibility identifier, not a
privacy mechanism.

## Reproducible comparison

1. Seed 42; initial split is stratified 60% train / 20% validation / 20% test.
2. Logistic Regression uses a training-fitted StandardScaler, class-balanced
   loss, and C candidates `{0.1, 1.0}`.
3. Random Forest uses 100 trees, balanced subsample weights, minimum leaf size 2,
   and depth candidates `{6, 12}`.
4. XGBoost uses 100 histogram-boosted trees, learning rate .08, subsample and
   column subsample .9, training-only negative/positive weight, and depths `{3,5}`.
5. Each algorithm selects its parameter candidate using **validation AP**.
6. Its decision threshold maximizes F1 on the validation precision-recall curve.
   This is a research tradeoff, not a calibrated operational fraud-cost policy.
7. The winning algorithm is selected by validation AP **before** test evaluation.
8. Each winning candidate receives one final evaluation on the untouched test
   partition. Reading the test results must not be used to retune the same run.
9. Serialize only the selected fitted model, preprocessing, threshold, provenance,
   background sample for SHAP, and version. Save all three evaluation reports.

No preprocessing is fitted on validation/test data. No SMOTE or preprocessing
is applied across split boundaries. Class weighting avoids synthetic resampling
and keeps the MVP practical on a 16 GB laptop. This small validation grid is
intentional; it is not an exhaustive optimization study.

Run with `--split chronological` for a separate sensitivity experiment. Equal
timestamps remain in one partition: first ~60% train, next ~20% validation, final
~20% test. All partitions must contain both classes. Two days of anonymized ULB
activity cannot establish stability across months, account groups, or merchant
segments. Stratified results assume exchangeability and can overestimate future
performance; temporal results can be unstable with few positives. Neither split
supports grouped-by-account validation because account IDs are absent.

## Metrics and interpretation

Saved metrics: precision, recall, F1, average precision (reported as PR-AUC/AP),
ROC-AUC, confusion matrix in `[[TN, FP], [FN, TP]]` order, false-positive rate,
and sampled precision-recall points. AP uses scikit-learn's average precision,
not trapezoidal integration of the PR curve. These are distinct definitions.

With ~0.17% ULB fraud, predicting every transaction legitimate produces very
high accuracy and zero fraud recall. Accuracy is deliberately not the headline
metric. Precision changes with prevalence; synthetic fixture prevalence is 6%,
so its precision cannot be extrapolated to the ULB prevalence. Report threshold,
positive counts, and provenance alongside scores.

A `predict_proba` output is called an **uncalibrated model score**, especially
because class weighting changes the effective training distribution. No claim
of calibrated real-world fraud probability, operational savings, or causal
explanation is made.

## Explainability

SHAP LinearExplainer explains standardized logistic log-odds using training
background. TreeExplainer explains XGBoost raw margins/log-odds and forest
positive-class probability. All 30 attributions and their base value are
returned, and the UI shows the largest absolute contributions. Automated tests
check that contributions reconstruct each algorithm's output in its proper
space. Global importance is absolute standardized coefficient magnitude or
estimator tree importance, with scales that must not be compared across models.

V1–V28 are anonymized components. They do not justify claims about location,
merchant, device, cardholder behavior, or an actual fraud cause. The separate
synthetic graph does not enrich or explain ULB predictions.

## Current research evidence

`docs/research/synthetic-evaluation.json` is a saved **actual run on artificial
fixtures**, not an ULB benchmark. Training uses generator seed 42 (2,000 rows).
The interactive demonstration uses independent seed 2026 (600 rows). The checked
sample upload uses seed 4401 (40 rows). These fixtures deliberately contain
learnable feature shifts and are useful for software verification only.

The ML Laboratory reads server-owned report JSON; it never synthesizes metrics.
Repeated runs retain versions; scores are reproducible with the locked dependency
versions and seed, allowing for platform floating-point differences. Timestamps
and measured durations will vary. Confidence intervals, calibration, broader
search, external validation and drift monitoring remain future research work.


## Actual ULB experiments (26 October 2026)

Official input: 284,807 rows; 1,081 duplicate feature rows removed; 283,726 unique
rows including 473 frauds. Both experiments use the same normalized dataset hash.
Stratified train/validation/test fraud counts are 284/94/95; chronological counts
are 342/57/74. Chronological cutoffs keep equal timestamps together.

The stratified validation selection chose XGBoost: held-out precision .9474,
recall .7579, F1 .8421, AP .8069, ROC-AUC .9793. The chronological validation
selection chose Logistic Regression: held-out precision .9423, recall .6622,
F1 .7778, AP .7475, ROC-AUC .9818. Other candidates' test results are all retained;
a higher test AP did not retroactively change selection. These experiments are
single-seed estimates without confidence intervals or deployment validation.

See `docs/research/ulb-stratified-evaluation.json`,
`docs/research/ulb-chronological-evaluation.json`, and `ulb-source.json` for exact
measurements and provenance. Training completed in 26.456 and 27.327 seconds on
this host; this is one observation, not a performance guarantee.

The interactive database may include training, validation and test rows from an
imported full CSV. Dashboard labeled-data detection rate is therefore **not** an
unseen-test metric. Only the Laboratory's saved held-out reports support the
benchmark claims above. Synthetic and ULB score versions remain separately labeled.
