# Calibration and generalization review

Review of the preserved experiments; no retraining or post-hoc test-based tuning. Scores are class-weighted predict_proba estimates, not calibrated real-world fraud risk.

|Split|Model|Test Brier score (lower better)|Validation threshold|FP|FN|
|---|---|---:|---:|---:|---:|
|stratified|Logistic Regression|0.021969|0.999999999243|9|24|
|stratified|Random Forest|0.000555|0.59972260081|6|26|
|stratified|XGBoost|0.001093|0.974755465984|4|23|
|chronological|Logistic Regression|0.023840|0.999992247612|3|25|
|chronological|Random Forest|0.000482|0.289237474564|7|19|
|chronological|XGBoost|0.003694|0.963408827782|5|22|

Logistic Regression's Brier scores around 0.022–0.024 are much worse than a constant predictor at the held-out prevalence (roughly 0.0017 stratified and 0.0013 chronological). Its high ranking performance therefore does not establish calibrated probabilities. Very high validation thresholds are observed measurements, not evidence of near-certain fraud. Weighting the positive class changes the fitted probability scale. Forest Brier scores are lower, but no guarantee follows from a single aggregate number under extreme imbalance. Reliability curves are saved for all candidates; repeated probability values collapse quantile bins, so the forest curves have fewer bins than requested.

XGBoost is selected by stratified validation AP; Logistic Regression by chronological validation AP. Selected test recall changes from0.7579 to0.6622 across these protocols, while different time partitions contain different positive counts. This is a sensitivity result, not a causal comparison or confidence interval. AP and ROC-AUC measure discrimination; they do not certify calibrated risk. No new threshold/model/calibrator was chosen from the test metrics.

Deduplication precedes partitioning, identical-feature conflicting labels are rejected, StandardScaler fits only training data, class weights derive from training labels, and threshold/parameter/model selection uses validation only. The two-candidate search and repeated use of one validation partition can still overfit validation. Multi-seed confidence intervals, independently held-out calibration, external datasets, contemporary prevalence and concept-drift evaluation remain future work. Existing test sets must not be recycled as tuning sets.
