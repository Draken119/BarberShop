# ✂️ Painel da Barbearia (Flask)

Sistema web completo para barbearia, agora em **Python + Flask**, mantendo todas as funcionalidades do projeto original.

## Stack
- Python 3.11+
- Flask
- SQLAlchemy
- SQLite (dev, arquivo local)
- Pronto para PostgreSQL via `DATABASE_URL`
- Pytest

## Funcionalidades
- **Clientes (CRUD)** + busca por nome/email.
- **Planos (CRUD)** com regras: `ANY_DAY` e `WEEKDAYS_ONLY`, limite semanal e mínimo entre cortes.
- **Assinaturas** (1 ativa por cliente): ativar/trocar/cancelar com data de início.
- **Agenda (CRUD)** com status: `SCHEDULED`, `DONE`, `CANCELED`, `NO_SHOW`.
- **Validação por plano** ao agendar:
  - bloqueio de fim de semana para `WEEKDAYS_ONLY`;
  - limite semanal;
  - intervalo mínimo com base no último `DONE`.
- **E-mail de boas-vindas**:
  - `TEST` (log)
  - `SMTP` (envio real)
- **Estimador de retorno** (sem API externa) com heurística + média móvel do histórico.
- **Dashboard** com totais, hoje, próximos 7 dias e alertas.
- **Export CSV**: clientes e agenda por período.
- **Configurações**: modo de e-mail, remetente e parâmetros do estimador.
- **Seed idempotente** dos planos Basic/Plus/Max.

## Como rodar
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Acesse:
- Painel: `http://localhost:5000`

## Banco de dados
Por padrão usa SQLite local em `data/barbershop.db`.

Para PostgreSQL:
```bash
export DATABASE_URL='postgresql+psycopg://user:pass@localhost:5432/barbershop'
```

## Testes
```bash
pytest
```
