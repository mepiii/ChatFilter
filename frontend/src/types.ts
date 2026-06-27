export type Explanation = {
  top_terms: string[];
  rule_hints: string[];
};

export type DetectionResult = {
  message?: string | null;
  label: 'safe' | 'spam' | 'scam';
  spam_probability: number;
  risk_level: 'low' | 'medium' | 'high';
  explanation: Explanation;
};

export type HistoryItem = DetectionResult & {
  id: number;
  message: string;
  created_at: string;
};

export type ModelMetrics = {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
};

export type RetrainResponse = {
  metrics: ModelMetrics;
  source: string;
};
