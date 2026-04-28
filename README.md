# PlantOS

Sistema distribuído de ordens de serviço para plantas industriais, desenvolvido como projeto integrador da disciplina de Laboratório de Desenvolvimento de Aplicações Móveis e Distribuídas — PUC Minas, 1º Semestre 2026.

---

## Sobre o projeto

O PlantOS permite que operadores de uma planta industrial abram ordens de serviço (OS) relatando falhas ou necessidades de manutenção, e que técnicos recebam, aceitem e executem essas ordens de forma assíncrona, registrando os materiais utilizados e emitindo um laudo ao final.

A arquitetura é orientada a eventos (EDA): toda mudança de estado de uma OS gera um evento publicado no RabbitMQ, que notifica os aplicativos interessados sem necessidade de polling contínuo.

---

## Perfis de usuário

| Perfil | Descrição |
|---|---|
| **Operador** | Abre OS, acompanha o status em tempo real, recebe notificação de conclusão |
| **Técnico** | Recebe novas OS, aceita ou recusa, registra materiais usados, conclui com laudo |

---

## Arquitetura

```
Operador (Flutter)
    │  REST
    ▼
Backend Flask ──── RabbitMQ ────► Técnico (Flutter)
    │                                    │
    ▼                                    ▼
 SQLite                          Aceita / Conclui OS
    │                                    │
    └──────────── RabbitMQ ◄─────────────┘
                     │
                     ▼
             Operador notificado
```

**Componentes:**
- `apps/operator` — App Flutter do operador
- `apps/technician` — App Flutter do técnico
- `backend` — API REST em Flask (Python)
- RabbitMQ — Middleware orientado a mensagens (MOM)
- SQLite — Banco de dados local

---

## Fluxo de eventos

| Evento | Produzido quando | Consumidor |
|---|---|---|
| `os.criada` | Operador abre nova OS | App do técnico |
| `os.aceita` | Técnico aceita a OS | App do operador |
| `os.recusada` | Técnico recusa a OS | App do operador |
| `os.concluida` | Técnico conclui com laudo | App do operador |

---

## Estrutura do repositório

```
plantos/
├── backend/          # API REST Flask + publisher/consumer RabbitMQ
├── apps/
│   ├── operator/     # Flutter — app do operador
│   └── technician/   # Flutter — app do técnico
├── infra/            # docker-compose.yml (RabbitMQ)
├── docs/             # Entregas por sprint
│   ├── sprint1/
│   ├── sprint2/
│   ├── sprint3/
│   └── sprint4/
└── README.md
```

---

## Pré-requisitos

- Python 3.11+
- Flutter 3.10+ / Dart 3.x
- Docker e Docker Compose

---

## Como rodar

### 1. Subir o RabbitMQ

```bash
cd infra
docker-compose up -d
```

Painel de administração disponível em `http://localhost:15672` (guest / guest).

### 2. Rodar o backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

API disponível em `http://localhost:5000`.

### 3. Rodar os apps Flutter

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

| Sprint | Foco | Prazo |
|---|---|---|
| Sprint 1 | Proposta + Backend REST | 11/05/2026 |
| Sprint 2 | Integração RabbitMQ (MOM) | 25/05/2026 |
| Sprint 3 | App Flutter — Operador | 15/06/2026 |
| Sprint 4 | App Flutter — Técnico + entrega final | 03/07/2026 |

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Apps móveis | Flutter / Dart |
| Backend | Flask (Python) |
| Banco de dados | SQLite |
| Mensageria | RabbitMQ |
| Infraestrutura | Docker Compose |

---

## Disciplina

**Lab. de Desenvolvimento de Aplicações Móveis e Distribuídas**
Engenharia de Software — 5º Período — PUC Minas
Professores: Cleiton Silva Tavares e Cristiano de Macedo Neto