from app.ml.preprocess import normalize_text


def test_normalize_text_lowercases_and_trims_spaces():
    assert normalize_text('  WIN   A Prize NOW  ') == 'win a prize now'


def test_normalize_text_keeps_url_money_and_phone_signals():
    text = normalize_text('Pay $50 at https://bad.example or call +1-555-0100')
    assert '$' in text
    assert 'https://bad.example' in text
    assert '+1-555-0100' in text
