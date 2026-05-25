# PlantOS

Sistema distribuído de **ordens de serviço para plantas industriais**, desenvolvido como projeto integrador da disciplina de Laboratório de Desenvolvimento de Aplicações Móveis e Distribuídas — PUC Minas, 1º Semestre 2026.

---

## Sobre o projeto

O **PlantOS** (*Plant* + *OS*) digitaliza o fluxo de abertura, acompanhamento e conclusão de ordens de serviço em ambientes industriais. Operadores de chão de fábrica registram falhas ou necessidades de manutenção em equipamentos, e técnicos de manutenção recebem, avaliam e executam essas ordens de forma assíncrona, documentando os materiais utilizados e emitindo um laudo técnico ao final.

A arquitetura é **orientada a eventos (EDA)**: toda mudança de estado de uma OS gera um evento publicado no RabbitMQ, que notifica os aplicativos interessados sem necessidade de polling contínuo. Isso garante comunicação em tempo real entre os dois perfis de usuário.

### Problema resolvido

Em plantas industriais, a comunicação entre operadores e equipes de manutenção é frequentemente feita de forma verbal ou em quadros físicos — métodos sujeitos a perda de informação, atrasos e falta de rastreabilidade. O PlantOS elimina esses problemas com rastreabilidade completa, notificações automáticas e registro estruturado de cada intervenção.

---

## Perfis de usuário

| Perfil | Papel | Funcionalidades principais |
|---|---|---|
| **Operador** (Cliente) | Profissional da operação da planta | Abre OS com título, descrição, setor, equipamento e prioridade; acompanha status em tempo real; recebe notificação de aceite/recusa/conclusão; consulta laudo e materiais |
| **Técnico** (Prestador) | Profissional de manutenção | Recebe novas OS em tempo real; aceita ou recusa; registra materiais utilizados; conclui com laudo técnico; consulta histórico de OS executadas |

---

## Ciclo de vida de uma OS

```
  ┌────────┐    aceitar    ┌────────┐   iniciar   ┌──────────────┐   concluir   ┌───────────┐
  │ ABERTA │──────────────►│ ACEITA │────────────►│ EM ANDAMENTO │─────────────►│ CONCLUÍDA │
  └────┬───┘               └────────┘             └──────────────┘              └───────────┘
       │   recusar    ┌──────────┐
       └─────────────►│ RECUSADA │
                      └──────────┘
```

---

## Arquitetura

```
┌──────────────────┐                          ┌──────────────────┐
│  App Operador    │                          │  App Técnico     │
│  (Flutter/Dart)  │                          │  (Flutter/Dart)  │
└────────┬─────────┘                          └────────┬─────────┘
         │ REST (HTTP/JSON)                            │ REST (HTTP/JSON)
         ▼                                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Backend Flask (Python)                        │
│                 API REST + Event Publisher                       │
├──────────────────────────┬───────────────────────────────────────┤
│       SQLite             │           RabbitMQ (AMQP)            │
│    (Persistência)        │          (Mensageria/MOM)            │
└──────────────────────────┴───────────────────────────────────────┘
                                       │
                          Eventos assíncronos
                          ▼               ▼
                   App Técnico     App Operador
                   (notificado)    (notificado)
```

**Protocolos de comunicação:**
- **Apps ↔ Backend:** HTTP/REST com payloads JSON (porta 5000)
- **Backend → RabbitMQ:** AMQP 0-9-1 (porta 5672) — publicação de eventos (mensagens persistentes)
- **RabbitMQ → Apps:** Consumo via filas duráveis (fila.operador e fila.tecnico)
- **Backend ↔ Banco:** SQLite (acesso local embutido, arquivo `plantos.db`)

> Documentação completa da arquitetura com diagramas Mermaid (C4, sequência, ER, máquina de estados) disponível em [`docs/sprint1/arquitetura.md`](docs/sprint1/arquitetura.md).

---

## Fluxo de eventos

| Evento | Produzido quando | Produtor | Consumidor | Fila/Exchange |
|---|---|---|---|---|
| `os.criada` | Operador abre nova OS | Backend (via endpoint POST /os) | App do técnico | `plantos.events` |
| `os.aceita` | Técnico aceita a OS | Backend (via endpoint PATCH) | App do operador | `plantos.events` |
| `os.recusada` | Técnico recusa a OS | Backend (via endpoint PATCH) | App do operador | `plantos.events` |
| `os.em_andamento` | Técnico inicia a execução | Backend (via endpoint PATCH) | App do operador | `plantos.events` |
| `os.concluida` | Técnico conclui com laudo | Backend (via endpoint PATCH) | App do operador | `plantos.events` |

---

## Endpoints da API REST

> **Sprint 2:** todas as rotas (exceto `/auth/register`, `/auth/login` e `/health`) exigem o header `Authorization: Bearer <jwt>`.

### Autenticação

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| `POST` | `/auth/register` | Público | Cadastra usuário com role `operador`, `tecnico` ou `admin` |
| `POST` | `/auth/login` | Público | Retorna JWT (válido por 8h) |
| `GET`  | `/auth/me` | Autenticado | Retorna o usuário associado ao token |
| `GET`  | `/auth/usuarios` | Admin | Lista todos os usuários (sem hash de senha) |
| `GET`  | `/health` | Público | Healthcheck |

### Ordens de Serviço

| Método | Rota | Quem pode | Descrição |
|---|---|---|---|
| `POST` | `/os` | operador | Criar OS (`operador_id` vem do token) |
| `GET` | `/os` | autenticado | Listar OS (operador vê apenas as suas) |
| `GET` | `/os/<id>` | autenticado | Consultar OS por ID |
| `PATCH` | `/os/<id>/aceitar` | tecnico | Aceita a OS (publica `os.aceita`) |
| `PATCH` | `/os/<id>/recusar` | tecnico | Recusa (publica `os.recusada`) |
| `PATCH` | `/os/<id>/iniciar` | tecnico | Inicia (publica `os.em_andamento`) |
| `PATCH` | `/os/<id>/concluir` | tecnico | Conclui com laudo (publica `os.concluida`) |
| `POST` | `/os/<id>/materiais` | tecnico | Registra material utilizado |
| `GET` | `/os/<id>/materiais` | autenticado | Lista materiais de uma OS |

---

## Modelo de dados

### Usuário (Sprint 2)

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | INTEGER (PK) | Identificador único |
| `nome` | TEXT | Nome completo |
| `login` | TEXT (UNIQUE) | Identificador de acesso |
| `senha` | TEXT | Hash bcrypt (nunca exposto) |
| `role` | TEXT | operador, tecnico, admin |
| `ativo` | INTEGER | 0 ou 1 |
| `criado_em` / `atualizado_em` | DATETIME | Timestamps |

### Ordem de Serviço

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | INTEGER (PK) | Identificador único |
| `titulo` | TEXT | Título resumido da falha |
| `descricao` | TEXT | Descrição detalhada |
| `setor` | TEXT | Setor ou área da planta |
| `equipamento` | TEXT | Equipamento afetado |
| `prioridade` | TEXT | baixa, média, alta, crítica |
| `status` | TEXT | aberta, aceita, em_andamento, concluída, recusada |
| `operador_id` | TEXT | Identificador do operador |
| `tecnico_id` | TEXT | Identificador do técnico (após aceite) |
| `laudo` | TEXT | Laudo técnico (após conclusão) |
| `criado_em` | DATETIME | Data/hora de criação |
| `atualizado_em` | DATETIME | Data/hora da última atualização |

### Material Utilizado

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | INTEGER (PK) | Identificador único |
| `ordem_servico_id` | INTEGER (FK) | Referência à OS |
| `nome` | TEXT | Nome do material/peça |
| `quantidade` | INTEGER | Quantidade utilizada |

### Evento Consumido (Sprint 2 — Auditoria)

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | INTEGER (PK) | Identificador único |
| `fila` | TEXT | Nome da fila RabbitMQ de origem |
| `routing_key` | TEXT | Routing key do evento (`os.criada`, `os.aceita`, ...) |
| `payload` | TEXT | JSON completo da mensagem |
| `recebido_em` | DATETIME | Timestamp em que o worker processou |

---

## Estrutura do repositório

```
PlantOS-LAMD/
├── backend/              # API REST Flask + publisher/consumer RabbitMQ
│   ├── app.py            # Entry point
│   ├── requirements.txt  # Dependências Python
│   └── app/
│       ├── models/       # Modelos de dados (SQLite nativo)
│       ├── routes/       # Blueprints com endpoints REST
│       ├── services/     # Lógica de negócio
│       └── messaging/    # Publisher e consumer RabbitMQ
├── apps/
│   ├── operator/         # Flutter — app do operador (cliente)
│   │   └── lib/
│   │       ├── models/   # Modelos de dados Dart
│   │       ├── screens/  # Telas do app
│   │       └── services/ # Comunicação com API e eventos
│   └── technician/       # Flutter — app do técnico (prestador)
│       └── lib/
│           ├── models/
│           ├── screens/
│           └── services/
├── infra/                # podman-compose.yml (RabbitMQ)
├── docs/                 # Entregas por sprint
│   ├── sprint1/          # Proposta, diagrama, backend REST
│   ├── sprint2/          # Integração MOM
│   ├── sprint3/          # App Flutter — Operador
│   └── sprint4/          # App Flutter — Técnico + entrega final
└── README.md
```

---

## Coleção de Testes (Postman)

O arquivo [`backend/PlantOS.postman_collection.json`](backend/PlantOS.postman_collection.json) contém a coleção atualizada da Sprint 2 (com JWT + RBAC), organizada em quatro grupos:

1. **Auth** — `/auth/register`, `/auth/login` (salva o token automaticamente em variáveis da coleção), `/auth/me`
2. **Ordens de Serviço** — CRUD + transições + casos de erro (400, 401, 403, 404, 409)
3. **Materiais** — Registro e listagem de materiais por OS
4. **Fluxo Completo Sprint 2** — 10 requests sequenciais: registrar operador e técnico, login (popula `op_token`/`tec_token`), criar OS, aceitar, iniciar, registrar material, concluir com laudo, verificar estado final. Com o worker rodando, os 4 eventos aparecem no console e na tabela `evento_log`.

Todos os requests incluem exemplos de resposta salvos (`saved examples`).

**Para importar:** Postman → Import → selecione o arquivo JSON.

---

## Pré-requisitos

- Python 3.11+
- Flutter 3.10+ / Dart 3.x
- Podman e Podman Compose

---

## Como rodar

### 1. Subir o RabbitMQ

```bash
cd infra
podman compose up -d
```

Painel de administração disponível em `http://localhost:15672` (guest / guest).

### 2. Rodar o backend

```bash
cd backend
python -m venv .venv

# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

pip install -r requirements.txt
python app.py
```

API disponível em `http://localhost:5000`.

### 3. Rodar o worker consumidor de eventos (Sprint 2)

Em outro terminal, com o RabbitMQ rodando:

```bash
cd backend
python worker.py
```

O worker consome as filas `fila.operador` e `fila.tecnico` e persiste cada evento na tabela `evento_log` (auditoria). Detalhes em [docs/sprint2/eventos.md](docs/sprint2/eventos.md).

### 4. Rodar os testes automatizados

```bash
cd backend

# 21 testes unitários (não exigem RabbitMQ)
python -m pytest tests/ -v

# Smoke test end-to-end (exige RabbitMQ rodando)
python tests/integration_rabbitmq.py
```

### 5. Rodar os apps Flutter

```bash
# App do operador
cd apps/operator
flutter pub get
flutter run

# App do técnico (em outro terminal ou emulador)
cd apps/technician
flutter pub get
flutter run
```

---

## Sprints

| Sprint | Foco | Entregas | Prazo |
|---|---|---|---|
| Sprint 1 ✅ | Proposta + Backend REST | Proposta de domínio, diagrama de arquitetura, endpoints CRUD, coleção Postman | 11/05/2026 |
| Sprint 2 ✅ | Integração RabbitMQ (MOM) + Auth | Publisher + consumer, 5 eventos, JWT/RBAC, [eventos.md](docs/sprint2/eventos.md), [autenticacao.md](docs/sprint2/autenticacao.md), [relatório de integração](docs/sprint2/relatorio-integracao.md) | 25/05/2026 |
| Sprint 3 | App Flutter — Operador | App funcional (3+ telas), integração REST, atualização assíncrona de estado | 15/06/2026 |
| Sprint 4 | App Flutter — Técnico + Entrega final | App prestador, fluxo ponta a ponta, screencast, relatório técnico final | 03/07/2026 |

---

## Tecnologias

| Camada | Tecnologia | Versão |
|---|---|---|
| Apps móveis | Flutter / Dart | 3.10+ / 3.x |
| Backend | Flask (Python) | 3.11+ |
| Banco de dados | SQLite | 3.x |
| Mensageria (MOM) | RabbitMQ | 3.12 |
| Infraestrutura | Podman Compose | 5.x+ |

---

## Disciplina

**Lab. de Desenvolvimento de Aplicações Móveis e Distribuídas**  
Engenharia de Software — 5º Período — PUC Minas  
Professores: Cleiton Silva Tavares e Cristiano de Macedo Neto  
Semestre: 1º Semestre 2026