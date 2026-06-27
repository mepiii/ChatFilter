import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app, rate_limiter, settings
from app.models import AnalysisHistory


@pytest.fixture
def client():
    original_limit = rate_limiter.limit
    rate_limiter.requests.clear()
    with SessionLocal() as db:
        db.query(AnalysisHistory).delete()
        db.commit()
    with TestClient(app) as test_client:
        yield test_client
    rate_limiter.limit = original_limit
    rate_limiter.requests.clear()


def test_detect_spam_returns_prediction(client):
    response = client.post('/api/detect-spam', json={'message': 'Urgent claim your prize now'})
    assert response.status_code == 200
    data = response.json()
    assert data['label'] in {'spam', 'scam'}
    assert 0 <= data['spam_probability'] <= 1
    assert 'top_terms' in data['explanation']
    assert 'rule_hints' in data['explanation']


def test_detect_strong_scam_hint_returns_high_risk(client):
    response = client.post('/api/detect-spam', json={'message': 'verify your bank password now'})
    assert response.status_code == 200
    data = response.json()
    assert data['label'] == 'scam'
    assert data['risk_level'] == 'high'


def test_detect_batch_returns_results(client):
    response = client.post('/api/detect-batch', json={'messages': ['hello friend', 'verify your bank password now']})
    assert response.status_code == 200
    data = response.json()
    assert len(data['results']) == 2
    assert data['results'][0]['message'] == 'hello friend'


def test_metrics_endpoint_returns_scores(client):
    response = client.get('/api/model-metrics')
    assert response.status_code == 200
    assert set(response.json()) == {'accuracy', 'precision', 'recall', 'f1'}


def test_retrain_endpoint_returns_metrics(client):
    response = client.post('/api/retrain', json={'use_public_dataset': False})
    assert response.status_code == 200
    data = response.json()
    assert data['source'] == 'seed dataset'
    assert set(data['metrics']) == {'accuracy', 'precision', 'recall', 'f1'}


def test_history_lists_created_detection(client):
    client.post('/api/detect-spam', json={'message': 'claim free cash now'})
    response = client.get('/api/history')
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert {'id', 'message', 'label', 'spam_probability', 'risk_level', 'explanation', 'created_at'} <= set(data[0])


def test_history_delete_removes_item(client):
    message = 'claim lottery prize now'
    client.post('/api/detect-spam', json={'message': message})
    items = client.get('/api/history').json()
    item_id = next(item['id'] for item in items if item['message'] == message)
    response = client.delete(f'/api/history/{item_id}')
    assert response.status_code == 204
    assert client.delete(f'/api/history/{item_id}').status_code == 404


def test_rate_limit_returns_429(client):
    rate_limiter.limit = 1
    assert client.post('/api/detect-spam', json={'message': 'hello'}).status_code == 200
    response = client.post('/api/detect-spam', json={'message': 'hello again'})
    assert response.status_code == 429
    assert response.json() == {'detail': 'Rate limit exceeded'}


def test_invalid_messages_are_rejected(client):
    assert client.post('/api/detect-spam', json={'message': ''}).status_code == 422
    assert client.post('/api/detect-spam', json={'message': 'x' * (settings.max_message_length + 1)}).status_code == 422
    assert client.post('/api/detect-batch', json={'messages': []}).status_code == 422
    assert client.post('/api/detect-batch', json={'messages': ['hello'] * (settings.max_batch_size + 1)}).status_code == 422
