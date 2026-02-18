<div align="center">

# ✂️💈 Painel da Barbearia

<img alt="Java" src="https://img.shields.io/badge/Java-21-ED8B00?style=for-the-badge&logo=openjdk&logoColor=white" />
<img alt="Spring Boot" src="https://img.shields.io/badge/Spring_Boot-3.x-6DB33F?style=for-the-badge&logo=springboot&logoColor=white" />
<img alt="Thymeleaf" src="https://img.shields.io/badge/Thymeleaf-UI-005F0F?style=for-the-badge&logo=thymeleaf&logoColor=white" />
<img alt="Maven" src="https://img.shields.io/badge/Maven-Build-C71A36?style=for-the-badge&logo=apachemaven&logoColor=white" />
<img alt="H2" src="https://img.shields.io/badge/H2-Dev_DB-0F4C81?style=for-the-badge" />

### Um painel web moderno para gestão completa de barbearia

</div>

---

## 🌟 Visão Geral

O **Painel da Barbearia** é uma aplicação web feita em **Java 21 + Spring Boot 3** para organizar a operação diária da barbearia de forma simples, visual e eficiente.

Com ele, você consegue:

- 👤 Gerenciar clientes (cadastro, edição, busca e detalhes completos).
- 🧾 Configurar planos de assinatura com regras de uso.
- 🔁 Ativar, trocar e cancelar assinaturas por cliente.
- 📅 Controlar agenda com validações automáticas baseadas no plano ativo.
- 📊 Acompanhar indicadores no dashboard inicial.
- 📤 Exportar dados em CSV para relatórios.
- 📧 Enviar boas-vindas por e-mail (modo teste ou SMTP real).
- 🤖 Obter estimativa de retorno do cliente com heurística local (sem API externa).

---

## 🧠 O que a aplicação faz (em detalhes)

### 1) Clientes (CRUD + busca)
- Cadastro com: **nome completo, e-mail, telefone, idade e observações**.
- Listagem com busca por nome ou e-mail.
- Tela de detalhes com:
  - histórico de atendimentos;
  - assinatura ativa;
  - estimativa de retorno do cliente.

### 2) Planos (CRUD editável)
Cada plano possui:
- nome;
- preço;
- regra de dias (`ANY_DAY` ou `WEEKDAYS_ONLY`);
- mínimo de dias entre cortes;
- limite semanal de agendamentos.

Na primeira execução, o sistema cria automaticamente (sem duplicar em reinícios):
- **Basic** → 1 corte/semana (`minDaysBetween=7`, `weeklyLimit=1`, `ANY_DAY`)
- **Plus** → dias úteis (`WEEKDAYS_ONLY`, `weeklyLimit=999`, `minDaysBetween=0`)
- **Max** → qualquer dia (`ANY_DAY`, `weeklyLimit=999`, `minDaysBetween=0`)

### 3) Assinaturas (Cliente ↔ Plano)
- Cada cliente pode manter **uma assinatura ativa**.
- Fluxos disponíveis:
  - ativar plano;
  - trocar plano;
  - cancelar assinatura.
- Registro de data de início da assinatura.

### 4) Agenda (Agendamentos)
- Campos: cliente, data/hora, serviço e status (`SCHEDULED`, `DONE`, `CANCELED`, `NO_SHOW`).
- Regras automáticas no agendamento:
  - bloqueia sábado/domingo para plano `WEEKDAYS_ONLY`;
  - respeita limite semanal do plano;
  - respeita intervalo mínimo entre cortes com base no último atendimento `DONE`.
- Formulário com `datetime-local` convertido para `LocalDateTime`.

### 5) E-mail de boas-vindas
- **Modo TEST**: não envia e-mail real, apenas registra no log.
- **Modo SMTP**: envio real via servidor SMTP.
- Seleção do modo no painel de configurações.

### 6) Estimador de retorno (“IA própria”)
Sem APIs externas.

O sistema calcula uma janela estimada **(mín..máx dias)** para retorno do cliente usando:
- heurística por idade + taxa base de crescimento;
- ajuste por média móvel com histórico real de atendimentos `DONE`.

---

## 🖥️ Dashboard e utilidades

A tela inicial traz:
- total de clientes;
- agendamentos do dia;
- agendamentos dos próximos 7 dias;
- alertas de clientes sem plano ativo;
- quantidade de planos inativos.

Extras:
- Exportação CSV de clientes;
- Exportação CSV da agenda por período;
- Página de configurações básicas do sistema.

---

## 🧱 Stack Técnica

- **Java 21**
- **Spring Boot 3**
- **Spring MVC + Thymeleaf**
- **Spring Data JPA**
- **Bean Validation**
- **H2 Database** (desenvolvimento)
- **PostgreSQL-ready** (configuração preparada)
- **Maven**
- **JUnit 5 + Mockito**

---

## 📦 Requisitos

- Java 21 instalado
- Maven 3.9+

Verifique versões:

```bash
java -version
mvn -v
```

---

## 🚀 Como rodar o projeto

```bash
mvn spring-boot:run
```

Após iniciar:
- App: `http://localhost:8080`
- H2 Console: `http://localhost:8080/h2-console`

### Credenciais H2 (dev)
- JDBC URL: `jdbc:h2:file:./data/barbershopdb;AUTO_SERVER=TRUE`
- User: `sa`
- Password: *(vazio)*

---

## 🧭 Navegação rápida do painel

- `/` → Dashboard
- `/clients` → Clientes
- `/plans` → Planos
- `/appointments` → Agenda
- `/settings` → Configurações
- `/export/clients.csv` → Exportar clientes
- `/export/appointments.csv?start=YYYY-MM-DD&end=YYYY-MM-DD` → Exportar agenda

---

## ⚙️ Configurações importantes

No painel em `/settings`, você pode ajustar:
- modo de e-mail (`TEST` ou `SMTP`);
- e-mail remetente (`from`);
- parâmetros do estimador (`targetCm` e `baseRate`).

---

## 🐘 Como migrar para PostgreSQL

Edite `src/main/resources/application.yml` com algo como:

```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/barbershop
    username: postgres
    password: postgres
    driver-class-name: org.postgresql.Driver
  jpa:
    hibernate:
      ddl-auto: update
```

Passos:
1. Suba o PostgreSQL.
2. Crie o banco `barbershop`.
3. Atualize `application.yml`.
4. Rode novamente: `mvn spring-boot:run`.

---

## ✅ Qualidade implementada

- Organização por pacotes (`domain`, `repo`, `service`, `web`, `config`).
- Validações de formulário com mensagens amigáveis.
- Seed idempotente de planos.
- Testes unitários para regras de plano e estimador de retorno.

---

## 🧪 Testes

```bash
mvn test
```

---

<div align="center">

### Feito com ☕, ✂️ e foco na experiência da barbearia

</div>
