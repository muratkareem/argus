# ARGUS — real application screenshots

Captured on 14 November 2026 using Playwright with headless Google Chrome against the existing, running ARGUS application. These are browser screenshots, not mockups or generated images. No UI, feature, or application-logic changes were made.

- **Desktop:** 1440 × 900 viewport, device scale factor 1, full-page PNG.
- **Mobile:** 390 × 844 viewport, device scale factor 1, full-page PNG.
- Full-page image heights extend beyond the viewport. Transaction drawers and dialogs retain the application's native scrolling and viewport bounds; the direct-prediction SHAP images show the full result panel.
- **ULB views:** 993 already stored unique transactions from the first 1,000 source rows, scored with the existing XGBoost artifact `20261114T080308283241Z-6d0da1ed`. Laboratory charts use the preserved full stratified experiment, not a fresh evaluation on this displayed subset.
- **Investigation and graph:** existing saved cases and the separate synthetic relational fixture from the persisted demonstration workspace. These screenshots are explicitly labeled synthetic; no ULB identities or relationships are invented. The ULB investigation empty state is also included.
- Predictions/explanations were requested through the real API. No network responses were mocked, no records/cases/notes were created, no models were trained, and no CSV was uploaded during capture. The import dialog is shown without a selected file, and the system access-key field is empty.
- **Analytics coverage:** ARGUS has no standalone Analytics route. Dashboard activity/risk charts and Laboratory ROC, PR, calibration, confusion-matrix, feature-importance and validation-threshold/cost analysis are captured on their existing pages.

ULB attribution: Contains information from the Worldline/Université Libre de Bruxelles Machine Learning Group [Credit Card Fraud Detection database](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud), under [ODbL v1.0](https://opendatacommons.org/licenses/odbl/1-0/) with [DbCL v1.0](https://opendatacommons.org/licenses/dbcl/1-0/) contents. See [dataset license review](../DATASET_LICENSE.md). Estimates are uncalibrated; a flag is not a factual fraud determination.

## Latest captures — 30 images

Each link opens the full-resolution PNG. Expand the sections below for previews.

| Page or feature | Desktop | Mobile |
|---|---|---|
| Dashboard / transaction activity and risk distribution | [1440×1439](dashboard-ulb-desktop.png) | [390×2113](dashboard-ulb-mobile.png) |
| Transaction explorer / search, filters and pagination | [1440×1512](transactions-ulb-desktop.png) | [390×2249](transactions-ulb-mobile.png) |
| Transaction details / observed label and model output | [1440×1512](transaction-details-ulb-desktop.png) | [390×2249](transaction-details-ulb-mobile.png) |
| Stored transaction SHAP explanation | [1440×1512](transaction-shap-ulb-desktop.png) | [390×2249](transaction-shap-ulb-mobile.png) |
| Fraud prediction / actual 30-feature input | [1440×1634](fraud-prediction-form-ulb-desktop.png) | [390×2767](fraud-prediction-form-ulb-mobile.png) |
| Fraud prediction / probability estimate and risk classification | [1440×1634](fraud-prediction-result-ulb-desktop.png) | [390×3150](fraud-prediction-result-ulb-mobile.png) |
| Direct prediction / positive and negative SHAP contributions | [1440×2090](fraud-prediction-shap-ulb-desktop.png) | [390×3894](fraud-prediction-shap-ulb-mobile.png) |
| Model performance / comparison, confusion matrix, PR/ROC and calibration | [1440×2194](model-performance-ulb-desktop.png) | [390×3535](model-performance-ulb-mobile.png) |
| Analytics / validation threshold and illustrative cost trade-offs | [1440×2194](analytics-thresholds-ulb-desktop.png) | [390×3535](analytics-thresholds-ulb-mobile.png) |
| Investigation queue / real-data empty state | [1440×966](investigations-ulb-empty-desktop.png) | [390×1218](investigations-ulb-empty-mobile.png) |
| System information / model, dataset, health and schema | [1440×1153](system-information-ulb-desktop.png) | [390×1687](system-information-ulb-mobile.png) |
| Dataset import / schema and provenance controls | [1440×1439](dataset-import-dialog-desktop.png) | [390×2113](dataset-import-dialog-mobile.png) |
| Workspace search / keyboard navigation | [1440×1439](workspace-search-desktop.png) | [390×2113](workspace-search-mobile.png) |
| Investigation workbench / existing saved case, evidence and timeline | [1440×1142](investigation-workbench-synthetic-desktop.png) | [390×2337](investigation-workbench-synthetic-mobile.png) |
| Intelligence graph / entity inspection and relationships | [1440×1174](intelligence-graph-synthetic-desktop.png) | [390×1911](intelligence-graph-synthetic-mobile.png) |

## Latest previews

<details>
<summary>Dashboard / transaction activity and risk distribution</summary>

Source: 993 stored ULB records; existing XGBoost model.

**Desktop** · viewport 1440×900; PNG 1440×1439 · [dashboard-ulb-desktop.png](dashboard-ulb-desktop.png)

<a href="dashboard-ulb-desktop.png"><img src="dashboard-ulb-desktop.png" width="720" alt="Dashboard / transaction activity and risk distribution — desktop"></a>

**Mobile** · viewport 390×844; PNG 390×2113 · [dashboard-ulb-mobile.png](dashboard-ulb-mobile.png)

<a href="dashboard-ulb-mobile.png"><img src="dashboard-ulb-mobile.png" width="320" alt="Dashboard / transaction activity and risk distribution — mobile"></a>

</details>

<details>
<summary>Transaction explorer / search, filters and pagination</summary>

Source: ULB.

**Desktop** · viewport 1440×900; PNG 1440×1512 · [transactions-ulb-desktop.png](transactions-ulb-desktop.png)

<a href="transactions-ulb-desktop.png"><img src="transactions-ulb-desktop.png" width="720" alt="Transaction explorer / search, filters and pagination — desktop"></a>

**Mobile** · viewport 390×844; PNG 390×2249 · [transactions-ulb-mobile.png](transactions-ulb-mobile.png)

<a href="transactions-ulb-mobile.png"><img src="transactions-ulb-mobile.png" width="320" alt="Transaction explorer / search, filters and pagination — mobile"></a>

</details>

<details>
<summary>Transaction details / observed label and model output</summary>

Source: ULB.

**Desktop** · viewport 1440×900; PNG 1440×1512 · [transaction-details-ulb-desktop.png](transaction-details-ulb-desktop.png)

<a href="transaction-details-ulb-desktop.png"><img src="transaction-details-ulb-desktop.png" width="720" alt="Transaction details / observed label and model output — desktop"></a>

**Mobile** · viewport 390×844; PNG 390×2249 · [transaction-details-ulb-mobile.png](transaction-details-ulb-mobile.png)

<a href="transaction-details-ulb-mobile.png"><img src="transaction-details-ulb-mobile.png" width="320" alt="Transaction details / observed label and model output — mobile"></a>

</details>

<details>
<summary>Stored transaction SHAP explanation</summary>

Source: ULB; actual active XGBoost contributions.

**Desktop** · viewport 1440×900; PNG 1440×1512 · [transaction-shap-ulb-desktop.png](transaction-shap-ulb-desktop.png)

<a href="transaction-shap-ulb-desktop.png"><img src="transaction-shap-ulb-desktop.png" width="720" alt="Stored transaction SHAP explanation — desktop"></a>

**Mobile** · viewport 390×844; PNG 390×2249 · [transaction-shap-ulb-mobile.png](transaction-shap-ulb-mobile.png)

<a href="transaction-shap-ulb-mobile.png"><img src="transaction-shap-ulb-mobile.png" width="320" alt="Stored transaction SHAP explanation — mobile"></a>

</details>

<details>
<summary>Fraud prediction / actual 30-feature input</summary>

Source: Stored ULB example; no fabricated feature values.

**Desktop** · viewport 1440×900; PNG 1440×1634 · [fraud-prediction-form-ulb-desktop.png](fraud-prediction-form-ulb-desktop.png)

<a href="fraud-prediction-form-ulb-desktop.png"><img src="fraud-prediction-form-ulb-desktop.png" width="720" alt="Fraud prediction / actual 30-feature input — desktop"></a>

**Mobile** · viewport 390×844; PNG 390×2767 · [fraud-prediction-form-ulb-mobile.png](fraud-prediction-form-ulb-mobile.png)

<a href="fraud-prediction-form-ulb-mobile.png"><img src="fraud-prediction-form-ulb-mobile.png" width="320" alt="Fraud prediction / actual 30-feature input — mobile"></a>

</details>

<details>
<summary>Fraud prediction / probability estimate and risk classification</summary>

Source: ULB; actual inference, uncalibrated estimate.

**Desktop** · viewport 1440×900; PNG 1440×1634 · [fraud-prediction-result-ulb-desktop.png](fraud-prediction-result-ulb-desktop.png)

<a href="fraud-prediction-result-ulb-desktop.png"><img src="fraud-prediction-result-ulb-desktop.png" width="720" alt="Fraud prediction / probability estimate and risk classification — desktop"></a>

**Mobile** · viewport 390×844; PNG 390×3150 · [fraud-prediction-result-ulb-mobile.png](fraud-prediction-result-ulb-mobile.png)

<a href="fraud-prediction-result-ulb-mobile.png"><img src="fraud-prediction-result-ulb-mobile.png" width="320" alt="Fraud prediction / probability estimate and risk classification — mobile"></a>

</details>

<details>
<summary>Direct prediction / positive and negative SHAP contributions</summary>

Source: ULB; computed on demand.

**Desktop** · viewport 1440×900; PNG 1440×2090 · [fraud-prediction-shap-ulb-desktop.png](fraud-prediction-shap-ulb-desktop.png)

<a href="fraud-prediction-shap-ulb-desktop.png"><img src="fraud-prediction-shap-ulb-desktop.png" width="720" alt="Direct prediction / positive and negative SHAP contributions — desktop"></a>

**Mobile** · viewport 390×844; PNG 390×3894 · [fraud-prediction-shap-ulb-mobile.png](fraud-prediction-shap-ulb-mobile.png)

<a href="fraud-prediction-shap-ulb-mobile.png"><img src="fraud-prediction-shap-ulb-mobile.png" width="320" alt="Direct prediction / positive and negative SHAP contributions — mobile"></a>

</details>

<details>
<summary>Model performance / comparison, confusion matrix, PR/ROC and calibration</summary>

Source: Preserved full ULB stratified experiment; not the 993-row demo evaluation.

**Desktop** · viewport 1440×900; PNG 1440×2194 · [model-performance-ulb-desktop.png](model-performance-ulb-desktop.png)

<a href="model-performance-ulb-desktop.png"><img src="model-performance-ulb-desktop.png" width="720" alt="Model performance / comparison, confusion matrix, PR/ROC and calibration — desktop"></a>

**Mobile** · viewport 390×844; PNG 390×3535 · [model-performance-ulb-mobile.png](model-performance-ulb-mobile.png)

<a href="model-performance-ulb-mobile.png"><img src="model-performance-ulb-mobile.png" width="320" alt="Model performance / comparison, confusion matrix, PR/ROC and calibration — mobile"></a>

</details>

<details>
<summary>Analytics / validation threshold and illustrative cost trade-offs</summary>

Source: Existing validation results; display selection only.

**Desktop** · viewport 1440×900; PNG 1440×2194 · [analytics-thresholds-ulb-desktop.png](analytics-thresholds-ulb-desktop.png)

<a href="analytics-thresholds-ulb-desktop.png"><img src="analytics-thresholds-ulb-desktop.png" width="720" alt="Analytics / validation threshold and illustrative cost trade-offs — desktop"></a>

**Mobile** · viewport 390×844; PNG 390×3535 · [analytics-thresholds-ulb-mobile.png](analytics-thresholds-ulb-mobile.png)

<a href="analytics-thresholds-ulb-mobile.png"><img src="analytics-thresholds-ulb-mobile.png" width="320" alt="Analytics / validation threshold and illustrative cost trade-offs — mobile"></a>

</details>

<details>
<summary>Investigation queue / real-data empty state</summary>

Source: Existing ULB workspace has no saved cases; populated saved cases are captured separately.

**Desktop** · viewport 1440×900; PNG 1440×966 · [investigations-ulb-empty-desktop.png](investigations-ulb-empty-desktop.png)

<a href="investigations-ulb-empty-desktop.png"><img src="investigations-ulb-empty-desktop.png" width="720" alt="Investigation queue / real-data empty state — desktop"></a>

**Mobile** · viewport 390×844; PNG 390×1218 · [investigations-ulb-empty-mobile.png](investigations-ulb-empty-mobile.png)

<a href="investigations-ulb-empty-mobile.png"><img src="investigations-ulb-empty-mobile.png" width="320" alt="Investigation queue / real-data empty state — mobile"></a>

</details>

<details>
<summary>System information / model, dataset, health and schema</summary>

Source: Actual runtime metadata; access-key input is empty.

**Desktop** · viewport 1440×900; PNG 1440×1153 · [system-information-ulb-desktop.png](system-information-ulb-desktop.png)

<a href="system-information-ulb-desktop.png"><img src="system-information-ulb-desktop.png" width="720" alt="System information / model, dataset, health and schema — desktop"></a>

**Mobile** · viewport 390×844; PNG 390×1687 · [system-information-ulb-mobile.png](system-information-ulb-mobile.png)

<a href="system-information-ulb-mobile.png"><img src="system-information-ulb-mobile.png" width="320" alt="System information / model, dataset, health and schema — mobile"></a>

</details>

<details>
<summary>Dataset import / schema and provenance controls</summary>

Source: Existing import UI; no file selected or uploaded.

**Desktop** · viewport 1440×900; PNG 1440×1439 · [dataset-import-dialog-desktop.png](dataset-import-dialog-desktop.png)

<a href="dataset-import-dialog-desktop.png"><img src="dataset-import-dialog-desktop.png" width="720" alt="Dataset import / schema and provenance controls — desktop"></a>

**Mobile** · viewport 390×844; PNG 390×2113 · [dataset-import-dialog-mobile.png](dataset-import-dialog-mobile.png)

<a href="dataset-import-dialog-mobile.png"><img src="dataset-import-dialog-mobile.png" width="320" alt="Dataset import / schema and provenance controls — mobile"></a>

</details>

<details>
<summary>Workspace search / keyboard navigation</summary>

Source: Existing command menu; no writes.

**Desktop** · viewport 1440×900; PNG 1440×1439 · [workspace-search-desktop.png](workspace-search-desktop.png)

<a href="workspace-search-desktop.png"><img src="workspace-search-desktop.png" width="720" alt="Workspace search / keyboard navigation — desktop"></a>

**Mobile** · viewport 390×844; PNG 390×2113 · [workspace-search-mobile.png](workspace-search-mobile.png)

<a href="workspace-search-mobile.png"><img src="workspace-search-mobile.png" width="320" alt="Workspace search / keyboard navigation — mobile"></a>

</details>

<details>
<summary>Investigation workbench / existing saved case, evidence and timeline</summary>

Source: Existing persisted synthetic demonstration case; no new notes/cases created.

**Desktop** · viewport 1440×900; PNG 1440×1142 · [investigation-workbench-synthetic-desktop.png](investigation-workbench-synthetic-desktop.png)

<a href="investigation-workbench-synthetic-desktop.png"><img src="investigation-workbench-synthetic-desktop.png" width="720" alt="Investigation workbench / existing saved case, evidence and timeline — desktop"></a>

**Mobile** · viewport 390×844; PNG 390×2337 · [investigation-workbench-synthetic-mobile.png](investigation-workbench-synthetic-mobile.png)

<a href="investigation-workbench-synthetic-mobile.png"><img src="investigation-workbench-synthetic-mobile.png" width="320" alt="Investigation workbench / existing saved case, evidence and timeline — mobile"></a>

</details>

<details>
<summary>Intelligence graph / entity inspection and relationships</summary>

Source: Existing separate synthetic relational fixture; no ULB identities or inferred relationships.

**Desktop** · viewport 1440×900; PNG 1440×1174 · [intelligence-graph-synthetic-desktop.png](intelligence-graph-synthetic-desktop.png)

<a href="intelligence-graph-synthetic-desktop.png"><img src="intelligence-graph-synthetic-desktop.png" width="720" alt="Intelligence graph / entity inspection and relationships — desktop"></a>

**Mobile** · viewport 390×844; PNG 390×1911 · [intelligence-graph-synthetic-mobile.png](intelligence-graph-synthetic-mobile.png)

<a href="intelligence-graph-synthetic-mobile.png"><img src="intelligence-graph-synthetic-mobile.png" width="320" alt="Intelligence graph / entity inspection and relationships — mobile"></a>

</details>

## Earlier screenshots retained

These pre-existing captures are preserved unchanged for documentation continuity. Their data/model/state may differ from the latest views; use the displayed provenance labels and the latest captures above for current visual review.

<details>
<summary>graph-upgrade.png — 1440×1174</summary>

[graph-upgrade.png](graph-upgrade.png)

<a href="graph-upgrade.png"><img src="graph-upgrade.png" width="720" alt="Earlier ARGUS screenshot: graph-upgrade"></a>

</details>

<details>
<summary>investigation-mobile.png — 390×3272</summary>

[investigation-mobile.png](investigation-mobile.png)

<a href="investigation-mobile.png"><img src="investigation-mobile.png" width="320" alt="Earlier ARGUS screenshot: investigation-mobile"></a>

</details>

<details>
<summary>investigation-upgrade.png — 1440×1112</summary>

[investigation-upgrade.png](investigation-upgrade.png)

<a href="investigation-upgrade.png"><img src="investigation-upgrade.png" width="720" alt="Earlier ARGUS screenshot: investigation-upgrade"></a>

</details>

<details>
<summary>laboratory.png — 1440×1443</summary>

[laboratory.png](laboratory.png)

<a href="laboratory.png"><img src="laboratory.png" width="720" alt="Earlier ARGUS screenshot: laboratory"></a>

</details>

<details>
<summary>overview-mobile.png — 390×2235</summary>

[overview-mobile.png](overview-mobile.png)

<a href="overview-mobile.png"><img src="overview-mobile.png" width="320" alt="Earlier ARGUS screenshot: overview-mobile"></a>

</details>

<details>
<summary>overview-synthetic.png — 1440×1379</summary>

[overview-synthetic.png](overview-synthetic.png)

<a href="overview-synthetic.png"><img src="overview-synthetic.png" width="720" alt="Earlier ARGUS screenshot: overview-synthetic"></a>

</details>

<details>
<summary>overview.png — 1440×1354</summary>

[overview.png](overview.png)

<a href="overview.png"><img src="overview.png" width="720" alt="Earlier ARGUS screenshot: overview"></a>

</details>

<details>
<summary>transactions-upgrade.png — 1440×1520</summary>

[transactions-upgrade.png](transactions-upgrade.png)

<a href="transactions-upgrade.png"><img src="transactions-upgrade.png" width="720" alt="Earlier ARGUS screenshot: transactions-upgrade"></a>

</details>

<details>
<summary>ulb-explanation.png — 1440×1520</summary>

[ulb-explanation.png](ulb-explanation.png)

<a href="ulb-explanation.png"><img src="ulb-explanation.png" width="720" alt="Earlier ARGUS screenshot: ulb-explanation"></a>

</details>

