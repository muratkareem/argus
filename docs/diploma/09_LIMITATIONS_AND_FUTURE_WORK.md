# Limitations and future work

ULB is a historical, anonymized dataset with small positive counts and limited context. Single-seed holdouts do not establish modern banking performance. Chronological results differ from stratified results; concept drift and external validation remain unresolved. Temporal holdout and repeated validation across seeds should precede stronger claims.

False positives cost analyst effort and false negatives miss labeled fraud. Validation F1 is only one policy; assumed FP 1/FN 25 cost profiles are illustrative. Class-weighted scores are uncalibrated; deployment would require independent calibration and monitoring under actual prevalence. SHAP describes statistical contributions, not causes or transaction legitimacy.

Only one active model is supported. Batch activation races fail atomically rather than silently mixing models. CSV parsing still materializes a validated dataframe; large exports and some investigation lists remain materialized and can grow. Query/overview benchmarks use10k synthetic rows, concurrency 1; full-dataset/concurrent API/browser timing remains unverified. Cached SHAP is bounded, but cold SHAP costs and varying model sizes need broader measurement.

Joblib requires trusted local files. Optional shared API key lacks per-user authorization, revocation/audit identity and production TLS/rate controls. Anonymous transactions still merit private handling. This system makes no PCI/privacy-law/regulatory compliance or banking effectiveness claim. Review publisher licensing before reuse; do not commit data or credentials.

Prioritized future work: independent multi-seed validation and calibration; query/export scaling measurements; safe dependency advisory updates; production identity/access and monitoring only if deployed beyond private demonstration. Additional infrastructure is not justified by current measurements.
