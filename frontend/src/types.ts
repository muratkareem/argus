export type Tx = {
  id: number;
  dataset_id: number;
  amount: number;
  time: number;
  label: number | null;
  risk_score: number | null;
  flagged: boolean | null;
  model_version: string | null;
  threshold: number | null;
  provenance: string;
  features?: Record<string, number>;
  case_ids?: number[];
};
export type Case = {
  id: number;
  title: string;
  status: string;
  priority: string;
  decision: string;
  transaction_ids: number[];
  entity_ids: string[];
  created_at: string;
  notes: { id: number; body: string; created_at: string }[];
};
export type Metrics = {
  precision: number;
  recall: number;
  f1: number;
  average_precision: number;
  roc_auc: number;
  false_positive_rate: number;
  confusion_matrix: number[][];
  pr_curve: { recall: number; precision: number }[];
};
export type Model = {
  name: string;
  threshold: number;
  validation_average_precision: number;
  test: Metrics;
  feature_importance: { feature: string; importance: number }[];
};
export type Experiment = {
  version: string;
  provenance: string;
  split: string;
  seed: number;
  rows: number;
  fraud_rows: number;
  duplicates_removed: number;
  selected_model: string;
  created_at: string;
  duration_seconds: number;
  models: Model[];
  partitions: Record<string, { rows: number; fraud: number }>;
};
export type Models = {
  active_version: string | null;
  experiments: Experiment[];
};
export type Overview = {
  total: number;
  scored: number;
  flagged: number;
  volume: number;
  fraud_detection_rate: number | null;
  labeled_scored_fraud: number;
  provenance_counts: Record<string, number>;
  risk_distribution: { bucket: string; count: number }[];
  trend: { hour: number; count: number; flagged: number; amount: number }[];
  recent_flagged: Tx[];
  open_cases: number;
};
export type Dataset = {
  id: number;
  name: string;
  provenance: string;
  rows: number;
  duplicates: number;
  created_at: string;
};
export type Settings = {
  database: string;
  ollama_enabled: boolean;
  ollama_model: string;
  max_upload_mib: number;
  authentication: string;
  schema: string[];
};
