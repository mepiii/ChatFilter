"""Model training and optional dataset download utilities.

Purpose: Train ChatFilter text classifier from CSV data.
Callers: CLI, FastAPI retrain endpoint, tests.
Deps: pandas, scikit-learn, joblib, urllib.
API: load_dataset(), download_public_dataset(), train(), main().
Side effects: Writes model/metrics artifacts and optional dataset CSV.
"""

import argparse
import json
from pathlib import Path
from urllib.request import urlretrieve

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.ml.preprocess import normalize_text


LABEL_MAP = {'safe': 0, 'spam': 1, 'scam': 1, 'ham': 0}
PUBLIC_DATASET_URL = 'https://raw.githubusercontent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv'


def download_public_dataset(path: Path, url: str = PUBLIC_DATASET_URL) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix('.tmp')
    urlretrieve(url, temporary_path)
    data = pd.read_csv(temporary_path, sep='\t', names=['label', 'message'])
    data.to_csv(path, index=False)
    temporary_path.unlink(missing_ok=True)
    return path


def load_dataset(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path).copy()
    data.loc[:, 'message'] = data['message'].astype(str).map(normalize_text)
    data.loc[:, 'target'] = data['label'].astype(str).str.lower().map(LABEL_MAP)
    return data.dropna(subset=['target']).copy()


def train(data_path: Path, model_path: Path, metrics_path: Path) -> dict[str, float]:
    data = load_dataset(data_path)
    if data.empty:
        raise ValueError('Training dataset has no valid labeled rows')
    targets = data['target'].astype(int)
    class_counts = targets.value_counts()
    if len(class_counts) < 2:
        raise ValueError('Training dataset must contain at least two classes')
    if class_counts.min() < 2:
        raise ValueError('Each class needs at least two samples for stratified split')
    x_train, x_test, y_train, y_test = train_test_split(
        data['message'],
        targets,
        test_size=0.3,
        random_state=42,
        stratify=targets,
    )
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2))),
        ('model', LogisticRegression(class_weight='balanced', max_iter=1000)),
    ])
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    metrics = {
        'accuracy': round(float(accuracy_score(y_test, predictions)), 4),
        'precision': round(float(precision_score(y_test, predictions, zero_division=0)), 4),
        'recall': round(float(recall_score(y_test, predictions, zero_division=0)), 4),
        'f1': round(float(f1_score(y_test, predictions, zero_division=0)), 4),
    }
    model_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    metrics_path.write_text(json.dumps(metrics, indent=2))
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path, default=Path('data/seed_messages.csv'))
    parser.add_argument('--model', type=Path, default=Path('artifacts/spam_model.joblib'))
    parser.add_argument('--metrics', type=Path, default=Path('artifacts/model_metrics.json'))
    parser.add_argument('--download-public', action='store_true')
    args = parser.parse_args()
    if args.download_public:
        download_public_dataset(args.data)
    metrics = train(args.data, args.model, args.metrics)
    print(json.dumps(metrics, indent=2))


if __name__ == '__main__':
    main()
