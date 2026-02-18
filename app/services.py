from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, date
from email.message import EmailMessage
import logging
import smtplib
from typing import Optional
from sqlalchemy import func

from .models import (AppSetting, Appointment, AppointmentStatus, Client, Plan,
                     PlanDayRule, Subscription)

logger = logging.getLogger(__name__)

@dataclass
class EstimateRange:
    min_days: int
    max_days: int
    reasoning: str

class SettingsService:
    EMAIL_MODE = 'email.mode'
    EMAIL_FROM = 'email.from'
    EST_TARGET_CM = 'estimator.targetCm'
    EST_BASE_RATE = 'estimator.baseRateCmPerDay'

    def __init__(self, session):
        self.session = session

    def ensure_defaults(self):
        self._set_if_missing(self.EMAIL_MODE, 'TEST')
        self._set_if_missing(self.EMAIL_FROM, 'no-reply@barbearia.local')
        self._set_if_missing(self.EST_TARGET_CM, '1.2')
        self._set_if_missing(self.EST_BASE_RATE, '0.04')

    def _set_if_missing(self, key, value):
        if not self.session.get(AppSetting, key):
            self.session.add(AppSetting(setting_key=key, setting_value=value))

    def get(self, key, default):
        found = self.session.get(AppSetting, key)
        return found.setting_value if found else default

    def set(self, key, value):
        self.session.merge(AppSetting(setting_key=key, setting_value=value))

class EmailService:
    def __init__(self, session, smtp_host='localhost', smtp_port=1025):
        self.settings = SettingsService(session)
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

    def send_welcome(self, to_email: str, name: str):
        mode = self.settings.get(SettingsService.EMAIL_MODE, 'TEST')
        from_email = self.settings.get(SettingsService.EMAIL_FROM, 'no-reply@barbearia.local')
        subject = 'Bem-vindo à Barbearia'
        body = f'Olá {name}, seu cadastro foi concluído com sucesso!\n\nAlerta: não esqueça de agendar seu primeiro corte.'
        if mode == 'TEST':
            logger.info('[EMAIL TEST] to=%s subject=%s body=%s', to_email, subject, body)
            logger.warning('[ALERTA] Novo cliente cadastrado: %s (%s)', name, to_email)
            return
        msg = EmailMessage()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.set_content(body)
        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as smtp:
            smtp.send_message(msg)

class PlanPolicyService:
    def __init__(self, session):
        self.session = session

    def validate_appointment(self, client: Client, when: datetime):
        sub = self.session.query(Subscription).filter_by(client_id=client.id, active=True).first()
        if not sub:
            raise ValueError('Cliente sem plano ativo.')
        plan = sub.plan
        if plan.day_rule == PlanDayRule.WEEKDAYS_ONLY and when.weekday() >= 5:
            raise ValueError('Este plano permite somente dias úteis.')

        week_start = when.date() - timedelta(days=when.weekday())
        week_end = week_start + timedelta(days=6)
        scheduled_count = self.session.query(func.count(Appointment.id)).filter(
            Appointment.client_id == client.id,
            Appointment.status == AppointmentStatus.SCHEDULED,
            Appointment.appointment_date_time >= datetime.combine(week_start, datetime.min.time()),
            Appointment.appointment_date_time <= datetime.combine(week_end, datetime.max.time()),
        ).scalar() or 0
        if scheduled_count >= plan.weekly_limit:
            raise ValueError('Limite semanal do plano atingido.')

        last_done = self.session.query(Appointment).filter_by(
            client_id=client.id,
            status=AppointmentStatus.DONE
        ).order_by(Appointment.appointment_date_time.desc()).first()
        if last_done:
            days = (when.date() - last_done.appointment_date_time.date()).days
            if days < plan.min_days_between_appointments:
                raise ValueError('Intervalo mínimo entre cortes não respeitado.')

class ReturnEstimatorService:
    def __init__(self, session):
        self.session = session
        self.settings = SettingsService(session)

    def estimate_for(self, client: Client) -> EstimateRange:
        target_cm = float(self.settings.get(SettingsService.EST_TARGET_CM, '1.2'))
        base_rate = float(self.settings.get(SettingsService.EST_BASE_RATE, '0.04'))
        rate = self._adjust_rate_by_age(base_rate, client.age)
        baseline = max(5, round(target_cm / rate))
        min_days, max_days = max(3, baseline - 3), baseline + 4

        done = self.session.query(Appointment).filter_by(
            client_id=client.id,
            status=AppointmentStatus.DONE
        ).order_by(Appointment.appointment_date_time.asc()).all()
        if len(done) >= 3:
            gaps = []
            for i in range(1, len(done)):
                gaps.append((done[i].appointment_date_time.date() - done[i-1].appointment_date_time.date()).days)
            avg = sum(gaps) / len(gaps)
            mid = round((baseline + avg) / 2)
            return EstimateRange(max(3, mid-2), max(mid+3, mid-1), 'Heurística de idade + média móvel do histórico real.')
        return EstimateRange(min_days, max_days, 'Heurística por idade e taxa média de crescimento.')

    def _adjust_rate_by_age(self, base_rate: float, age: Optional[int]) -> float:
        if age is None:
            return base_rate
        if age < 18:
            return base_rate * 1.10
        if age <= 45:
            return base_rate
        return base_rate * 0.9


def seed_defaults(session):
    seeds = [
        ('Basic', 79.90, PlanDayRule.ANY_DAY, 7, 1),
        ('Plus', 119.90, PlanDayRule.WEEKDAYS_ONLY, 0, 999),
        ('Max', 159.90, PlanDayRule.ANY_DAY, 0, 999),
    ]
    for name, price, day_rule, min_days, weekly in seeds:
        if not session.query(Plan).filter(func.lower(Plan.name) == name.lower()).first():
            session.add(Plan(
                name=name,
                price=price,
                day_rule=day_rule,
                min_days_between_appointments=min_days,
                weekly_limit=weekly,
                active=True,
            ))
    SettingsService(session).ensure_defaults()
