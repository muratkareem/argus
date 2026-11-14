# Project overview

**Development of a Machine Learning System for Credit Card Fraud Detection Using Transaction Data**

ARGUS supports offline research and analyst review of anonymized credit card transactions. Its users are students, researchers and demonstration analysts. The objective is reproducible classification under severe class imbalance, combined with transparent explanations and a persistent investigation workflow.

Functional requirements: validate/import transactions; distinguish observed labels from model flags; search/filter/sort/page records; predict individually and in batches; change review thresholds; explain on demand; compare three algorithms; retain notes, links and case decisions; export evidence; inspect health/model/dataset metadata.

Nonfunctional requirements: CPU-only operation, bounded requests, repeatable splits, training-only preprocessing, versioned artifacts, honest measurements, accessible responsive controls, parameterized database queries, restricted local deployment and no generative model service.

Scope excludes payment processing, bank integration, real cardholder identities, production authorization and compliance certification. A flagged score requires review; it is not a factual fraud determination. Synthetic demonstrations do not establish real-world effectiveness.
