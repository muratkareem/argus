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
  day_cluster_bootstrap?: {
    method: string;
    clusters: number;
    repeats: number;
    intervals: Record<string, [number, number] | null>;
    limitation: string;
  };
  confidence_intervals?: {
    method: string;
    precision: [number, number] | null;
    recall: [number, number] | null;
    limitation: string;
  };
  precision: number;
  recall: number;
  f1: number;
  average_precision: number;
  roc_auc: number;
  false_positive_rate: number;
  false_negative_rate?: number;
  brier_score?: number;
  roc_curve?: { false_positive_rate: number; true_positive_rate: number }[];
  calibration_curve?: {
    mean_predicted_probability: number;
    fraction_positive: number;
  }[];
  confusion_matrix: number[][];
  pr_curve: { recall: number; precision: number }[];
};
export type Model = {
  name: string;
  threshold: number;
  validation_average_precision: number;
  test: Metrics;
  feature_importance: { feature: string; importance: number }[];
  inference_latency?: {
    single_p50_ms: number;
    single_p95_ms: number;
    batch_1000_ms: number;
    measurement: string;
    repeats: number;
  };
  validation_threshold_analysis?: {
    partition: string;
    cost_assumptions: {
      unit: string;
      false_positive: number;
      false_negative: number;
    };
    points: {
      threshold: number;
      precision: number;
      recall: number;
      f1: number;
      false_positives: number;
      false_negatives: number;
      estimated_cost: number;
    }[];
  };
};
export type BenchmarkCatalog = {
  datasets: {
    id: string;
    name: string;
    data_kind: string;
    status: string;
    source: string;
    license: string;
    blocker: string | null;
  }[];
  experiments: Experiment[];
  report_errors: { file: string; error: string }[];
  interpretation: string;
};
export type Experiment = {
  dataset_id?: string;
  data_kind?: string;
  execution_status?: string;
  limitations?: string;
  preprocessing?: {
    numeric: string[];
    categorical: string[];
    excluded: string[];
  };
  source?: { sampling: string; rows: number; fraud_rows: number };
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
  labeled_fraud?: number;
  labeled_legitimate?: number;
  unlabeled?: number;
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
export type ActiveModel = {
  status: string;
  name?: string | null;
  version?: string | null;
  provenance?: string;
  threshold?: number;
  last_evaluated_at?: string | null;
};
export type Settings = {
  active_model?: ActiveModel;
  database: string;
  max_upload_mib: number;
  authentication: string;
  schema: string[];
};
