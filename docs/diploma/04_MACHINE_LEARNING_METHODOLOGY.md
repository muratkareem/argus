# Machine learning methodology

Logistic Regression estimates sigmoid(w·x+b), using regularization and balanced class weights. Random Forest averages randomized decision trees with balanced subsampling weights. XGBoost adds gradient-boosted trees with training-derived positive weighting. A fixed seed 42 and two estimator threads control repeatability; full package versions and fitted hyperparameters are stored.

Each algorithm has two parameter candidates: Logistic Regression C 0.1/1, forest depth 6/12, XGBoost depth 3/5. Candidates fit only the training partition. Validation Average Precision selects each algorithm's candidate. Validation F1 selects its classification threshold. The largest validation AP chooses the deployed algorithm; exact ties prefer measured single-prediction p95 latency. Test metrics are calculated after selection and never used to revise the winner. The held-out validation design is appropriate to this bounded search; repeated cross-validation and multi-seed confidence intervals remain future work.

Precision=TP/(TP+FP), recall=TP/(TP+FN), F1=2TP/(2TP+FP+FN), FPR=FP/(FP+TN), FNR=FN/(FN+TP). Average Precision summarizes precision/recall under imbalance; ROC-AUC is complementary. Confusion matrices use rows=true class, columns=prediction, legitimate first. Accuracy is not a selection criterion.

Validation threshold profiles illustrate recall/precision/F1, false-positive/negative counts and cost FP × 1 + FN × 25 in arbitrary units. These assumed costs are not banking loss estimates. Raising the threshold usually reduces flags and recall; request overrides change classification without changing the model estimate. Fixed display risk bands are low<0.1, medium<0.5, high<0.9 and critical≥0.9; the learned review threshold is independent.

Predict_proba returns an uncalibrated class estimate. Brier score and calibration curves assess its behavior; no post-hoc calibration is deployed or guaranteed. Training weighting and changing prevalence limit probability interpretation.

SHAP explains the selected fitted estimator, not causation: Logistic Regression/XGBoost contributions use log-odds; forest uses probability. Base plus contributions reconstructs the raw score; responses include reconstructed probability and numerical additivity error. Explanations are generated on demand, reuse explainers and occupy a 128-entry cache. Model-native global importance is reported separately from local SHAP; it must not be mislabeled global SHAP.

Trusted artifact activation writes immutable version directories and atomically replaces a manifest with checksum. Only server-owned artifacts may be loaded; joblib is unsafe for untrusted files. Checksum integrity does not authenticate a malicious replacement of both manifest and artifact.
