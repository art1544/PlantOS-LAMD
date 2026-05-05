# Backend — PlantOS

API REST em Flask (Python 3.11+) que gerencia Ordens de Serviço para plantas industriais.

## Estrutura

```
backend/
├── app.py                # Ponto de entrada
├── requirements.txt      # Dependências Python
├── plantos.db            # SQLite (criado automaticamente)
└── app/
    ├── database.py       # Conexão SQLite + init_db()
    ├── models/
    │   ├── ordem_servico.py
    │   └── material.py
    ├── routes/
    │   └── os_routes.py  # Blueprints REST
    ├── services/
    │   └── os_service.py # Lógica de negócio
    └── messaging/
        └── publisher.py  # Publica eventos no RabbitMQ
```

## Como rodar

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
python app.py
```

API disponível em `http://localhost:5000`.

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| POST | /os | Criar nova OS |
| GET | /os | Listar OS (filtros: ?status, ?operador_id) |
| GET | /os/:id | Consultar OS por ID |
| PATCH | /os/:id/aceitar | Técnico aceita a OS |
| PATCH | /os/:id/recusar | Técnico recusa a OS |
| PATCH | /os/:id/iniciar | Técnico inicia execução |
| PATCH | /os/:id/concluir | Técnico conclui com laudo |
| POST | /os/:id/materiais | Registrar material utilizado |
| GET | /os/:id/materiais | Listar materiais de uma OS |

## Variáveis de ambiente

| Variável | Default | Descrição |
|---|---|---|
| RABBITMQ_HOST | localhost | Host do RabbitMQ |
| FLASK_PORT | 5000 | Porta da API |
