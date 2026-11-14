# Five-to-seven minute defense demonstration

Before presenting: run health/readiness, confirm active provenance/model version, run tests/build, open the workspace, and prepare a valid transaction. Use synthetic demo data with a synthetic model or authorized ULB data with its matching model; keep their claims separate.

1. **0:00–0:45 Architecture:** show the modular monolith diagram, offline training, database and inference boundary. State the diploma objective.
2. **0:45–1:30 Dataset:** show recorded source checksum/audit,30 input features, imbalance, deduplication and partitions. Explain anonymous components and absence of entity identities.
3. **1:30–2:20 Dashboard/explorer:** show actual stored aggregates, search/filter/page transactions and open a record. Distinguish observed labels and predicted review flags.
4. **2:20–3:20 Prediction:** enter/copy all30 valid feature values in Fraud Detection, select matching provenance and predict. Explain model/version, estimate, classification and threshold. Change threshold and show probability stays fixed.
5. **3:20–4:15 Explainability:** request SHAP on demand. Show positive/negative contributions and base value, state log-odds versus probability and reject causal interpretation.
6. **4:15–5:20 Evaluation:** open Laboratory for the active experiment; show AP/precision/recall/F1/confusion/ROC/PR/calibration and validation threshold costs. Compare the two saved ULB reports in docs/research; do not claim the UI loads reports from unrelated artifact directories automatically.
7. **5:20–6:30 Investigation/conclusion:** link suspicious evidence to a case and note analyst judgment. Present measured query/import performance and remaining false negatives. Synthetic graph is optional and separate. End with limitations and future work.

Avoid changing active artifacts mid-demonstration. Never imply synthetic graph fixtures establish relationships in ULB data.
