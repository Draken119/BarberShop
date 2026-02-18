from datetime import datetime, date, timedelta
import re
from flask import Flask, flash, redirect, render_template, request, Response, url_for
from sqlalchemy import func, or_

from .config import Config
from .db import init_engine, get_session, close_session
from .models import Base, Client, Plan, Subscription, Appointment, AppointmentStatus, PlanDayRule
from .services import (EmailService, PlanPolicyService, ReturnEstimatorService,
                       SettingsService, seed_defaults)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    engine = init_engine(app.config['DATABASE_URL'])
    Base.metadata.create_all(engine)

    with app.app_context():
        session = get_session()
        seed_defaults(session)
        close_session()

    app.teardown_appcontext(close_session)

    @app.context_processor
    def inject_now():
        return {'now': datetime.now(), 'timedelta': timedelta, 'AppointmentStatus': AppointmentStatus, 'PlanDayRule': PlanDayRule}

    @app.route('/')
    def dashboard():
        session = get_session()
        today = date.today()
        total_clients = session.query(func.count(Client.id)).scalar() or 0
        today_count = session.query(func.count(Appointment.id)).filter(
            Appointment.appointment_date_time >= datetime.combine(today, datetime.min.time()),
            Appointment.appointment_date_time <= datetime.combine(today, datetime.max.time())
        ).scalar() or 0
        next7 = session.query(func.count(Appointment.id)).filter(
            Appointment.appointment_date_time >= datetime.combine(today, datetime.min.time()),
            Appointment.appointment_date_time <= datetime.combine(today + timedelta(days=7), datetime.max.time())
        ).scalar() or 0
        active_subs = session.query(func.count(Subscription.id)).filter_by(active=True).scalar() or 0
        inactive_plans = session.query(func.count(Plan.id)).filter_by(active=False).scalar() or 0
        return render_template('dashboard.html', total_clients=total_clients, today_count=today_count,
                               next7=next7, without_plan=max(total_clients - active_subs, 0), inactive_plans=inactive_plans)

    @app.route('/clients')
    def clients_list():
        session = get_session()
        q = request.args.get('q', '').strip()
        query = session.query(Client)
        if q:
            like = f'%{q}%'
            query = query.filter(or_(Client.full_name.ilike(like), Client.email.ilike(like)))
        clients = query.order_by(Client.full_name).all()
        return render_template('clients/list.html', clients=clients, q=q)

    @app.route('/clients/new', methods=['GET', 'POST'])
    @app.route('/clients/<int:client_id>/edit', methods=['GET', 'POST'])
    def clients_form(client_id=None):
        session = get_session()
        client = session.get(Client, client_id) if client_id else Client()
        if request.method == 'POST':
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip().lower()
            phone = request.form.get('phone', '').strip()
            age_text = request.form.get('age', '').strip()
            notes = request.form.get('notes', '').strip()

            if not full_name or not email or not phone:
                flash('Nome, email e telefone são obrigatórios.', 'error')
                return render_template('clients/form.html', client=client)
            if not EMAIL_RE.match(email):
                flash('E-mail inválido.', 'error')
                return render_template('clients/form.html', client=client)

            age = None
            if age_text:
                try:
                    age = int(age_text)
                    if age < 0:
                        raise ValueError
                except ValueError:
                    flash('Idade deve ser um número positivo.', 'error')
                    return render_template('clients/form.html', client=client)

            duplicate = session.query(Client).filter(Client.email == email)
            if client.id:
                duplicate = duplicate.filter(Client.id != client.id)
            if duplicate.first():
                flash('Já existe cliente com este e-mail.', 'error')
                return render_template('clients/form.html', client=client)

            client.full_name = full_name
            client.email = email
            client.phone = phone
            client.age = age
            client.notes = notes

            is_new = client.id is None
            session.add(client)
            session.flush()
            if is_new:
                EmailService(session, app.config['SMTP_HOST'], app.config['SMTP_PORT']).send_welcome(client.email, client.full_name)
                flash('Cliente criado e e-mail de boas-vindas processado.', 'success')
            else:
                flash('Cliente atualizado.', 'success')
            return redirect(url_for('clients_list'))
        return render_template('clients/form.html', client=client)

    @app.post('/clients/<int:client_id>/delete')
    def clients_delete(client_id):
        session = get_session()
        client = session.get(Client, client_id)
        if client:
            session.delete(client)
            flash('Cliente removido.', 'success')
        return redirect(url_for('clients_list'))

    @app.route('/clients/<int:client_id>')
    def clients_details(client_id):
        session = get_session()
        client = session.get(Client, client_id)
        if not client:
            return redirect(url_for('clients_list'))
        appointments = session.query(Appointment).filter_by(client_id=client.id).order_by(Appointment.appointment_date_time.desc()).all()
        estimate = ReturnEstimatorService(session).estimate_for(client)
        plans = session.query(Plan).order_by(Plan.name).all()
        active_sub = session.query(Subscription).filter_by(client_id=client.id, active=True).first()
        return render_template('clients/details.html', client=client, appointments=appointments,
                               estimate=estimate, plans=plans, active_sub=active_sub)

    @app.post('/clients/<int:client_id>/subscription')
    def subscription_activate(client_id):
        session = get_session()
        client = session.get(Client, client_id)
        plan = session.get(Plan, int(request.form['plan_id']))
        if not client or not plan:
            flash('Cliente ou plano inválido.', 'error')
            return redirect(url_for('clients_list'))
        old = session.query(Subscription).filter_by(client_id=client.id, active=True).first()
        if old:
            old.active = False
        sub = session.query(Subscription).filter_by(client_id=client.id).first()
        if not sub:
            sub = Subscription(client_id=client.id, plan_id=plan.id, start_date=date.today(), active=True)
            session.add(sub)
        else:
            sub.plan_id = plan.id
            sub.start_date = date.today()
            sub.active = True
        flash('Plano ativado/trocado com sucesso.', 'success')
        return redirect(url_for('clients_details', client_id=client_id))

    @app.post('/clients/<int:client_id>/subscription/cancel')
    def subscription_cancel(client_id):
        session = get_session()
        sub = session.query(Subscription).filter_by(client_id=client_id, active=True).first()
        if sub:
            sub.active = False
        flash('Assinatura cancelada.', 'success')
        return redirect(url_for('clients_details', client_id=client_id))

    @app.route('/plans')
    def plans_list():
        plans = get_session().query(Plan).order_by(Plan.name).all()
        return render_template('plans/list.html', plans=plans)

    @app.route('/plans/new', methods=['GET', 'POST'])
    @app.route('/plans/<int:plan_id>/edit', methods=['GET', 'POST'])
    def plans_form(plan_id=None):
        session = get_session()
        plan = session.get(Plan, plan_id) if plan_id else Plan(active=True)
        if request.method == 'POST':
            try:
                price = float(request.form.get('price', '0') or 0)
                min_days = int(request.form.get('min_days_between_appointments', '0') or 0)
                weekly_limit = int(request.form.get('weekly_limit', '1') or 1)
            except ValueError:
                flash('Preço, mínimo de dias e limite semanal devem ser numéricos.', 'error')
                return render_template('plans/form.html', plan=plan)

            plan.name = request.form.get('name', '').strip()
            plan.price = price
            plan.day_rule = PlanDayRule(request.form.get('day_rule', 'ANY_DAY'))
            plan.min_days_between_appointments = min_days
            plan.weekly_limit = weekly_limit
            plan.active = bool(request.form.get('active'))

            if not plan.name:
                flash('Nome do plano é obrigatório.', 'error')
                return render_template('plans/form.html', plan=plan)
            if plan.price < 0:
                flash('Preço não pode ser negativo.', 'error')
                return render_template('plans/form.html', plan=plan)
            if plan.min_days_between_appointments < 0:
                flash('Mínimo de dias deve ser >= 0.', 'error')
                return render_template('plans/form.html', plan=plan)
            if plan.weekly_limit < 1:
                flash('Limite semanal deve ser >= 1.', 'error')
                return render_template('plans/form.html', plan=plan)
            session.add(plan)
            flash('Plano salvo com sucesso.', 'success')
            return redirect(url_for('plans_list'))
        return render_template('plans/form.html', plan=plan)

    @app.post('/plans/<int:plan_id>/delete')
    def plans_delete(plan_id):
        session = get_session()
        plan = session.get(Plan, plan_id)
        if plan:
            session.delete(plan)
            flash('Plano removido.', 'success')
        return redirect(url_for('plans_list'))

    @app.route('/appointments')
    def appointments_list():
        appointments = get_session().query(Appointment).order_by(Appointment.appointment_date_time.desc()).all()
        return render_template('appointments/list.html', appointments=appointments)

    @app.route('/appointments/new', methods=['GET', 'POST'])
    @app.route('/appointments/<int:appointment_id>/edit', methods=['GET', 'POST'])
    def appointments_form(appointment_id=None):
        session = get_session()
        appointment = session.get(Appointment, appointment_id) if appointment_id else Appointment(status=AppointmentStatus.SCHEDULED)
        clients = session.query(Client).order_by(Client.full_name).all()
        if request.method == 'POST':
            try:
                appointment.client_id = int(request.form['client_id'])
                appointment.appointment_date_time = datetime.fromisoformat(request.form['appointment_date_time'])
            except (KeyError, ValueError):
                flash('Data/hora e cliente inválidos.', 'error')
                return render_template('appointments/form.html', appointment=appointment, clients=clients)

            appointment.service = request.form.get('service', '').strip()
            appointment.status = AppointmentStatus(request.form.get('status', 'SCHEDULED'))

            if not appointment.service:
                flash('Serviço é obrigatório.', 'error')
                return render_template('appointments/form.html', appointment=appointment, clients=clients)

            if appointment.status == AppointmentStatus.SCHEDULED and appointment.appointment_date_time < datetime.now():
                flash('Agendamento SCHEDULED deve ser no presente/futuro.', 'error')
                return render_template('appointments/form.html', appointment=appointment, clients=clients)

            client = session.get(Client, appointment.client_id)
            if not client:
                flash('Cliente não encontrado.', 'error')
                return render_template('appointments/form.html', appointment=appointment, clients=clients)

            # Regras obrigatórias no ato da criação do agendamento
            if appointment.id is None:
                try:
                    PlanPolicyService(session).validate_appointment(client, appointment.appointment_date_time)
                except ValueError as ex:
                    flash(str(ex), 'error')
                    return render_template('appointments/form.html', appointment=appointment, clients=clients)

            session.add(appointment)
            flash('Agendamento salvo.', 'success')
            return redirect(url_for('appointments_list'))
        return render_template('appointments/form.html', appointment=appointment, clients=clients)

    @app.post('/appointments/<int:appointment_id>/delete')
    def appointments_delete(appointment_id):
        session = get_session()
        a = session.get(Appointment, appointment_id)
        if a:
            session.delete(a)
            flash('Agendamento removido.', 'success')
        return redirect(url_for('appointments_list'))

    @app.route('/export/clients.csv')
    def export_clients():
        session = get_session()
        clients = session.query(Client).all()

        def esc(v):
            return (v or '').replace('"', "'")

        lines = ['id,nome,email,telefone,idade,observacoes']
        for c in clients:
            lines.append(f'{c.id},"{esc(c.full_name)}","{esc(c.email)}","{esc(c.phone)}",{c.age or ""},"{esc(c.notes)}"')
        return Response('\n'.join(lines), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=clientes.csv'})

    @app.route('/export/appointments.csv')
    def export_appointments():
        session = get_session()
        start_text = request.args.get('start')
        end_text = request.args.get('end')
        if not start_text or not end_text:
            today = date.today()
            start_text = start_text or today.isoformat()
            end_text = end_text or (today + timedelta(days=30)).isoformat()
        try:
            start = datetime.fromisoformat(start_text + 'T00:00:00')
            end = datetime.fromisoformat(end_text + 'T23:59:59')
        except ValueError:
            return Response('Parâmetros start/end inválidos. Use YYYY-MM-DD.', status=400)

        rows = session.query(Appointment).filter(
            Appointment.appointment_date_time >= start,
            Appointment.appointment_date_time <= end
        ).order_by(Appointment.appointment_date_time).all()
        lines = ['id,cliente,dataHora,servico,status']
        for a in rows:
            lines.append(f'{a.id},"{a.client.full_name}",{a.appointment_date_time.isoformat()},"{a.service}",{a.status.value}')
        return Response('\n'.join(lines), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=agenda.csv'})

    @app.route('/settings', methods=['GET', 'POST'])
    def settings():
        session = get_session()
        svc = SettingsService(session)
        if request.method == 'POST':
            svc.set(SettingsService.EMAIL_MODE, request.form.get('email_mode', 'TEST'))
            svc.set(SettingsService.EMAIL_FROM, request.form.get('email_from', 'no-reply@barbearia.local'))
            svc.set(SettingsService.EST_TARGET_CM, request.form.get('target_cm', '1.2'))
            svc.set(SettingsService.EST_BASE_RATE, request.form.get('base_rate', '0.04'))
            flash('Configurações atualizadas.', 'success')
            return redirect(url_for('settings'))
        data = {
            'email_mode': svc.get(SettingsService.EMAIL_MODE, 'TEST'),
            'email_from': svc.get(SettingsService.EMAIL_FROM, 'no-reply@barbearia.local'),
            'target_cm': svc.get(SettingsService.EST_TARGET_CM, '1.2'),
            'base_rate': svc.get(SettingsService.EST_BASE_RATE, '0.04'),
        }
        return render_template('settings/form.html', data=data)

    return app
