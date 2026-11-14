# Local development history

Branch: development/diploma-ready. Baseline: c7a4691. No remote push. The following implementation commits precede the final verification/checkpoint commit; use `git log c7a4691..HEAD` for the complete final history.

```text
00ea240 refactor(ui): remove generative assistant workspace and controls
0916a02 fix(db): enforce SQLite integrity and concurrent reader settings
2d1fd61 fix(ml): validate inference schema and complete evaluation metrics
92b049e feat(db): migrate legacy datasets and index explorer query patterns
67cd608 refactor: remove local language model services and API routes
dab6f75 feat(ml): report validation threshold and illustrative cost tradeoffs
f3c3f93 feat(ml): persist observed dataset audit and inference schema metadata
7140850 feat: add configurable prediction thresholds and validated outputs
8fd6c19 perf(ml): measure warm model latency before algorithm selection
1b4f536 perf: record reproducible ingestion allocation baseline
41160be perf: record reproducible API and explanation baseline
3f40695 feat: add bounded vectorized batch prediction API
4e57c9f feat: expose on-demand SHAP for submitted transactions
2f6832a feat(ui): add schema-based fraud prediction and SHAP workflow
02851f9 fix(ml): verify artifact integrity and atomically cache model activation
cbc565a perf(data): bound import allocations and enforce atomic validated ingestion
6de2892 perf: verify reduced import time and peak allocations
71966b2 feat(ui): visualize ROC calibration and validation threshold trade-offs
f308a2e test: verify obsolete language-model routes are unavailable
091b6f9 perf(ml): cache bounded SHAP explanations with exact output-space labels
285e2d6 feat: protect API access and sanitize request error boundaries
bf40df1 perf(graph): query bounded neighborhoods and count distinct account links
abbabe2 feat(ui): add system metadata and optional API key connection
43d05c6 test(ml): verify reproducible training and concurrent artifact activation
c75203a perf(ui): defer graph engine loading until investigation navigation
3a5583b test(ui): discover API utility regression tests
bfa7d31 perf: bound dataset rescoring and offload CSV processing
64a5434 fix(api): validate finite analyst filters and literal search text
b137477 docs(ml): explain calibration diagnostics, latency and artifact trust
8764eb1 feat: expose model readiness and verified system metadata
1c115fd fix(data): reject model changes during atomic concurrent imports
a46391c fix(graph): report truncation when a deeper expansion exceeds the node limit
7cd8ed0 test(e2e): verify direct prediction SHAP and validation threshold workflow
f75cdff style: align ML modules with the configured formatter
855fcd3 docs: preserve completed ULB experiment results and source evidence
239fb89 test: preserve refreshed analyst workflow screenshots
bdc3789 docs: recover session checkpoint and prioritized continuation steps
29ba09b fix: migrate demo databases and preserve bootstrap idempotence
584ad39 docs: document diploma methodology results and requirement traceability
ec3ead9 docs: retire obsolete language-model instructions and evidence
03edbe9 feat: distinguish observed fraud labels from dashboard review flags
```
