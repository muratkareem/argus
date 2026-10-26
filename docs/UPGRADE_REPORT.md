# ARGUS enterprise analyst upgrade

Delivered 26 October 2026 in the existing repository, without rebuilding or
replacing the academic core. All original research data and model/report
fingerprints were preserved during activation and read-only QA.

## Implemented experience

- Command Center with linked charts, risk-range exploration and recent cases.
- Advanced transaction query builder, persistent saved views and matching exports.
- Resizable investigation queue/timeline/evidence panes with source/model context.
- Recorded field/link events, notes, decisions and dated evidence reports.
- Actual record search, keyboard command menu, focus containment and density controls.
- Synthetic graph neighborhoods, relationship filters, structural cues and case links.
- Bounded evidence Copilot with structured citation-ID validation and explicit note save.
- Original flat enterprise design; real screenshots reviewed and iterated.

## Screenshots from the working application

[Command Center: original ULB PostgreSQL workspace](screenshots/overview.png) ·
[Transaction Intelligence: ULB records](screenshots/transactions-upgrade.png) ·
[Investigation Workbench: synthetic QA case](screenshots/investigation-upgrade.png) ·
[Graph: independent synthetic fixture](screenshots/graph-upgrade.png) ·
[Live qwen2.5:7b over synthetic evidence](screenshots/copilot-upgrade.png) ·
[Mobile full-data Command Center](screenshots/overview-mobile.png).

## Actual verification

23 backend tests passed on SQLite and PostgreSQL; 3 component tests passed;
11 Playwright workflows passed; lint/typecheck/build passed. Real qwen2.5:7b
was verified through both API and browser, including read-only generation,
known source IDs and explicitly labeled note save. API tests remain independent
of installed models and private datasets.

Full-data checks used the preserved 284,366-record PostgreSQL workspace, verified
query/export parity, source search, graph traversal, SHAP, Laboratory and mobile
layouts. Fingerprints matched for original stored transactions, CSV, active model
and both ULB reports. See [preservation evidence](research/upgrade-preservation.json),
[full-data observations](research/full-workspace-upgrade-check.json),
[local model API proof](research/ollama-integration.json), and
[browser proof](research/ollama-ui-verification.json).

Code revision 9bef4c4 passed all four GitHub Actions jobs, including Chrome
browser workflows and Docker Compose startup:
https://github.com/muratkareem/argus/actions/runs/40353906621.
Final delivery documentation receives the same pipeline. The browser job now
uses the hosted image's explicitly version-printed Chrome, avoiding a stalled
external provisioning step without skipping tests.

## Meaningful commits created

| Commit | Implemented logical improvement |
|---|---|
| [`3c458a8`](https://github.com/muratkareem/argus/commit/3c458a8) | feat(ui): establish compact analyst workspace and keyboard navigation |
| [`f35bf3c`](https://github.com/muratkareem/argus/commit/f35bf3c) | feat(intelligence): persist saved queries, evidence links and case timelines |
| [`8463bd1`](https://github.com/muratkareem/argus/commit/8463bd1) | feat(transactions): add saved query builder and global record search |
| [`97e0163`](https://github.com/muratkareem/argus/commit/97e0163) | feat(investigations): add resizable evidence workbench and audit timeline |
| [`8f5449e`](https://github.com/muratkareem/argus/commit/8f5449e) | feat(graph): add neighborhood exploration and investigation evidence links |
| [`7f60793`](https://github.com/muratkareem/argus/commit/7f60793) | feat(copilot): add bounded evidence context and validated local-model citations |
| [`b262e72`](https://github.com/muratkareem/argus/commit/b262e72) | feat(ui): connect Command Center exploration and grounded investigation Copilot |
| [`d5c2529`](https://github.com/muratkareem/argus/commit/d5c2529) | fix(ui): recover invalid queries without displaying stale evidence |
| [`93eea22`](https://github.com/muratkareem/argus/commit/93eea22) | ci: run browser verification with the hosted image Chrome channel |
| [`87869bc`](https://github.com/muratkareem/argus/commit/87869bc) | fix(ui): preserve readable large-value KPIs on narrow screens |
| [`9bef4c4`](https://github.com/muratkareem/argus/commit/9bef4c4) | fix(api): keep investigation timestamps timezone-consistent across databases |

The final documentation/screenshot delivery follows these implementation commits.
All commits are ordinary verified fast-forward commits; no empty/backdated commits,
force pushes or history rewrites were used.

## Preserved scientific scope and limits

Logistic Regression, Random Forest, XGBoost, reproducible splits, PR-AUC/AP,
precision/recall/F1, SHAP, model versions and provenance are unchanged. Synthetic
graph entities never imply ULB relationships. Scores are uncalibrated. Copilot
citations identify supplied records but do not guarantee factual correctness.
No authentication, multi-user isolation, production banking assurance or PDF
reporting is claimed. See [implementation status](IMPLEMENTATION_STATUS.md)
and [design research](UX_RESEARCH.md) for details and restart commands.

Final timeline QA normalized timezone-free SQLite timestamps to explicit UTC at
the API boundary; PostgreSQL timestamps use the same representation. Stored values
were not rewritten. The regression suite now has 23 tests on each database, and
the original full-data case/record fingerprints were verified again.
