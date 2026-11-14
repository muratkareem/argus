# Dependency security review

14 November 2026: compatible npm audit fix updated ESLint10.13.0→10.15.0, config-array0.23.5→0.23.6 and typescript-eslint8.72.0→8.72.2. No forced downgrade/override or major direct dependency upgrade was used. Nine moderate findings reduced to seven. Production-only npm audit reports zero vulnerabilities; full audit reports seven moderate, zero high/critical. Results are point-in-time registry findings, not a security guarantee.

|Affected package after update|Scope|Reason/action|
|---|---|---|
|@typescript-eslint/eslint-plugin|Development only|Transitive exposure through typescript-eslint/minimatch; compatible direct update applied, remaining range needs upstream compatibility fix.|
|@typescript-eslint/parser|Development only|Transitive exposure through typescript-eslint/minimatch; compatible direct update applied, remaining range needs upstream compatibility fix.|
|@typescript-eslint/type-utils|Development only|Transitive exposure through typescript-eslint/minimatch; compatible direct update applied, remaining range needs upstream compatibility fix.|
|@typescript-eslint/typescript-estree|Development only|Transitive exposure through typescript-eslint/minimatch; compatible direct update applied, remaining range needs upstream compatibility fix.|
|@typescript-eslint/utils|Development only|Transitive exposure through typescript-eslint/minimatch; compatible direct update applied, remaining range needs upstream compatibility fix.|
|minimatch|Development only|Affected minimatch10.2.6 transitive dependency; patched major11 is outside its parent dependency range. No forced override.|
|typescript-eslint|Development only|Transitive exposure through typescript-eslint/minimatch; compatible direct update applied, remaining range needs upstream compatibility fix.|

The two resolved findings were ESLint and @eslint/config-array, now using fixed minimatch11 through their own supported ranges. Remaining seven are minimatch, typescript-eslint, @typescript-eslint/eslint-plugin, parser, type-utils, typescript-estree and utils. The underlying [GHSA-g3hv-75wg-m249](https://github.com/advisories/GHSA-g3hv-75wg-m249) concerns glob pattern amplification. These tools run during development/linting and are not served in the Nginx production bundle. Do not process untrusted lint/glob configuration; apply a compatible upstream fix when available. npm suggests a forced typescript-eslint8.36.0 change; that downgrade is not adopted. Frontend lint/typecheck,12 unit tests,build and12 browser workflows pass after updates.
