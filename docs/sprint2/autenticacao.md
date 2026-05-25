# Autenticação e Autorização — Sprint 2

**Projeto:** PlantOS  
**Disciplina:** Lab. de Desenvolvimento de Aplicações Móveis e Distribuídas — PUC Minas  
**Sprint:** 2

---

## 1. Motivação

Na Sprint 1, as rotas da API aceitavam `operador_id` e `tecnico_id` arbitrários
no body — qualquer cliente podia se passar por qualquer usuário. Para que os
eventos publicados no RabbitMQ (Sprint 2) carreguem **identidades confiáveis**
e para preparar o sistema para as Sprints 3 e 4, foi introduzida a entidade
**Usuário** com autenticação **JWT** e autorização **baseada em papéis (RBAC)**.

---

## 2. Modelo de Dados

Tabela `usuario` (já estava prevista no banco; agora é efetivamente usada):

| Coluna | Tipo | Restrição | Descrição |
|---|---|---|---|
| `id` | INTEGER | PK, AUTOINCREMENT | Identificador único |
| `nome` | TEXT | NOT NULL | Nome completo |
| `login` | TEXT | NOT NULL, UNIQUE | Identificador de acesso |
| `senha` | TEXT | NOT NULL | **Hash bcrypt** (nunca em texto puro) |
| `role` | TEXT | CHECK IN (`operador`,`tecnico`,`admin`) | Papel do usuário |
| `ativo` | INTEGER | DEFAULT 1 | Soft delete |
| `criado_em` | DATETIME | DEFAULT CURRENT_TIMESTAMP | — |
| `atualizado_em` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Atualizado via trigger |

A coluna `senha` **nunca** é retornada nas respostas HTTP — o helper
`Usuario.to_public_dict()` remove o campo antes da serialização.

---

## 3. Endpoints de Autenticação

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| `POST` | `/auth/register` | Público | Cadastra novo usuário (escolhe role no body) |
| `POST` | `/auth/login` | Público | Recebe `login`/`senha`, retorna `token` JWT |
| `GET`  | `/auth/me` | Autenticado | Retorna o usuário associado ao token |
| `GET`  | `/auth/usuarios` | Admin | Lista todos os usuários (sem senha) |

### 3.1 Registro

```http
POST /auth/register
Content-Type: application/json

{
  "nome": "Carla Operadora",
  "login": "carla",
  "senha": "minhasenha123",
  "role": "operador"
}
```

Respostas:

* `201 Created` — `{id, nome, login, role, ativo, criado_em, atualizado_em}`
* `400 Bad Request` — Campo obrigatório ausente, role inválido, senha curta (<6)
* `409 Conflict` — Login já cadastrado

### 3.2 Login

```http
POST /auth/login
Content-Type: application/json

{ "login": "carla", "senha": "minhasenha123" }
```

Resposta `200 OK`:

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.....",
  "usuario": { "id": 3, "nome": "Carla Operadora", "login": "carla", "role": "operador", "ativo": 1, "criado_em": "...", "atualizado_em": "..." }
}
```

Falhas:

* `400` campos ausentes
* `401` credenciais inválidas
* `403` usuário inativo

---

## 4. Uso do Token

Inclua o header em todas as requisições protegidas:

```http
Authorization: Bearer <token>
```

O token expira em **8 horas** por padrão (configurável via variável de ambiente
`JWT_EXPIRATION_HOURS`).

### Claims do JWT

| Claim | Valor |
|---|---|
| `sub` | ID numérico do usuário (string) |
| `login` | login do usuário |
| `role` | `operador` | `tecnico` | `admin` |
| `iat` | data/hora de emissão |
| `exp` | data/hora de expiração |

---

## 5. Matriz de Autorização (RBAC)

| Endpoint | Operador | Técnico | Admin |
|---|:-:|:-:|:-:|
| `POST   /auth/register` | público | público | público |
| `POST   /auth/login` | público | público | público |
| `GET    /auth/me` | ✅ | ✅ | ✅ |
| `GET    /auth/usuarios` | ❌ | ❌ | ✅ |
| `POST   /os` | ✅ | ❌ | ✅ |
| `GET    /os` | ✅ (apenas as próprias) | ✅ | ✅ |
| `GET    /os/<id>` | ✅ | ✅ | ✅ |
| `PATCH  /os/<id>/aceitar` | ❌ | ✅ | ✅ |
| `PATCH  /os/<id>/recusar` | ❌ | ✅ | ✅ |
| `PATCH  /os/<id>/iniciar` | ❌ | ✅ | ✅ |
| `PATCH  /os/<id>/concluir` | ❌ | ✅ | ✅ |
| `POST   /os/<id>/materiais` | ❌ | ✅ | ✅ |
| `GET    /os/<id>/materiais` | ✅ | ✅ | ✅ |

**Regras-chave:**

* O `operador_id` da OS é **sempre** preenchido com `user-<id>` extraído do
  token (não pode ser falsificado via body).
* O `tecnico_id` da OS é **sempre** preenchido com `user-<id>` extraído do
  token nas rotas de transição de status.
* Operadores que listam `/os` recebem apenas suas próprias OSs (filtro
  automático). Técnicos veem todas.

---

## 6. Implementação

| Arquivo | Responsabilidade |
|---|---|
| `backend/app/auth.py` | Geração/validação JWT, decorators `@requires_auth` e `@requires_role`, bcrypt |
| `backend/app/models/usuario.py` | CRUD da tabela `usuario` |
| `backend/app/services/auth_service.py` | Regras de registro e login |
| `backend/app/routes/auth_routes.py` | Blueprint `/auth/*` |
| `backend/app/routes/os_routes.py` | Aplica decorators nas rotas de OS |

### 6.1 Hash de Senha (`bcrypt`)

```python
hashed = bcrypt.hashpw(senha.encode(), bcrypt.gensalt())  # cost factor padrão 12
bcrypt.checkpw(senha.encode(), hashed)                    # constante-tempo
```

### 6.2 Geração do Token

```python
payload = {'sub': str(user_id), 'login': login, 'role': role,
           'iat': now, 'exp': now + timedelta(hours=8)}
jwt.encode(payload, JWT_SECRET, algorithm='HS256')
```

### 6.3 Proteção das Rotas

```python
@os_bp.route('/os', methods=['POST'])
@requires_role('operador', 'admin')
def criar_os():
    dados = request.get_json(silent=True) or {}
    dados['operador_id'] = f"user-{g.current_user['id']}"
    ...
```

---

## 7. Aspectos de Segurança

| Tópico | Tratamento adotado |
|---|---|
| Armazenamento de senha | bcrypt (cost factor 12) — **nunca em texto puro** |
| Transporte do token | Header `Authorization: Bearer`. **Recomenda-se HTTPS em produção.** |
| Segredo de assinatura | Variável `JWT_SECRET` (default apenas para dev). Em produção, deve ser longa e secreta. |
| Expiração | 8h padrão, configurável. Após expirar, o cliente deve reautenticar. |
| Confidencialidade do hash | A senha hash é removida de toda resposta HTTP por `Usuario.to_public_dict()`. |
| Vazamento de informação no login | Mensagem genérica "Credenciais inválidas" para login e senha errados (mitiga user-enumeration). |
| Injeção SQL | Todos os acessos usam *parameterized queries* (`?`), sem string concatenation. |
| Force brute em login | (Pendente para Sprint 4) Rate limiting a ser adicionado se necessário. |

---

## 8. Variáveis de Ambiente

| Variável | Default | Descrição |
|---|---|---|
| `JWT_SECRET` | `plantos-dev-secret-change-in-production` | **Trocar em produção** |
| `JWT_EXPIRATION_HOURS` | `8` | Tempo de vida do token |
| `RABBITMQ_HOST` | `localhost` | Host do broker (uso compartilhado com a Sprint 2) |
