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

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/os` | Criar nova ordem de serviço |
| `GET` | `/os` | Listar todas as OS (filtros opcionais: `?status=aberta`) |
| `GET` | `/os/<id>` | Consultar OS por ID |
| `PATCH` | `/os/<id>/aceitar` | Técnico aceita a OS |
| `PATCH` | `/os/<id>/recusar` | Técnico recusa a OS |
| `PATCH` | `/os/<id>/iniciar` | Técnico inicia a execução da OS |
| `PATCH` | `/os/<id>/concluir` | Técnico conclui a OS com laudo |
| `POST` | `/os/<id>/materiais` | Registrar materiais utilizados na OS |
| `GET` | `/os/<id>/materiais` | Listar materiais de uma OS |

---

## Modelo de dados

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

O arquivo [`backend/PlantOS.postman_collection.json`](backend/PlantOS.postman_collection.json) contém a coleção completa para importar no Postman, organizada em três grupos:

1. **Ordens de Serviço** — CRUD + transições de status + casos de erro (400, 404, 409)
2. **Materiais** — Registro e listagem de materiais por OS
3. **Fluxo Completo** — Execução sequencial do ciclo de vida completo de uma OS (criar → aceitar → iniciar → registrar material → concluir com laudo → verificar)

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

| Sprint | Foco | Entregas | Prazo |
|---|---|---|---|
| Sprint 1 | Proposta + Backend REST | Proposta de domínio, diagrama de arquitetura, endpoints CRUD, coleção Postman | 11/05/2026 |
| Sprint 2 | Integração RabbitMQ (MOM) | Publisher/consumer, eventos assíncronos, documentação de eventos | 25/05/2026 |
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