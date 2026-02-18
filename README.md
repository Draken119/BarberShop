# ✂️ Painel da Barbearia (Flask + JSON)

Sistema web completo para barbearia em **Python + Flask**, com persistência em **arquivo JSON** (sem SQLAlchemy).

## Stack
- Python 3.11+
- Flask
- JSON file database (`data/barbershop.json`)
- Pytest

## Funcionalidades
- **Clientes (CRUD)** + busca por nome/email.
- **Planos (CRUD)** com regras `ANY_DAY` e `WEEKDAYS_ONLY`, limite semanal e mínimo entre cortes.
- **Assinaturas** (1 ativa por cliente): ativar/trocar/cancelar com data de início.
- **Agenda (CRUD)** com status `SCHEDULED`, `DONE`, `CANCELED`, `NO_SHOW`.
- **Validação por plano** no agendamento (dias permitidos, limite semanal, intervalo mínimo).
- **E-mail de boas-vindas** em modo `TEST` (log) ou `SMTP`.
- **Estimador de retorno** (heurística + média móvel).
- **Dashboard** com totais e alertas.
- **Export CSV** de clientes e agenda por período.
- **Configurações** de e-mail e parâmetros do estimador.
- **Seed idempotente** dos planos Basic/Plus/Max.

## Como rodar
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Acesse: `http://localhost:5000`

## Testes
```bash
pytest
```
