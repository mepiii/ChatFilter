import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import App from './App';

const okJson = (data: unknown) => Promise.resolve({ ok: true, json: () => Promise.resolve(data) } as Response);

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('App', () => {
  it('renders analysis results after manual analyze', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
      if (String(url).endsWith('/api/history')) return okJson([]);
      return okJson({
        results: [{
          message: 'claim prize now',
          label: 'scam',
          spam_probability: 0.91,
          risk_level: 'high',
          explanation: { top_terms: ['prize'], rule_hints: ['reward claim'] },
        }],
      });
    });

    render(<App />);
    await userEvent.type(screen.getByLabelText(/chat messages/i), 'claim prize now');
    await userEvent.click(screen.getByRole('button', { name: /analyze/i }));

    expect(await screen.findByText('scam')).toBeInTheDocument();
    expect(screen.getByText('91%')).toBeInTheDocument();
    expect(screen.getByText('reward claim')).toBeInTheDocument();
  });

  it('shows API error state', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('offline'));
    render(<App />);
    await userEvent.type(screen.getByLabelText(/chat messages/i), 'hello');
    await userEvent.click(screen.getByRole('button', { name: /analyze/i }));

    expect(await screen.findByText(/api unavailable/i)).toBeInTheDocument();
  });

  it('loads history', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
      if (String(url).endsWith('/api/history')) {
        return okJson([{ id: 1, message: 'hello', label: 'safe', spam_probability: 0.03, risk_level: 'low', explanation: { top_terms: [], rule_hints: [] }, created_at: '2026-04-27T00:00:00Z' }]);
      }
      return okJson({ results: [] });
    });

    render(<App />);
    expect(await screen.findByText('hello')).toBeInTheDocument();
  });

  it('retrain button renders metrics', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
      if (String(url).endsWith('/api/history')) return okJson([]);
      if (String(url).endsWith('/api/retrain')) {
        return okJson({ source: 'seed dataset', metrics: { accuracy: 1, precision: 0.9, recall: 0.8, f1: 0.85 } });
      }
      return okJson({ results: [] });
    });

    render(<App />);
    await userEvent.click(screen.getByRole('button', { name: /use seed data/i }));

    expect(await screen.findByText(/last trained: seed dataset/i)).toBeInTheDocument();
    expect(screen.getByText('accuracy: 100%')).toBeInTheDocument();
  });
});
