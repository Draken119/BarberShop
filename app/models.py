from datetime import datetime, date
from enum import Enum
from sqlalchemy import (Boolean, Column, Date, DateTime, Enum as SAEnum, ForeignKey,
                        Integer, Numeric, String, Text)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class PlanDayRule(str, Enum):
    ANY_DAY = 'ANY_DAY'
    WEEKDAYS_ONLY = 'WEEKDAYS_ONLY'

class AppointmentStatus(str, Enum):
    SCHEDULED = 'SCHEDULED'
    DONE = 'DONE'
    CANCELED = 'CANCELED'
    NO_SHOW = 'NO_SHOW'

class Client(Base):
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(60), nullable=False)
    age = Column(Integer)
    notes = Column(Text)

class Plan(Base):
    __tablename__ = 'plans'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False, unique=True)
    price = Column(Numeric(10,2), nullable=False)
    day_rule = Column(SAEnum(PlanDayRule), nullable=False)
    min_days_between_appointments = Column(Integer, nullable=False, default=0)
    weekly_limit = Column(Integer, nullable=False, default=1)
    active = Column(Boolean, nullable=False, default=True)

class Subscription(Base):
    __tablename__ = 'subscriptions'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, unique=True)
    plan_id = Column(Integer, ForeignKey('plans.id'), nullable=False)
    start_date = Column(Date, nullable=False, default=date.today)
    active = Column(Boolean, nullable=False, default=True)

    client = relationship('Client')
    plan = relationship('Plan')

class Appointment(Base):
    __tablename__ = 'appointments'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    appointment_date_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    service = Column(String(255), nullable=False)
    status = Column(SAEnum(AppointmentStatus), nullable=False, default=AppointmentStatus.SCHEDULED)

    client = relationship('Client')

class AppSetting(Base):
    __tablename__ = 'app_settings'
    setting_key = Column(String(100), primary_key=True)
    setting_value = Column(String(1000), nullable=False)
