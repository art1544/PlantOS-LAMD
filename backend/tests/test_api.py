"""
Suite de testes automatizados — PlantOS Sprint 2.

Cobertura:
  * Autenticação: registro, login, /me, controle de acesso por role
  * Ordens de Serviço: CRUD, transições válidas/inválidas, 401/403/404/409
  * Materiais: registro, listagem, validações
  * Eventos: publish_event é chamado nos momentos corretos do fluxo
  * Fluxo completo ponta-a-ponta (operador → técnico → conclusão)

Os testes NÃO exigem RabbitMQ rodando: o `publish_event` é mockado para
verificar QUAIS eventos foram publicados, sem realmente conectar via AMQP.
"""

from __future__ import annotations

import os
import sys
import tempfile
import importlib
from unittest.mock import patch

import pytest

# Garante que o pacote `app` seja importável a partir de backend/
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


@pytest.fixture()
def app_client(monkeypatch):
    """Cria uma app Flask isolada com banco SQLite em arquivo temporário."""
    tmp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp_db.close()

    # Redireciona o caminho do banco antes de importar módulos que o usam
    import app.database as database_mod
    monkeypatch.setattr(database_mod, 'DATABASE_PATH', tmp_db.name)

    # Recarrega módulos que possam ter cacheado o path antigo
    for modname in [
        'app.models.usuario',
        'app.models.ordem_servico',
        'app.models.material',
    ]:
        if modname in sys.modules:
            importlib.reload(sys.modules[modname])

    # Mock do publisher: evita conexão real ao RabbitMQ e captura eventos
    eventos_publicados: list[tuple[str, dict]] = []

    def _fake_publish(routing_key, payload):
        eventos_publicados.append((routing_key, payload))

    monkeypatch.setattr('app.messaging.publisher.publish_event', _fake_publish)
    monkeypatch.setattr('app.services.os_service.publish_event', _fake_publish)
    # setup_queues também não deve abrir conexão durante o create_app
    monkeypatch.setattr('app.messaging.publisher.setup_queues', lambda: None)

    from app import create_app
    app = create_app()
    app.config['TESTING'] = True

    client = app.test_client()
    client.eventos = eventos_publicados  # type: ignore[attr-defined]

    yield client

    os.unlink(tmp_db.name)


# ---------- Helpers ----------


def _register(client, login, senha, role, nome=None):
    return client.post('/auth/register', json={
        'nome': nome or f'Usuario {login}',
        'login': login,
        'senha': senha,
        'role': role,
    })


def _login(client, login, senha):
    resp = client.post('/auth/login', json={'login': login, 'senha': senha})
    assert resp.status_code == 200, resp.get_json()
    return resp.get_json()['token']


def _auth_header(token):
    return {'Authorization': f'Bearer {token}'}


def _seed_users(client):
    _register(client, 'op1', 'senha123', 'operador', nome='Operador Um')
    _register(client, 'tec1', 'senha123', 'tecnico', nome='Tecnico Um')
    op_token = _login(client, 'op1', 'senha123')
    tec_token = _login(client, 'tec1', 'senha123')
    return op_token, tec_token


# ---------- Autenticação ----------


class TestAuth:

    def test_health(self, app_client):
        r = app_client.get('/health')
        assert r.status_code == 200
        assert r.get_json()['status'] == 'ok'

    def test_registrar_usuario(self, app_client):
        r = _register(app_client, 'novo', 'segredo1', 'operador')
        assert r.status_code == 201
        body = r.get_json()
        assert body['login'] == 'novo'
        assert body['role'] == 'operador'
        assert 'senha' not in body  # nunca expor hash

    def test_registrar_duplicado_409(self, app_client):
        _register(app_client, 'dup', 'segredo1', 'operador')
        r = _register(app_client, 'dup', 'segredo1', 'operador')
        assert r.status_code == 409

    def test_registrar_role_invalido(self, app_client):
        r = _register(app_client, 'x', 'segredo1', 'hacker')
        assert r.status_code == 400

    def test_registrar_senha_curta(self, app_client):
        r = _register(app_client, 'x', '123', 'operador')
        assert r.status_code == 400

    def test_login_credenciais_invalidas(self, app_client):
        _register(app_client, 'u1', 'segredo1', 'operador')
        r = app_client.post('/auth/login', json={'login': 'u1', 'senha': 'errada'})
        assert r.status_code == 401

    def test_me_sem_token(self, app_client):
        r = app_client.get('/auth/me')
        assert r.status_code == 401

    def test_me_com_token(self, app_client):
        _register(app_client, 'u1', 'segredo1', 'operador')
        token = _login(app_client, 'u1', 'segredo1')
        r = app_client.get('/auth/me', headers=_auth_header(token))
        assert r.status_code == 200
        assert r.get_json()['login'] == 'u1'

    def test_token_invalido(self, app_client):
        r = app_client.get('/auth/me', headers={'Authorization': 'Bearer abc.invalid.token'})
        assert r.status_code == 401


# ---------- Autorização (RBAC) ----------


class TestRBAC:

    def test_operador_nao_pode_aceitar_os(self, app_client):
        op_token, tec_token = _seed_users(app_client)
        os_id = self._criar_os(app_client, op_token)
        r = app_client.patch(f'/os/{os_id}/aceitar', headers=_auth_header(op_token), json={})
        assert r.status_code == 403

    def test_tecnico_nao_pode_criar_os(self, app_client):
        _, tec_token = _seed_users(app_client)
        r = app_client.post('/os', headers=_auth_header(tec_token), json={
            'titulo': 't', 'descricao': 'd', 'setor': 's',
            'equipamento': 'e', 'prioridade': 'alta',
        })
        assert r.status_code == 403

    def _criar_os(self, client, token):
        r = client.post('/os', headers=_auth_header(token), json={
            'titulo': 'Teste', 'descricao': 'desc', 'setor': 'A',
            'equipamento': 'eq', 'prioridade': 'media',
        })
        assert r.status_code == 201, r.get_json()
        return r.get_json()['id']


# ---------- Ordens de Serviço ----------


class TestOS:

    def test_criar_os_publica_evento(self, app_client):
        op_token, _ = _seed_users(app_client)
        r = app_client.post('/os', headers=_auth_header(op_token), json={
            'titulo': 'Vazamento', 'descricao': 'd', 'setor': 'A',
            'equipamento': 'V-1', 'prioridade': 'alta',
        })
        assert r.status_code == 201
        body = r.get_json()
        assert body['status'] == 'aberta'
        assert body['operador_id'].startswith('user-')

        # Evento os.criada foi publicado
        eventos = [e[0] for e in app_client.eventos]
        assert 'os.criada' in eventos

    def test_criar_os_campo_obrigatorio_ausente(self, app_client):
        op_token, _ = _seed_users(app_client)
        r = app_client.post('/os', headers=_auth_header(op_token), json={'titulo': 'x'})
        assert r.status_code == 400

    def test_criar_os_prioridade_invalida(self, app_client):
        op_token, _ = _seed_users(app_client)
        r = app_client.post('/os', headers=_auth_header(op_token), json={
            'titulo': 't', 'descricao': 'd', 'setor': 's',
            'equipamento': 'e', 'prioridade': 'xx',
        })
        assert r.status_code == 400

    def test_buscar_inexistente_404(self, app_client):
        op_token, _ = _seed_users(app_client)
        r = app_client.get('/os/9999', headers=_auth_header(op_token))
        assert r.status_code == 404

    def test_transicao_invalida_409(self, app_client):
        op_token, tec_token = _seed_users(app_client)
        os_id = _criar_os_default(app_client, op_token)
        # tenta iniciar antes de aceitar
        r = app_client.patch(f'/os/{os_id}/iniciar', headers=_auth_header(tec_token), json={})
        assert r.status_code == 409

    def test_concluir_sem_laudo_400(self, app_client):
        op_token, tec_token = _seed_users(app_client)
        os_id = _criar_os_default(app_client, op_token)
        app_client.patch(f'/os/{os_id}/aceitar', headers=_auth_header(tec_token), json={})
        app_client.patch(f'/os/{os_id}/iniciar', headers=_auth_header(tec_token), json={})
        r = app_client.patch(f'/os/{os_id}/concluir', headers=_auth_header(tec_token), json={})
        assert r.status_code == 400


# ---------- Materiais ----------


class TestMateriais:

    def test_registrar_e_listar(self, app_client):
        op_token, tec_token = _seed_users(app_client)
        os_id = _criar_os_default(app_client, op_token)

        r = app_client.post(f'/os/{os_id}/materiais', headers=_auth_header(tec_token),
                            json={'nome': 'Parafuso', 'quantidade': 5})
        assert r.status_code == 201

        r = app_client.get(f'/os/{os_id}/materiais', headers=_auth_header(op_token))
        assert r.status_code == 200
        assert len(r.get_json()) == 1

    def test_quantidade_invalida(self, app_client):
        op_token, tec_token = _seed_users(app_client)
        os_id = _criar_os_default(app_client, op_token)
        r = app_client.post(f'/os/{os_id}/materiais', headers=_auth_header(tec_token),
                            json={'nome': 'x', 'quantidade': 0})
        assert r.status_code == 400


# ---------- Fluxo ponta-a-ponta ----------


class TestFluxoCompleto:

    def test_ciclo_completo_publica_todos_eventos(self, app_client):
        op_token, tec_token = _seed_users(app_client)
        os_id = _criar_os_default(app_client, op_token)

        r = app_client.patch(f'/os/{os_id}/aceitar', headers=_auth_header(tec_token), json={})
        assert r.status_code == 200 and r.get_json()['status'] == 'aceita'

        r = app_client.patch(f'/os/{os_id}/iniciar', headers=_auth_header(tec_token), json={})
        assert r.status_code == 200 and r.get_json()['status'] == 'em_andamento'

        app_client.post(f'/os/{os_id}/materiais', headers=_auth_header(tec_token),
                        json={'nome': 'Gaxeta', 'quantidade': 2})

        r = app_client.patch(f'/os/{os_id}/concluir', headers=_auth_header(tec_token),
                             json={'laudo': 'Reparo concluído com sucesso.'})
        assert r.status_code == 200 and r.get_json()['status'] == 'concluida'

        eventos_publicados = [e[0] for e in app_client.eventos]
        for esperado in ['os.criada', 'os.aceita', 'os.em_andamento', 'os.concluida']:
            assert esperado in eventos_publicados, f"Evento {esperado} não foi publicado"

    def test_recusar(self, app_client):
        op_token, tec_token = _seed_users(app_client)
        os_id = _criar_os_default(app_client, op_token)
        r = app_client.patch(f'/os/{os_id}/recusar', headers=_auth_header(tec_token), json={})
        assert r.status_code == 200
        eventos = [e[0] for e in app_client.eventos]
        assert 'os.recusada' in eventos


# ---------- Helpers compartilhados ----------


def _criar_os_default(client, token):
    r = client.post('/os', headers=_auth_header(token), json={
        'titulo': 'Teste', 'descricao': 'desc', 'setor': 'A',
        'equipamento': 'eq', 'prioridade': 'media',
    })
    assert r.status_code == 201
    return r.get_json()['id']
