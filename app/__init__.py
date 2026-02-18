from datetime import datetime, date, timedelta
import re
from .config import Config
from .storage import JsonStore
from .services import EmailService, PlanPolicyService, ReturnEstimatorService, SettingsService, seed_defaults

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _find(items, item_id):
    return next((x for x in items if x['id'] == item_id), None)


def create_app():
    from flask import Flask, flash, redirect, render_template, request, Response, url_for

    app = Flask(__name__)
    app.config.from_object(Config)

    store = JsonStore(app.config['DATA_FILE'])
    data = store.read()
    seed_defaults(data, store.next_id)
    store.write(data)

    @app.context_processor
    def inject_now():
        return {'now': datetime.now(), 'timedelta': timedelta}

    @app.route('/')
    def dashboard():
        data = store.read()
        today = date.today()
        total_clients = len(data['clients'])
        today_count = sum(1 for a in data['appointments'] if datetime.fromisoformat(a['appointment_date_time']).date() == today)
        next7 = sum(1 for a in data['appointments'] if today <= datetime.fromisoformat(a['appointment_date_time']).date() <= today + timedelta(days=7))
        active_subs = sum(1 for s in data['subscriptions'] if s['active'])
        inactive_plans = sum(1 for p in data['plans'] if not p['active'])
        return render_template('dashboard.html', total_clients=total_clients, today_count=today_count,
                               next7=next7, without_plan=max(total_clients-active_subs, 0), inactive_plans=inactive_plans)

    @app.route('/clients')
    def clients_list():
        data = store.read()
        q = request.args.get('q', '').strip().lower()
        clients = data['clients']
        if q:
            clients = [c for c in clients if q in c['full_name'].lower() or q in c['email'].lower()]
        clients.sort(key=lambda x: x['full_name'].lower())
        return render_template('clients/list.html', clients=clients, q=q)

    @app.route('/clients/new', methods=['GET', 'POST'])
    @app.route('/clients/<int:client_id>/edit', methods=['GET', 'POST'])
    def clients_form(client_id=None):
        data = store.read()
        client = _find(data['clients'], client_id) if client_id else {'id': None, 'full_name': '', 'email': '', 'phone': '', 'age': None, 'notes': ''}
        if request.method == 'POST':
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip().lower()
            phone = request.form.get('phone', '').strip()
            age_text = request.form.get('age', '').strip()
            notes = request.form.get('notes', '').strip()

            if not full_name or not email or not phone:
                flash('Nome, email e telefone são obrigatórios.', 'error')
                client.update({'full_name': full_name, 'email': email, 'phone': phone, 'notes': notes})
                return render_template('clients/form.html', client=client)
            if not EMAIL_RE.match(email):
                flash('E-mail inválido.', 'error')
                client.update({'full_name': full_name, 'email': email, 'phone': phone, 'notes': notes})
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

            if any(c['email'] == email and c['id'] != client_id for c in data['clients']):
                flash('Já existe cliente com este e-mail.', 'error')
                return render_template('clients/form.html', client=client)

            if client_id:
                client.update({'full_name': full_name, 'email': email, 'phone': phone, 'age': age, 'notes': notes})
                flash('Cliente atualizado.', 'success')
            else:
                new_client = {
                    'id': store.next_id(data, 'clients'),
                    'full_name': full_name,
                    'email': email,
                    'phone': phone,
                    'age': age,
                    'notes': notes,
                }
                data['clients'].append(new_client)
                EmailService(app.config['SMTP_HOST'], app.config['SMTP_PORT']).send_welcome(data, new_client['email'], new_client['full_name'])
                flash('Cliente criado e e-mail de boas-vindas processado.', 'success')

            store.write(data)
            return redirect(url_for('clients_list'))
        return render_template('clients/form.html', client=client)

    @app.post('/clients/<int:client_id>/delete')
    def clients_delete(client_id):
        data = store.read()
        data['clients'] = [c for c in data['clients'] if c['id'] != client_id]
        data['appointments'] = [a for a in data['appointments'] if a['client_id'] != client_id]
        data['subscriptions'] = [s for s in data['subscriptions'] if s['client_id'] != client_id]
        store.write(data)
        flash('Cliente removido.', 'success')
        return redirect(url_for('clients_list'))

    @app.route('/clients/<int:client_id>')
    def clients_details(client_id):
        data = store.read()
        client = _find(data['clients'], client_id)
        if not client:
            return redirect(url_for('clients_list'))
        appointments = sorted([a for a in data['appointments'] if a['client_id'] == client_id], key=lambda x: x['appointment_date_time'], reverse=True)
        estimate = ReturnEstimatorService.estimate_for(data, client)
        plans = sorted(data['plans'], key=lambda p: p['name'])
        active_sub = next((s for s in data['subscriptions'] if s['client_id'] == client_id and s['active']), None)
        if active_sub:
            active_sub = dict(active_sub)
            active_sub['plan'] = _find(data['plans'], active_sub['plan_id'])
        return render_template('clients/details.html', client=client, appointments=appointments,
                               estimate=estimate, plans=plans, active_sub=active_sub)

    @app.post('/clients/<int:client_id>/subscription')
    def subscription_activate(client_id):
        data = store.read()
        plan_id = int(request.form['plan_id'])
        client = _find(data['clients'], client_id)
        plan = _find(data['plans'], plan_id)
        if not client or not plan:
            flash('Cliente ou plano inválido.', 'error')
            return redirect(url_for('clients_list'))

        for s in data['subscriptions']:
            if s['client_id'] == client_id and s['active']:
                s['active'] = False
        found = next((s for s in data['subscriptions'] if s['client_id'] == client_id), None)
        if found:
            found['plan_id'] = plan_id
            found['start_date'] = date.today().isoformat()
            found['active'] = True
        else:
            data['subscriptions'].append({
                'id': store.next_id(data, 'subscriptions'),
                'client_id': client_id,
                'plan_id': plan_id,
                'start_date': date.today().isoformat(),
                'active': True,
            })
        store.write(data)
        flash('Plano ativado/trocado com sucesso.', 'success')
        return redirect(url_for('clients_details', client_id=client_id))

    @app.post('/clients/<int:client_id>/subscription/cancel')
    def subscription_cancel(client_id):
        data = store.read()
        for s in data['subscriptions']:
            if s['client_id'] == client_id and s['active']:
                s['active'] = False
        store.write(data)
        flash('Assinatura cancelada.', 'success')
        return redirect(url_for('clients_details', client_id=client_id))

    @app.route('/plans')
    def plans_list():
        data = store.read()
        plans = sorted(data['plans'], key=lambda p: p['name'])
        return render_template('plans/list.html', plans=plans)

    @app.route('/plans/new', methods=['GET', 'POST'])
    @app.route('/plans/<int:plan_id>/edit', methods=['GET', 'POST'])
    def plans_form(plan_id=None):
        data = store.read()
        plan = _find(data['plans'], plan_id) if plan_id else {'id': None, 'name': '', 'price': 0, 'day_rule': 'ANY_DAY', 'min_days_between_appointments': 0, 'weekly_limit': 1, 'active': True}
        if request.method == 'POST':
            try:
                price = float(request.form.get('price', '0') or 0)
                min_days = int(request.form.get('min_days_between_appointments', '0') or 0)
                weekly_limit = int(request.form.get('weekly_limit', '1') or 1)
                day_rule = request.form.get('day_rule', 'ANY_DAY')
            except ValueError:
                flash('Valores numéricos inválidos.', 'error')
                return render_template('plans/form.html', plan=plan)
            name = request.form.get('name', '').strip()
            active = bool(request.form.get('active'))

            if not name:
                flash('Nome do plano é obrigatório.', 'error')
                return render_template('plans/form.html', plan=plan)
            if price < 0 or min_days < 0 or weekly_limit < 1:
                flash('Validações do plano inválidas.', 'error')
                return render_template('plans/form.html', plan=plan)
            if day_rule not in {'ANY_DAY', 'WEEKDAYS_ONLY'}:
                flash('Regra de dias inválida.', 'error')
                return render_template('plans/form.html', plan=plan)

            if plan_id:
                plan.update({'name': name, 'price': price, 'day_rule': day_rule,
                             'min_days_between_appointments': min_days, 'weekly_limit': weekly_limit, 'active': active})
            else:
                data['plans'].append({'id': store.next_id(data, 'plans'), 'name': name, 'price': price, 'day_rule': day_rule,
                                      'min_days_between_appointments': min_days, 'weekly_limit': weekly_limit, 'active': active})
            store.write(data)
            flash('Plano salvo com sucesso.', 'success')
            return redirect(url_for('plans_list'))
        return render_template('plans/form.html', plan=plan)

    @app.post('/plans/<int:plan_id>/delete')
    def plans_delete(plan_id):
        data = store.read()
        data['plans'] = [p for p in data['plans'] if p['id'] != plan_id]
        for s in data['subscriptions']:
            if s['plan_id'] == plan_id:
                s['active'] = False
        store.write(data)
        flash('Plano removido.', 'success')
        return redirect(url_for('plans_list'))

    @app.route('/appointments')
    def appointments_list():
        data = store.read()
        clients = {c['id']: c for c in data['clients']}
        appointments = sorted(data['appointments'], key=lambda x: x['appointment_date_time'], reverse=True)
        for a in appointments:
            a['client'] = clients.get(a['client_id'], {'full_name': 'Cliente removido'})
        return render_template('appointments/list.html', appointments=appointments)

    @app.route('/appointments/new', methods=['GET', 'POST'])
    @app.route('/appointments/<int:appointment_id>/edit', methods=['GET', 'POST'])
    def appointments_form(appointment_id=None):
        data = store.read()
        appt = _find(data['appointments'], appointment_id) if appointment_id else {
            'id': None, 'client_id': None, 'appointment_date_time': '', 'service': '', 'status': 'SCHEDULED'
        }
        clients = sorted(data['clients'], key=lambda c: c['full_name'])
        if request.method == 'POST':
            try:
                client_id = int(request.form['client_id'])
                when = datetime.fromisoformat(request.form['appointment_date_time'])
                status = request.form.get('status', 'SCHEDULED')
            except (ValueError, KeyError):
                flash('Data/hora e cliente inválidos.', 'error')
                return render_template('appointments/form.html', appointment=appt, clients=clients)
            service = request.form.get('service', '').strip()
            if not service:
                flash('Serviço é obrigatório.', 'error')
                return render_template('appointments/form.html', appointment=appt, clients=clients)
            if status == 'SCHEDULED' and when < datetime.now():
                flash('Agendamento SCHEDULED deve ser no presente/futuro.', 'error')
                return render_template('appointments/form.html', appointment=appt, clients=clients)
            if not _find(data['clients'], client_id):
                flash('Cliente não encontrado.', 'error')
                return render_template('appointments/form.html', appointment=appt, clients=clients)
            if appointment_id is None:
                try:
                    PlanPolicyService.validate_appointment(data, client_id, when)
                except ValueError as ex:
                    flash(str(ex), 'error')
                    return render_template('appointments/form.html', appointment=appt, clients=clients)

            if appointment_id:
                appt.update({'client_id': client_id, 'appointment_date_time': when.isoformat(), 'service': service, 'status': status})
            else:
                data['appointments'].append({'id': store.next_id(data, 'appointments'), 'client_id': client_id,
                                             'appointment_date_time': when.isoformat(), 'service': service, 'status': status})
            store.write(data)
            flash('Agendamento salvo.', 'success')
            return redirect(url_for('appointments_list'))
        return render_template('appointments/form.html', appointment=appt, clients=clients)

    @app.post('/appointments/<int:appointment_id>/delete')
    def appointments_delete(appointment_id):
        data = store.read()
        data['appointments'] = [a for a in data['appointments'] if a['id'] != appointment_id]
        store.write(data)
        flash('Agendamento removido.', 'success')
        return redirect(url_for('appointments_list'))

    @app.route('/export/clients.csv')
    def export_clients():
        data = store.read()
        lines = ['id,nome,email,telefone,idade,observacoes']
        for c in data['clients']:
            notes = (c.get('notes') or '').replace('"', "'")
            lines.append(f'{c["id"]},"{c["full_name"]}","{c["email"]}","{c["phone"]}",{c.get("age") or ""},"{notes}"')
        return Response('\n'.join(lines), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=clientes.csv'})

    @app.route('/export/appointments.csv')
    def export_appointments():
        data = store.read()
        start_text = request.args.get('start') or date.today().isoformat()
        end_text = request.args.get('end') or (date.today() + timedelta(days=30)).isoformat()
        try:
            start = datetime.fromisoformat(start_text + 'T00:00:00')
            end = datetime.fromisoformat(end_text + 'T23:59:59')
        except ValueError:
            return Response('Parâmetros start/end inválidos. Use YYYY-MM-DD.', status=400)

        clients = {c['id']: c['full_name'] for c in data['clients']}
        rows = [a for a in data['appointments'] if start <= datetime.fromisoformat(a['appointment_date_time']) <= end]
        rows.sort(key=lambda x: x['appointment_date_time'])
        lines = ['id,cliente,dataHora,servico,status']
        for a in rows:
            lines.append(f'{a["id"]},"{clients.get(a["client_id"], "Cliente removido")}",{a["appointment_date_time"]},"{a["service"]}",{a["status"]}')
        return Response('\n'.join(lines), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=agenda.csv'})

    @app.route('/settings', methods=['GET', 'POST'])
    def settings():
        data = store.read()
        if request.method == 'POST':
            SettingsService.set(data, SettingsService.EMAIL_MODE, request.form.get('email_mode', 'TEST'))
            SettingsService.set(data, SettingsService.EMAIL_FROM, request.form.get('email_from', 'no-reply@barbearia.local'))
            SettingsService.set(data, SettingsService.EST_TARGET_CM, request.form.get('target_cm', '1.2'))
            SettingsService.set(data, SettingsService.EST_BASE_RATE, request.form.get('base_rate', '0.04'))
            store.write(data)
            flash('Configurações atualizadas.', 'success')
            return redirect(url_for('settings'))

        page_data = {
            'email_mode': SettingsService.get(data, SettingsService.EMAIL_MODE, 'TEST'),
            'email_from': SettingsService.get(data, SettingsService.EMAIL_FROM, 'no-reply@barbearia.local'),
            'target_cm': SettingsService.get(data, SettingsService.EST_TARGET_CM, '1.2'),
            'base_rate': SettingsService.get(data, SettingsService.EST_BASE_RATE, '0.04'),
        }
        return render_template('settings/form.html', data=page_data)

    return app
