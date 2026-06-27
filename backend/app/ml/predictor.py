from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app.ml.preprocess import normalize_text
from app.ml.rules import detect_rule_hints, map_label

TRUSTED_MODEL_DIR = Path('artifacts').resolve()


class SpamScamPredictor:
    def __init__(self, model_path: Path):
        self.pipeline = self._load_or_create_fallback(model_path)

    def predict(self, message: str) -> dict:
        normalized = normalize_text(message)
        probability = float(self.pipeline.predict_proba([normalized])[0][1])
        hints = detect_rule_hints(normalized)
        label = map_label(probability, hints)
        return {
            'label': label,
            'spam_probability': round(probability, 4),
            'risk_level': self._risk_level(probability, hints),
            'explanation': {
                'top_terms': self._top_terms(normalized),
                'rule_hints': hints,
            },
        }

    def _load_or_create_fallback(self, model_path: Path) -> Pipeline:
        resolved_path = model_path.resolve()
        if TRUSTED_MODEL_DIR not in resolved_path.parents:
            raise ValueError('Model path must be inside artifacts directory')
        if resolved_path.exists():
            return joblib.load(resolved_path)
        examples = [
            'hello are we meeting today',
            'thanks for the update',
            'urgent claim your free prize now',
            'verify your bank password immediately',
        ]
        labels = [0, 0, 1, 1]
        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2))),
            ('model', LogisticRegression(class_weight='balanced')),
        ])
        pipeline.fit(examples, labels)
        return pipeline

    def _top_terms(self, text: str) -> list[str]:
        vectorizer: TfidfVectorizer = self.pipeline.named_steps['tfidf']
        model: LogisticRegression = self.pipeline.named_steps['model']
        matrix = vectorizer.transform([text])
        feature_names = vectorizer.get_feature_names_out()
        scores = matrix.toarray()[0] * model.coef_[0]
        ranked = sorted(
            ((feature_names[index], score) for index, score in enumerate(scores) if score > 0),
            key=lambda item: item[1],
            reverse=True,
        )
        return [term for term, _score in ranked[:5]]

    def _risk_level(self, probability: float, hints: list[str]) -> str:
        strong_hints = {'money language', 'credential request', 'off-platform contact request'}
        if probability >= 0.7 or strong_hints.intersection(hints):
            return 'high'
        if probability >= 0.4 or hints:
            return 'medium'
        return 'low'
