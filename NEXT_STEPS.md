# Resume checklist

1. Read PROGRESS.md; inspect git status/log. Keep development/diploma-ready. Never push without authorization.
2. Run focused/full tests on current code; resolve integration regressions. Do not repeat ULB training/download.
3. Run final full Playwright suite against preserved isolated synthetic workspace; review actual screenshots.
4. Measure optimized API with scripts/benchmark.py and same .local/baseline-models/10000-row fixture. Report regressions honestly, including validation overhead and methodology.
5. Fix bootstrap migration/idempotence, verify native startup and Compose using an isolated project/ports; preserve user databases and model files.
6. Remove obsolete generative documentation/assets; update README/API/architecture/status to current behavior.
7. Create all ten required docs/diploma files from measured evidence, including architecture, methodology, results, testing, deployment, 5–7minute demonstration, limitations and requirement traceability.
8. Review observed-vs-predicted overview semantics and optional API key browser integration. Inspect npm audit; apply only safe verified fixes.
9. Final lint/typecheck/unit/backend/browser/build/Compose checks, credential scan and git diff --check. Document exact blockers; avoid production-readiness claims.
10. Commit each verified logical change. Update PROGRESS.md/NEXT_STEPS.md and final report with commit count/log summary and remaining requirements.
