# Next session priorities

Core implementation and private diploma demonstration are verified. Read PROGRESS.md, then inspect git status/log; keep development/diploma-ready and never push without authorization.

1. Use existing dataset/artifacts; do not repeat completed experiments or download. For a demo reuse .local/e2e.db/.local/e2e-artifacts with matching environment, or follow docs/diploma/07_DEPLOYMENT_GUIDE.md for clean native setup.
2. Review publisher dataset license terms and document the exact license/version; raw data is currently not redistributed.
3. Address nine moderate development-tool dependency advisories with compatible package updates; rerun frontend lint/typecheck/unit/build/browser tests. Avoid force/downgrade without checking compatibility.
4. If expanding research scope, run independent multi-seed/temporal validation and calibration with a new explicit experiment plan; existing test partitions must not become tuning data.
5. If pursuing broader performance claims, benchmark full dataset/concurrent HTTP and browser initial-load timing. Current concurrency-one results and allocation evidence are already saved; do not claim universal target compliance.
6. Consider bounded exports/case-list pagination and global SHAP summary if measured requirements justify them. The optional duplicate-audit prototype is not implemented.
7. Maintain focused verified local Conventional Commits and update checkpoint/results when behavior changes. No current core workflow blocker remains; production deployment remains outside the verified research scope.
