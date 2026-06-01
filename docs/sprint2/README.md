# Sprint 2 — Integração com MOM + Autenticação

**Prazo:** 01/06/2026  
**Projeto:** PlantOS

---

## 🎬 Vídeo de Apresentação

Demonstração da Sprint 2 em execução (MOM, produtor/consumidor, JWT/RBAC e testes):
<https://youtu.be/p-_ed9gQMUk>

---

## Entregas

| Artefato | Arquivo | Descrição |
|---|---|---|
| Documentação dos Eventos | [eventos.md](eventos.md) | Catálogo completo dos 5 eventos, topologia RabbitMQ, payloads JSON, produtores e consumidores |
| Relatório de Integração | [relatorio-integracao.md](relatorio-integracao.md) | Escolha tecnológica, padrões EIP aplicados, evidências, desafios e soluções |
| Autenticação JWT | [autenticacao.md](autenticacao.md) | Entidade Usuario, JWT, bcrypt, RBAC, matriz de autorização |
| Worker Consumer | `../../backend/worker.py` + `../../backend/app/messaging/consumer.py` | Processo Python que consome eventos das filas e persiste em `evento_log` |
| Publisher | `../../backend/app/messaging/publisher.py` | Publica eventos no exchange `plantos.events` |
| Auditoria | tabela `evento_log` no SQLite | Histórico imutável de eventos efetivamente consumidos |
| Teste de Integração ao vivo | `../../backend/tests/integration_rabbitmq.py` | Script end-to-end que publica + consome + valida |
| Suite Pytest | `../../backend/tests/test_api.py` | 21 testes (auth, RBAC, OS, materiais, fluxo completo, eventos) |
| Coleção Postman atualizada | `../../backend/PlantOS.postman_collection.json` | Inclui `/auth/*`, header `Authorization: Bearer` e fluxo completo Sprint 2 |

---

## Como executar

### 1. Subir RabbitMQ

```powershell
cd infra
docker compose up -d            # (ou podman compose up -d)
```

Painel: <http://localhost:15672> (guest / guest)

### 2. Backend

```powershell
cd backend
pip install -r requirements.txt
python app.py
```

### 3. Worker consumidor (em outro terminal)

```powershell
cd backend
python worker.py
```

### 4. Validar tudo

```powershell
cd backend
python -m pytest tests/ -v                # 21 testes (rápido, sem broker)
python tests/integration_rabbitmq.py      # smoke test end-to-end com broker
```

---

## Aderência aos critérios de avaliação (20 pontos)

| Critério | Peso | Onde está atendido |
|---|---|---|
| MOM funcionando corretamente (evidência) | 25% (5,0) | Container `rabbitmq:3.12-management` em `infra/docker-compose.yml`; painel admin; tabela `evento_log`; script `integration_rabbitmq.py` |
| Implementação de produtor e consumidor | 30% (6,0) | Publisher em `app/messaging/publisher.py` chamado em 5 transições; Consumer em `app/messaging/consumer.py` + `worker.py` consumindo de 2 filas duráveis |
| Documentação dos eventos | 20% (4,0) | [eventos.md](eventos.md) — 5 eventos catalogados com payload, produtor, consumidor, fila, gatilho, semântica |
| Demonstração de assincronicidade real | 15% (3,0) | Produtor publica e segue em frente; consumer recebe sem chamada REST; mensagens persistentes em filas duráveis sobrevivem a offline |
| Clareza do relatório de integração | 10% (2,0) | [relatorio-integracao.md](relatorio-integracao.md) — escolhas, padrões EIP, desafios, métricas, próximos passos |

**Extra (preparação para Sprints 3 e 4):** entidade `Usuario` com JWT + RBAC,
garantindo que os eventos publicados carreguem `operador_id`/`tecnico_id`
**confiáveis** (extraídos do token, não do body).

