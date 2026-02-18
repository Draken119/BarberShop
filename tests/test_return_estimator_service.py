from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Client, Appointment, AppointmentStatus, AppSetting
from app.services import ReturnEstimatorService


def setup_session():
    engine = create_engine('sqlite:///:memory:', future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, future=True)
    s = Session()
    s.add_all([
        AppSetting(setting_key='estimator.targetCm', setting_value='1.2'),
        AppSetting(setting_key='estimator.baseRateCmPerDay', setting_value='0.04'),
    ])
    s.commit()
    return s


def test_estimator_with_history_uses_moving_average():
    s = setup_session()
    c = Client(full_name='A', email='a@a.com', phone='123', age=30)
    s.add(c)
    s.flush()
    s.add_all([
        Appointment(client_id=c.id, appointment_date_time=datetime(2026, 1, 1, 10, 0), service='Corte', status=AppointmentStatus.DONE),
        Appointment(client_id=c.id, appointment_date_time=datetime(2026, 1, 15, 10, 0), service='Corte', status=AppointmentStatus.DONE),
        Appointment(client_id=c.id, appointment_date_time=datetime(2026, 1, 29, 10, 0), service='Corte', status=AppointmentStatus.DONE),
    ])
    s.commit()
    estimate = ReturnEstimatorService(s).estimate_for(c)
    assert 'média móvel' in estimate.reasoning
    assert estimate.max_days >= estimate.min_days


def test_estimator_without_history_uses_heuristic():
    s = setup_session()
    c = Client(full_name='C', email='c@a.com', phone='123', age=50)
    s.add(c)
    s.commit()

    estimate = ReturnEstimatorService(s).estimate_for(c)
    assert 'Heurística por idade' in estimate.reasoning
    assert estimate.min_days > 0
