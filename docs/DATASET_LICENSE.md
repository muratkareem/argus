# ULB dataset license and attribution review

Reviewed 14 November 2026. The official [Kaggle metadata API](https://www.kaggle.com/api/v1/datasets/view/mlg-ulb/creditcardfraud) identifies the license as **Database: Open Database, Contents: Database Contents**. This is the [Open Database License (ODbL) v1.0](https://opendatacommons.org/licenses/odbl/1-0/) for the database and [Database Contents License (DbCL) v1.0](https://opendatacommons.org/licenses/dbcl/1-0/) for contents. These terms permit research/demonstration use subject to their conditions; this is not a public-domain or MIT dataset.

ARGUS attribution notice: Contains information from **Credit Card Fraud Detection**, collected and analysed through the research collaboration of **Worldline and the Machine Learning Group of Université Libre de Bruxelles (ULB)**, available from [Kaggle](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud) under ODbL v1.0, with contents under DbCL v1.0. This notice accompanies published experiment reports; keep it with presentations and other publicly used outputs.

ODbL sections 4.2–4.3 require preservation of source/license notices when distributing the database and source/license attribution with publicly used produced works. Sections 4.4 and 4.6 address publicly used derivative databases and availability of the derivative or alteration method. ARGUS publishes its preprocessing algorithm in backend/app/ml.py and does not redistribute the CSV, prepared database or trained model binaries. Anyone distributing those separately must review and satisfy the applicable database/contents terms; the code's MIT license does not replace dataset terms.

The official dataset page also requests citation of Andrea Dal Pozzolo, Olivier Caelen, Reid A. Johnson and Gianluca Bontempi, *Calibrating Probability with Undersampling for Unbalanced Classification*, IEEE Symposium on Computational Intelligence and Data Mining, 2015. This citation is reproduced as publisher-supplied bibliographic attribution, not as evidence that ARGUS implements its calibration method. The publisher provides further requested works on the source page.

The CSV is anonymized PCA/time/amount/label data, without account/cardholder/merchant identifiers. No PANs, CVVs or identity columns are accepted by ARGUS's exact schema. Anonymization does not establish a general privacy or compliance guarantee. Tracked-file and credential scans are part of delivery verification; ignored raw CSV and local SQL/artifacts are excluded from Git. Source metadata evidence: research/dataset-license-review.json.

## PaySim and IEEE-CIS review — 15 November 2026

The [author's PaySim repository](https://github.com/EdgarLopezPhD/PaySim) links to
[ealaxi/paysim1](https://www.kaggle.com/datasets/ealaxi/paysim1); the official
[Kaggle metadata API](https://www.kaggle.com/api/v1/datasets/view/ealaxi/paysim1)
identifies the dataset license as [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
Attribution: **E. A. Lopez-Rojas, A. Elmir, S. Axelsson**, *PaySim: A financial
mobile money simulator for fraud detection*, EMSS 2016. PaySim-derived published
reports and the combined comparison figure carry this attribution and are
provided under CC BY-SA 4.0; retain source/license notices and identify adaptations
when sharing. ARGUS adaptations are documented feature exclusions, seeded
sampling, preprocessing and independently fitted classification experiments.
No raw PaySim CSV, sampled dataset, identifiers or model binaries are redistributed.
The simulator repository's GPL license is distinct from the dataset's license;
ARGUS does not copy simulator code. Source evidence: [paysim-source.json](research/paysim-source.json).

[IEEE-CIS competition rules](https://www.kaggle.com/c/ieee-fraud-detection/rules)
permit noncommercial academic research/education subject to their conditions.
They do not make this competition data MIT-licensed. Download requires authorized
Kaggle access and rule acceptance; ARGUS received HTTP 401 and did not bypass it.
No IEEE data, metrics, private labels or fitted binaries are published. See
[access evidence](research/ieee-cis-access.json) and [exact integration commands](DATASETS.md).
The repository's code license remains MIT; dataset licenses/rules remain separate.
