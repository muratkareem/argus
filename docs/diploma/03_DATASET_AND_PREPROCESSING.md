# Dataset and preprocessing

The authorized source is [ULB/Worldline on Kaggle](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud). Source metadata and CSV checksum are preserved in `../research/diploma-ulb-source.json`; the dataset is not redistributed. Review the publisher's current license and usage terms before reuse; this implementation does not grant dataset rights.

The downloaded CSV has 284,807 rows and 492 positive labels. Feature-identical deduplication removes 1,081 rows, leaving 283,726 transactions and 473 positives. The input consists of elapsed `Time`, transaction `Amount`, anonymized PCA components `V1`–`V28`, and binary target `Class`. There are no cardholder/merchant/account identifiers. Amount and time are nonnegative. Exact dtypes, missing values, amount quantiles, time bounds and class counts are recorded from execution in both experiment JSON reports under `dataset_audit`.

Missing/nonfinite numeric values and unsupported columns are rejected; no unreported imputation is performed. Identical features with conflicting labels are rejected. Deduplication precedes partitioning, preventing identical feature rows crossing splits. Logistic Regression uses a StandardScaler pipeline fitted on training data only. Trees do not require scaling. Class weights/scale_pos_weight derive from training labels; no resampling touches validation or test data.

Two seed 42 experiments use60/20/20 partitions. Stratified splitting preserves class proportions; chronological splitting keeps equal timestamps together and uses strictly ordered time ranges. Every partition must contain both classes. Each run has 170,235 training, 56,745 validation and 56,746 test rows. Stratified test contains 95 positives; chronological test 74. Partition fingerprints/time ranges are saved.

Raw data/artifacts stay in ignored local directories. Independent synthetic training seed 42 and demo seed 2026 support software demonstrations only. Uploaded provenance is user-declared and cannot authenticate an arbitrary file as the official dataset.

License review completed: the official source specifies ODbL database / DbCL contents licensing. See [dataset attribution and conditions](../DATASET_LICENSE.md); research and demonstration use must preserve the applicable source/license notices. Raw data is not redistributed. This supersedes the earlier pending-license checkpoint.
