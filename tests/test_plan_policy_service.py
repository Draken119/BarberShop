from datetime import datetime
import pytest

from app.services import PlanPolicyService


def test_blocks_weekend_for_weekdays_plan():
    data = {
        'plans': [{'id': 1, 'day_rule': 'WEEKDAYS_ONLY', 'weekly_limit': 999, 'min_days_between_appointments': 0}],
        'subscriptions': [{'id': 1, 'client_id': 10, 'plan_id': 1, 'active': True}],
        'appointments': []
    }
    with pytest.raises(ValueError, match='dias úteis'):
        PlanPolicyService.validate_appointment(data, 10, datetime(2026, 2, 21, 10, 0))


def test_blocks_min_days_between():
    data = {
        'plans': [{'id': 1, 'day_rule': 'ANY_DAY', 'weekly_limit': 10, 'min_days_between_appointments': 7}],
        'subscriptions': [{'id': 1, 'client_id': 10, 'plan_id': 1, 'active': True}],
        'appointments': [{'id': 1, 'client_id': 10, 'appointment_date_time': '2026-02-01T10:00:00', 'status': 'DONE'}]
    }
    with pytest.raises(ValueError, match='Intervalo mínimo'):
        PlanPolicyService.validate_appointment(data, 10, datetime(2026, 2, 3, 10, 0))
