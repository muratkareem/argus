# Experimental results

Completed runs on14 November2026, Python3.12.16/macOS arm64,10 logical CPUs, two estimator threads. Full reports preserve versions, parameters, dataset audit, curves, calibration, threshold profiles and environment. The two training jobs ran concurrently; their latency/training times are not isolated hardware benchmarks. No training was repeated during recovery.

|Split|Algorithm|Precision|Recall|F1|AP|ROC-AUC|Confusion matrix TN,FP;FN,TP|
|---|---|---:|---:|---:|---:|---:|---|
|stratified|Logistic Regression|0.8875|0.7474|0.8114|0.7309|0.9670|[[56642, 9], [24, 71]]|
|stratified|Random Forest|0.9200|0.7263|0.8118|0.8389|0.9757|[[56645, 6], [26, 69]]|
|stratified|XGBoost (selected)|0.9474|0.7579|0.8421|0.8069|0.9793|[[56647, 4], [23, 72]]|
|chronological|Logistic Regression (selected)|0.9423|0.6622|0.7778|0.7475|0.9818|[[56669, 3], [25, 49]]|
|chronological|Random Forest|0.8871|0.7432|0.8088|0.8124|0.9546|[[56665, 7], [19, 55]]|
|chronological|XGBoost|0.9123|0.7027|0.7939|0.7834|0.9804|[[56667, 5], [22, 52]]|

XGBoost wins stratified validation AP, while Logistic Regression wins chronological validation AP. A higher test AP for another model is not grounds to reselect on the test set. Small positive test counts and temporal shifts limit generalization. ROC/PR/calibration points are preserved in the JSON and rendered by the Laboratory.

## API benchmarks

Warm in-process FastAPI TestClient, concurrency1,10,000 synthetic rows, same model artifact, three warmups and50 samples (SHAP15). Includes HTTP serialization/validation; excludes TCP/TLS and browser rendering.

|Operation|Baseline p95 ms|Current p95 ms|
|---|---:|---:|
|health|0.880|1.284|
|prediction|2.259|5.419|
|transactions|6.835|2.226|
|overview|13.824|10.196|
|shap_on_demand|4.014|5.723|

Current1000-record batch API p95 32.707ms. Query/overview improve; strict schema validation and request boundaries increase single/SHAP latency. All measured API targets are met only for these conditions, not proven for full-dataset load or concurrent clients. Current process peak RSS267.9MiB includes setup/imports; baseline includes training, so RSS reduction cannot be attributed solely to implementation.

The isolated ingestion benchmark uses a fake vector predictor and tracemalloc:60k rows20.335→15.068s,264.012→55.947MiB peak Python allocations. These single trials isolate ingestion and do not measure real model throughput. Raw results/methodology are in ../research/ingestion-{baseline,optimized}.json. Browser initial-load timing and full-dataset/concurrent performance remain unmeasured.
