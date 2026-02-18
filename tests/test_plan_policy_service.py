from datetime import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Client, Plan, Subscription, PlanDayRule, Appointment, AppointmentStatus
from app.services import PlanPolicyService


def setup_session():
    engine = create_engine('sqlite:///:memory:', future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, future=True)
    return Session()


def test_blocks_weekend_for_weekdays_plan():
    s = setup_session()
    c = Client(full_name='A', email='a@a.com', phone='123')
    p = Plan(name='P', price=10, day_rule=PlanDayRule.WEEKDAYS_ONLY, min_days_between_appointments=0, weekly_limit=999)
    s.add_all([c, p])
    s.flush()
    s.add(Subscription(client_id=c.id, plan_id=p.id, active=True))
    s.commit()

    with pytest.raises(ValueError, match='dias úteis'):
        PlanPolicyService(s).validate_appointment(c, datetime(2026, 2, 21, 10, 0))


def test_blocks_when_min_days_between_not_respected():
    s = setup_session()
    c = Client(full_name='B', email='b@a.com', phone='123')
    p = Plan(name='Basic', price=10, day_rule=PlanDayRule.ANY_DAY, min_days_between_appointments=7, weekly_limit=10)
    s.add_all([c, p])
    s.flush()
    s.add(Subscription(client_id=c.id, plan_id=p.id, active=True))
    s.add(Appointment(client_id=c.id, appointment_date_time=datetime(2026, 2, 1, 10, 0), service='Corte', status=AppointmentStatus.DONE))
    s.commit()

    with pytest.raises(ValueError, match='Intervalo mínimo'):
        PlanPolicyService(s).validate_appointment(c, datetime(2026, 2, 3, 10, 0))
