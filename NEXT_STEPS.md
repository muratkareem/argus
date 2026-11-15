# Multi-dataset research handoff — 15 November 2026

Completed implementation and measured results are recorded at the top of PROGRESS.md. Current work is directly on main with explicit push authorization; older branch/no-push instructions below are historical. Preserve existing ULB models and both PaySim reports. Do not rerun experiments or redownload datasets merely to resume.

1. Inspect `git status`, `git log -12 --oneline` and the GitHub Actions run for HEAD. All local gates passed: 95 tests on each database, 18 frontend tests, 16 browser workflows, lint/type/build/format and Compose/report proxy smoke. Initial verification failures were resolved; details/log locations are in PROGRESS.md.
2. IEEE-CIS is the only dataset-access blocker. Use authorized Kaggle login and competition-rule acceptance, then place labeled train_transaction.csv and optional train_identity.csv under ignored data/private/ieee_cis/. Follow docs/DATASETS.md exactly; no mirrors/private-label guesses. The adapter and three-algorithm training integration are already fixture-tested.
3. Before executing IEEE, predeclare sampling/feature availability/split plan. Run chronological evaluation, then a separately named stratified sensitivity report. Inspect raw/partition prevalence and CI limitations; do not retune based on the final test metrics. External runs write reports only and cannot replace active ULB models.
4. Any broader PaySim study should predeclare full-source or additional-seed evaluation and fresh assessment before execution. Current weak-recall results are intentionally retained; do not reintroduce prohibited balance/policy features to improve scores.
5. Research extensions such as time/entity-aware uncertainty, calibrated scores, grouped validation and true frozen-model cross-dataset transfer require separate defensible designs. No such claim is supported by current independently fitted benchmarks.
6. Preserve source/license attribution when sharing reports/figure. PaySim source is CC BY-SA 4.0; ULB ODbL/DbCL; IEEE competition restrictions apply. Raw sources, models, caches and credentials remain ignored.
7. Continue focused tested Conventional Commits and normal main pushes only within authorized scope. Source tests and published evidence must stay consistent; no artificial contribution inflation.

Historical handoffs follow.

# UI redesign handoff

The requested redesign is implemented and locally verified; do not repeat it. See docs/UI_REDESIGN.md and docs/screenshots/README.md for current behavior and before/after evidence.33 new full-page desktop/mobile images preserve the39-image baseline. Focus future work on user feedback, upstream development-tool advisories and the already documented research limitations. Current temporary capture helpers: .local/capture-redesign.mjs and .local/redesign-extras.mjs. Main publication and GitHub Actions are verified after the final commit. Historical follow-up follows.

# Post-delivery follow-up

Publication to main is explicitly authorized for the current delivery. Local final checks and real-data workflows passed; see docs/FINAL_DELIVERY.md. No dataset download or full ML experiment repetition is needed. Remaining work is research expansion and seven moderate development-tool advisories, not a core demonstration blocker.

# Next session priorities

Core implementation and private diploma demonstration are verified. Read PROGRESS.md, then inspect git status/log; keep development/diploma-ready and never push without authorization.

1. Use existing dataset/artifacts; do not repeat completed experiments or download. For a demo reuse .local/e2e.db/.local/e2e-artifacts with matching environment, or follow docs/diploma/07_DEPLOYMENT_GUIDE.md for clean native setup.
2. Dataset license review is complete: preserve attribution from docs/DATASET_LICENSE.md when presenting outputs; raw data is not redistributed.
3. Monitor the seven remaining moderate typescript-eslint/minimatch development-only advisories for an upstream compatible fix. ESLint fixes are applied; production audit reports zero. Avoid forced downgrade or major override.
4. If expanding research scope, run independent multi-seed/temporal validation and calibration with a new explicit experiment plan; existing test partitions must not become tuning data.
5. If pursuing broader performance claims, benchmark full dataset/concurrent HTTP and browser initial-load timing. Current concurrency-one results and allocation evidence are already saved; do not claim universal target compliance.
6. Consider bounded exports/case-list pagination and global SHAP summary if measured requirements justify them. The optional duplicate-audit prototype is not implemented.
7. Maintain focused verified local Conventional Commits and update checkpoint/results when behavior changes. No current core workflow blocker remains; production deployment remains outside the verified research scope.
