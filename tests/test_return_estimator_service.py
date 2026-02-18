from app.services import ReturnEstimatorService


def test_estimator_with_history_uses_moving_average():
    data = {
        'settings': [
            {'setting_key': 'estimator.targetCm', 'setting_value': '1.2'},
            {'setting_key': 'estimator.baseRateCmPerDay', 'setting_value': '0.04'},
        ],
        'appointments': [
            {'client_id': 1, 'appointment_date_time': '2026-01-01T10:00:00', 'status': 'DONE'},
            {'client_id': 1, 'appointment_date_time': '2026-01-15T10:00:00', 'status': 'DONE'},
            {'client_id': 1, 'appointment_date_time': '2026-01-29T10:00:00', 'status': 'DONE'},
        ],
    }
    estimate = ReturnEstimatorService.estimate_for(data, {'id': 1, 'age': 30})
    assert 'média móvel' in estimate.reasoning


def test_estimator_without_history_uses_heuristic():
    data = {
        'settings': [
            {'setting_key': 'estimator.targetCm', 'setting_value': '1.2'},
            {'setting_key': 'estimator.baseRateCmPerDay', 'setting_value': '0.04'},
        ],
        'appointments': [],
    }
    estimate = ReturnEstimatorService.estimate_for(data, {'id': 2, 'age': 50})
    assert 'Heurística por idade' in estimate.reasoning
    assert estimate.min_days > 0
