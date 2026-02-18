from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from email.message import EmailMessage
import logging
import smtplib

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

    DEFAULTS = {
        EMAIL_MODE: 'TEST',
        EMAIL_FROM: 'no-reply@barbearia.local',
        EST_TARGET_CM: '1.2',
        EST_BASE_RATE: '0.04',
    }

    @classmethod
    def ensure_defaults(cls, data):
        existing = {s['setting_key'] for s in data['settings']}
        for k, v in cls.DEFAULTS.items():
            if k not in existing:
                data['settings'].append({'setting_key': k, 'setting_value': v})

    @staticmethod
    def get(data, key, default):
        for s in data['settings']:
            if s['setting_key'] == key:
                return s['setting_value']
        return default

    @staticmethod
    def set(data, key, value):
        for s in data['settings']:
            if s['setting_key'] == key:
                s['setting_value'] = value
                return
        data['settings'].append({'setting_key': key, 'setting_value': value})


class EmailService:
    def __init__(self, smtp_host='localhost', smtp_port=1025):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

    def send_welcome(self, data, to_email: str, name: str):
        mode = SettingsService.get(data, SettingsService.EMAIL_MODE, 'TEST')
        from_email = SettingsService.get(data, SettingsService.EMAIL_FROM, 'no-reply@barbearia.local')
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
    @staticmethod
    def validate_appointment(data, client_id: int, when: datetime):
        sub = next((s for s in data['subscriptions'] if s['client_id'] == client_id and s['active']), None)
        if not sub:
            raise ValueError('Cliente sem plano ativo.')
        plan = next((p for p in data['plans'] if p['id'] == sub['plan_id']), None)
        if not plan:
            raise ValueError('Plano da assinatura não encontrado.')

        if plan['day_rule'] == 'WEEKDAYS_ONLY' and when.weekday() >= 5:
            raise ValueError('Este plano permite somente dias úteis.')

        week_start = when.date() - timedelta(days=when.weekday())
        week_end = week_start + timedelta(days=6)
        scheduled_count = 0
        for a in data['appointments']:
            dt = datetime.fromisoformat(a['appointment_date_time'])
            if a['client_id'] == client_id and a['status'] == 'SCHEDULED' and week_start <= dt.date() <= week_end:
                scheduled_count += 1
        if scheduled_count >= plan['weekly_limit']:
            raise ValueError('Limite semanal do plano atingido.')

        done = [a for a in data['appointments'] if a['client_id'] == client_id and a['status'] == 'DONE']
        if done:
            last_done = max(done, key=lambda x: x['appointment_date_time'])
            last_date = datetime.fromisoformat(last_done['appointment_date_time']).date()
            days = (when.date() - last_date).days
            if days < plan['min_days_between_appointments']:
                raise ValueError('Intervalo mínimo entre cortes não respeitado.')


class ReturnEstimatorService:
    @staticmethod
    def estimate_for(data, client) -> EstimateRange:
        target_cm = float(SettingsService.get(data, SettingsService.EST_TARGET_CM, '1.2'))
        base_rate = float(SettingsService.get(data, SettingsService.EST_BASE_RATE, '0.04'))

        age = client.get('age')
        if age is None:
            rate = base_rate
        elif age < 18:
            rate = base_rate * 1.10
        elif age <= 45:
            rate = base_rate
        else:
            rate = base_rate * 0.9

        baseline = max(5, round(target_cm / rate))
        min_days, max_days = max(3, baseline - 3), baseline + 4

        done = sorted(
            [a for a in data['appointments'] if a['client_id'] == client['id'] and a['status'] == 'DONE'],
            key=lambda a: a['appointment_date_time']
        )
        if len(done) >= 3:
            gaps = []
            for i in range(1, len(done)):
                d1 = datetime.fromisoformat(done[i - 1]['appointment_date_time']).date()
                d2 = datetime.fromisoformat(done[i]['appointment_date_time']).date()
                gaps.append((d2 - d1).days)
            avg = sum(gaps) / len(gaps)
            mid = round((baseline + avg) / 2)
            return EstimateRange(max(3, mid - 2), max(mid + 3, mid - 1), 'Heurística de idade + média móvel do histórico real.')

        return EstimateRange(min_days, max_days, 'Heurística por idade e taxa média de crescimento.')


def seed_defaults(data, next_id):
    seeds = [
        ('Basic', 79.90, 'ANY_DAY', 7, 1),
        ('Plus', 119.90, 'WEEKDAYS_ONLY', 0, 999),
        ('Max', 159.90, 'ANY_DAY', 0, 999),
    ]
    names = {p['name'].lower() for p in data['plans']}
    for name, price, day_rule, min_days, weekly in seeds:
        if name.lower() not in names:
            data['plans'].append({
                'id': next_id(data, 'plans'),
                'name': name,
                'price': price,
                'day_rule': day_rule,
                'min_days_between_appointments': min_days,
                'weekly_limit': weekly,
                'active': True,
            })
    SettingsService.ensure_defaults(data)
