from app.ml.rules import detect_rule_hints, map_label


def test_detect_rule_hints_finds_scam_patterns():
    hints = detect_rule_hints('Urgent: verify your bank password to claim your prize at https://bad.example')
    assert 'url present' in hints
    assert 'urgency language' in hints
    assert 'reward claim' in hints
    assert 'credential request' in hints


def test_map_label_marks_strong_scam_hint_as_scam():
    assert map_label(0.72, ['credential request']) == 'scam'


def test_map_label_marks_medium_probability_as_spam():
    assert map_label(0.55, []) == 'spam'


def test_map_label_marks_low_probability_as_safe():
    assert map_label(0.12, []) == 'safe'


def test_map_label_marks_low_probability_strong_hint_as_scam():
    assert map_label(0.12, ['credential request']) == 'scam'


def test_map_label_marks_low_probability_weak_hint_as_spam():
    assert map_label(0.12, ['reward claim']) == 'spam'
