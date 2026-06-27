import type { DetectionResult, HistoryItem, RetrainResponse } from './types';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/+$/, '');

const requestJson = async <T>(path: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (!response.ok) {
    const message = await response.text().catch(() => '');
    throw new Error(message || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
};

export const detectBatch = async (messages: string[]): Promise<DetectionResult[]> => {
  const data = await requestJson<{ results: DetectionResult[] }>('/api/detect-batch', {
    method: 'POST',
    body: JSON.stringify({ messages }),
  });
  return data.results;
};

export const getHistory = (): Promise<HistoryItem[]> => requestJson<HistoryItem[]>('/api/history');

export const retrainModel = (usePublicDataset: boolean): Promise<RetrainResponse> => requestJson<RetrainResponse>('/api/retrain', {
  method: 'POST',
  body: JSON.stringify({ use_public_dataset: usePublicDataset }),
});

export const deleteHistoryItem = async (id: number): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/api/history/${id}`, { method: 'DELETE' });
  if (!response.ok) {
    const message = await response.text().catch(() => '');
    throw new Error(message || `Request failed: ${response.status}`);
  }
};
