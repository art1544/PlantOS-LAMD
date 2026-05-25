# Relatório de Integração com o MOM — Sprint 2

**Projeto:** PlantOS  
**Disciplina:** Lab. de Desenvolvimento de Aplicações Móveis e Distribuídas — PUC Minas  
**Sprint:** 2 — Integração com Middleware Orientado a Mensagens  
**Data:** Maio de 2026

---

## 1. Escolha da Tecnologia

Optou-se pelo **RabbitMQ 3.12** (com plugin de gerenciamento) como
*Message-Oriented Middleware* do PlantOS. Os principais critérios foram:

1. **Maturidade e adoção industrial** — Padrão de fato em sistemas orientados
   a eventos no ecossistema Python, com farta documentação e exemplos.
2. **Modelo AMQP 0-9-1** — Suporte nativo a *exchanges*, *bindings* e *queues*
   com semântica explícita (durability, persistence, prefetch, ack), o que se
   encaixa diretamente nos padrões clássicos descritos em Hohpe & Woolf (2003).
3. **Filas duráveis e mensagens persistentes** — Atributos essenciais para o
   cenário do PlantOS, em que apps móveis podem ficar offline por períodos
   prolongados e ainda assim devem receber notificações ao reconectar.
4. **Painel de administração web** — Permite inspecionar filas, mensagens e
   conexões em tempo real, facilitando a depuração e gerando evidência visual
   para a avaliação da sprint.
5. **Containerização trivial** — Imagem oficial `rabbitmq:3.12-management`
   pronta para uso via Docker / Podman Compose (`infra/docker-compose.yml`).

Alternativas consideradas (Redis Pub/Sub, Kafka) foram descartadas por
oferecerem semântica mais fraca (Redis: sem durabilidade nativa em pub/sub
clássico) ou complexidade desproporcional ao escopo (Kafka).

---

## 2. Arquitetura Adotada

A integração segue o padrão **Publish/Subscribe com Direct Exchange**:

* Um único exchange `plantos.events` do tipo `direct`.
* Duas filas duráveis (`fila.operador`, `fila.tecnico`) representando os dois
  perfis de assinantes do sistema.
* Cada evento é roteado para a fila apropriada via *routing key* (`os.criada`,
  `os.aceita`, `os.recusada`, `os.em_andamento`, `os.concluida`).
* Mensagens são publicadas com `delivery_mode=2` (persistente) e
  `content_type=application/json`.

> Detalhes completos do contrato dos eventos (payloads, gatilhos, produtor,
> consumidor) em [eventos.md](eventos.md).

A escolha de `direct` em vez de `topic` foi consciente: o conjunto de eventos
é fechado e bem definido (não há padrões hierárquicos a serem inferidos),
então a roteabilidade explícita por chave exata é mais simples e mais
eficiente.

---

## 3. Padrões de Integração Aplicados

Os seguintes padrões de Hohpe & Woolf (*Enterprise Integration Patterns*,
2003) foram aplicados explicitamente:

| Padrão | Onde está aplicado |
|---|---|
| **Publish-Subscribe Channel** | Exchange `plantos.events` distribui cada evento para todas as filas associadas |
| **Durable Subscriber** | Filas declaradas como `durable=true` sobrevivem a reinício do broker |
| **Guaranteed Delivery** | Mensagens persistentes (`delivery_mode=2`) + acknowledgments manuais (`basic_ack` apenas após processar) |
| **Message Channel (Typed Routing)** | Routing keys nomeadas (`os.<evento>`) atuam como contrato semântico entre produtor e consumidores |
| **Event Message** | O envelope `{evento, timestamp, dados}` carrega o tipo do evento e o snapshot do estado |

Também observa-se aderência ao princípio de **Event-Driven Architecture**
(Richardson, 2018): o backend é o produtor canônico de eventos de domínio, e
qualquer parte do sistema interessada em reagir a uma mudança de estado o
faz se inscrevendo em uma fila — sem qualquer chamada REST de volta.

---

## 4. Implementação no Backend

### 4.1 Produtor (`backend/app/messaging/publisher.py`)

A função `publish_event(routing_key, payload)` encapsula toda a interação com
o broker. É chamada pela camada de serviço (`OSService`) imediatamente após a
persistência bem-sucedida de cada transição de estado:

```python
# trecho de app/services/os_service.py
os_criada = OrdemServico.criar(...)
try:
    publish_event('os.criada', os_criada)
except Exception:
    pass  # falha do MOM não bloqueia a operação REST
```

O padrão "publicar após persistir" garante que **nenhum evento é publicado
para uma OS que não chegou ao banco**, evitando inconsistência. O custo é não
ter ainda *Outbox Pattern* completo (idealmente, a publicação também seria
transacional), mas para o escopo da disciplina a solução foi aceita.

### 4.2 Consumidor (`backend/app/messaging/consumer.py` + `worker.py`)

O consumidor é um **processo Python separado** (`python worker.py`) que:

1. Conecta-se ao broker e declara o exchange/filas idempotentemente.
2. Inscreve-se em ambas as filas com `prefetch_count=10`.
3. Para cada mensagem recebida, registra no console e persiste em uma tabela
   de auditoria `evento_log` (SQLite).
4. Faz acknowledge manual apenas após o processamento, garantindo
   *at-least-once delivery*.
5. Reconecta automaticamente em caso de queda do broker.

Esse worker cumpre duas funções:

* **Evidência didática** de que o ciclo produtor → broker → consumidor está
  funcionando (mensagem que sai do backend chega no consumidor sem qualquer
  chamada REST entre eles).
* **Trampolim arquitetural** para as Sprints 3 e 4, em que os apps Flutter
  implementarão consumidores equivalentes (com o mesmo contrato).

---

## 5. Evidência de Comunicação Assíncrona

A comunicação é demonstravelmente **assíncrona** e **desacoplada**:

1. O backend **publica e segue em frente** — não espera resposta nem
   confirmação do consumidor para retornar 200/201 ao cliente HTTP.
2. O consumidor **recebe a mensagem sem chamar o backend** — toda a
   informação necessária está no payload do evento.
3. Mensagens publicadas enquanto o consumidor estiver offline **permanecem
   na fila durável** e são entregues quando o consumidor reconecta.
4. Múltiplos consumidores poderiam ser ligados à mesma fila para escalar
   horizontalmente (o broker faria *round-robin*).

**Como reproduzir a evidência:**

```bash
# Terminal 1 — broker
cd infra && docker compose up -d

# Terminal 2 — backend
cd backend && python app.py

# Terminal 3 — consumer (deixe rodando)
cd backend && python worker.py

# Terminal 4 — gerar eventos via REST autenticada
# (ver Postman: pasta "Fluxo Completo Sprint 2")
```

Ou rodando o script de integração em um único passo:

```bash
cd backend && python tests/integration_rabbitmq.py
```

Esperado:

```
SUCESSO — 1 evento(s) consumido(s):
  • fila=fila.tecnico    key=os.criada           os_id=99999 recebido_em=2026-05-25T...
```

A tabela `evento_log` no SQLite passa a conter o histórico permanente dos
eventos consumidos, podendo ser consultada com:

```sql
SELECT id, fila, routing_key, recebido_em FROM evento_log ORDER BY id DESC;
```

---

## 6. Tratamento de Falhas

| Falha | Comportamento adotado | Justificativa |
|---|---|---|
| RabbitMQ indisponível no momento do publish | Backend captura a exceção e responde 200/201 normalmente ao cliente; evento é perdido | Decisão pragmática: o usuário não é penalizado por uma falha de infraestrutura. Em produção, evoluiríamos para Transactional Outbox. |
| RabbitMQ indisponível no startup do worker | Worker faz *backoff* e tenta reconectar a cada 3s indefinidamente | Garante que o sistema converge para um estado funcional sem intervenção manual |
| Mensagem inválida (JSON malformado) | Worker faz `basic_ack` e segue em frente, logando o descarte | Evita *poison message* travar a fila |
| Falha ao gravar `evento_log` | Worker loga o erro mas ainda faz `basic_ack` | Auditoria é importante mas não deve bloquear o pipeline principal |

---

## 7. Desafios Encontrados e Soluções

### 7.1 Desacoplamento produtor/consumidor sem perder *contract testing*

**Desafio:** Como garantir que o produtor e o consumidor concordam sobre o
formato do evento sem acoplá-los em código?

**Solução:** O envelope padronizado `{evento, timestamp, dados}` foi
documentado em [eventos.md](eventos.md) como contrato explícito. Testes
unitários no backend verificam que `publish_event` é chamado com as routing
keys corretas em cada transição (`tests/test_api.py::TestFluxoCompleto`).

### 7.2 Falha do MOM não pode bloquear o usuário

**Desafio:** Se o RabbitMQ cair, o operador ainda deve conseguir abrir OSs.

**Solução:** `try/except Exception: pass` na chamada de `publish_event` no
serviço. Em produção isso seria evoluído para *Transactional Outbox* (grava
o evento numa tabela junto com a OS, e um worker drena para o broker
periodicamente), mas para a sprint o tratamento permissivo é suficiente e
documentado.

### 7.3 Autenticação como pré-requisito para rastreabilidade dos eventos

**Desafio:** O payload do evento precisa ter um ator estável
(`operador_id`/`tecnico_id`) para os apps reagirem. Como evitar IDs
falsificados pelo cliente?

**Solução:** Foi introduzida nesta sprint a entidade `Usuario` com
autenticação JWT (RBAC por role). O `operador_id`/`tecnico_id` é
**derivado do token autenticado**, nunca lido do body. Isso garante
integridade da rastreabilidade dos eventos. Ver
[autenticacao.md](autenticacao.md).

### 7.4 Demonstrar o consumo sem precisar dos apps Flutter

**Desafio:** A Sprint 2 entrega apenas o lado do servidor, mas precisa
provar que o consumidor funciona.

**Solução:** Foi implementado um worker Python (`worker.py`) que assina as
mesmas filas que os apps assinarão na Sprint 3/4. Ele serve como evidência
e como referência arquitetural para a implementação Flutter.

---

## 8. Métricas e Verificação

| Métrica | Resultado |
|---|---|
| Eventos definidos no domínio | 5 (`os.criada`, `os.aceita`, `os.recusada`, `os.em_andamento`, `os.concluida`) |
| Filas duráveis configuradas | 2 (`fila.operador`, `fila.tecnico`) |
| Testes automatizados passando | **21/21** (`pytest backend/tests/`) |
| Testes que validam publicação de eventos | 4 (`TestOS::test_criar_os_publica_evento`, `TestFluxoCompleto::*`) |
| Cobertura de fluxos de erro REST | 401, 403, 400, 404, 409 — todos testados |

---

## 9. Próximos Passos (Sprints 3 e 4)

* Substituir o worker Python pelo consumidor AMQP embarcado no app Flutter
  do operador (Sprint 3) e do técnico (Sprint 4) usando o pacote
  `dart_amqp`.
* Implementar a estratégia *Sync-First* documentada em
  [docs/sprint1/arquitetura.md](../sprint1/arquitetura.md#83-fluxo-de-reconexão-sync-first-strategy) ao reconectar, descartando mensagens antigas anteriores ao último sync REST.
* Avaliar evolução para *Transactional Outbox* no backend caso seja exigida
  garantia exatamente-uma vez.

---

## 10. Referências

* HOHPE, G.; WOOLF, B. **Enterprise Integration Patterns.** Addison-Wesley, 2003.
* RICHARDSON, C. **Microservices Patterns.** Manning, 2018.
* RABBITMQ. *AMQP 0-9-1 Model Explained.* Disponível em: <https://www.rabbitmq.com/tutorials/amqp-concepts.html>. Acesso em: 25 maio 2026.
