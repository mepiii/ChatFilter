/* Purpose: Render ChatFilter analysis UI, history, and feedback states. Callers: React entrypoint. Deps: React, API client, shared DTO types. API: App component. Side effects: Fetches detection and history data. */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { deleteHistoryItem, detectBatch, getHistory, retrainModel } from './api';
import type { DetectionResult, HistoryItem, RetrainResponse } from './types';

const examples = ['Hey are we still meeting tonight?', 'Congratulations claim your free prize now', 'Urgent verify your bank password immediately'];

const splitMessages = (text: string): string[] => text.split('\n').map((line) => line.trim()).filter(Boolean);

const percent = (value: number): string => `${Math.round(value * 100)}%`;

function App() {
  const [input, setInput] = useState('');
  const [results, setResults] = useState<DetectionResult[]>([]);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [retrainResult, setRetrainResult] = useState<RetrainResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [retraining, setRetraining] = useState(false);
  const [error, setError] = useState('');
  const messages = useMemo(() => splitMessages(input), [input]);

  const loadHistory = useCallback(async () => {
    try {
      setHistory(await getHistory());
    } catch {
      setHistory([]);
    }
  }, []);

  const analyze = useCallback(async () => {
    if (messages.length === 0) return;
    setLoading(true);
    setError('');
    try {
      setResults(await detectBatch(messages));
      await loadHistory();
    } catch {
      setError('API unavailable. Start the FastAPI backend and try again.');
    } finally {
      setLoading(false);
    }
  }, [loadHistory, messages]);

  const removeHistory = async (id: number) => {
    try {
      await deleteHistoryItem(id);
      await loadHistory();
    } catch {
      setError('Unable to delete history item. Try again.');
    }
  };

  const retrain = async (usePublicDataset: boolean) => {
    setRetraining(true);
    setError('');
    try {
      setRetrainResult(await retrainModel(usePublicDataset));
    } catch {
      setError('Unable to retrain model. Try the seed dataset or check the backend logs.');
    } finally {
      setRetraining(false);
    }
  };

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  useEffect(() => {
    if (messages.length === 0) {
      setResults([]);
      return;
    }
    const timer = window.setTimeout(() => void analyze(), 500);
    return () => window.clearTimeout(timer);
  }, [analyze, messages.length]);

  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">Machine Learning Web App</p>
        <h1>ChatFilter</h1>
        <p>Paste chat messages, get risk scores, and inspect why messages look suspicious.</p>
      </section>

      <section className="panel">
        <label htmlFor="messages">Chat messages</label>
        <textarea
          id="messages"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder={examples.join('\n')}
          rows={8}
        />
        <div className="actions">
          <button onClick={() => void analyze()} disabled={loading || messages.length === 0}>Analyze</button>
          <span>{loading ? 'Analyzing...' : `${messages.length} message(s)`}</span>
        </div>
        {error && <p className="error" role="alert">{error}</p>}
      </section>

      <section className="panel retrain-panel">
        <div>
          <h2>Retrain model</h2>
          <p className="muted-text">Refresh the classifier with seed data or download the public SMS spam dataset.</p>
        </div>
        <div className="actions">
          <button onClick={() => void retrain(false)} disabled={retraining}>Use seed data</button>
          <button onClick={() => void retrain(true)} disabled={retraining}>Use public dataset</button>
          <span>{retraining ? 'Retraining...' : retrainResult ? `Last trained: ${retrainResult.source}` : 'Ready'}</span>
        </div>
        {retrainResult && (
          <div className="metrics">
            {Object.entries(retrainResult.metrics).map(([name, value]) => <span key={name}>{name}: {percent(value)}</span>)}
          </div>
        )}
      </section>

      {results.length === 0 ? (
        <section className="panel muted">
          <h2>Try examples</h2>
          {examples.map((example) => <button className="example" key={example} onClick={() => setInput(example)}>{example}</button>)}
        </section>
      ) : (
        <section className="grid">
          {results.map((result, index) => (
            <article className={`card ${result.risk_level}`} key={`${result.message}-${index}`}>
              <div className="card-head">
                <strong>{result.label}</strong>
                <span>{percent(result.spam_probability)}</span>
              </div>
              <p>{result.message}</p>
              <div
                className="bar"
                role="progressbar"
                aria-label="Spam probability"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={Math.round(result.spam_probability * 100)}
              >
                <span style={{ width: percent(result.spam_probability) }} />
              </div>
              <div className="chips">
                <span>{result.risk_level} risk</span>
                {[...result.explanation.top_terms, ...result.explanation.rule_hints].map((item, itemIndex) => <span key={`${item}-${itemIndex}`}>{item}</span>)}
              </div>
            </article>
          ))}
        </section>
      )}

      <section className="panel">
        <h2>History</h2>
        {history.length === 0 ? <p className="muted-text">No analyzed messages yet.</p> : history.map((item) => (
          <div className="history-item" key={item.id}>
            <div>
              <strong>{item.label}</strong>
              <p>{item.message}</p>
            </div>
            <button onClick={() => void removeHistory(item.id)}>Delete</button>
          </div>
        ))}
      </section>
    </main>
  );
}

export default App;
