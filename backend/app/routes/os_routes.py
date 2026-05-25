"""Rotas REST de Ordens de Serviço.

Sprint 2: todas as rotas exigem autenticação JWT.

* `POST /os`                       — apenas perfil `operador`. operador_id é
                                     extraído do token (não pode ser falsificado).
* `GET /os`, `GET /os/<id>`        — qualquer usuário autenticado.
* `PATCH /os/<id>/aceitar|recusar|
  iniciar|concluir`                — apenas perfil `tecnico`. tecnico_id é
                                     extraído do token.
* `POST /os/<id>/materiais`        — apenas perfil `tecnico`.
* `GET  /os/<id>/materiais`        — qualquer usuário autenticado.
"""

from flask import Blueprint, request, jsonify, g

from app.auth import requires_auth, requires_role
from app.services.os_service import OSService

os_bp = Blueprint('os', __name__)


def _current_actor_id() -> str:
    """ID estável para usar como operador_id/tecnico_id no domínio."""
    return f"user-{g.current_user['id']}"


@os_bp.route('/os', methods=['POST'])
@requires_role('operador', 'admin')
def criar_os():
    dados = request.get_json(silent=True) or {}
    dados['operador_id'] = _current_actor_id()

    os_criada, erro = OSService.criar_os(dados)
    if erro:
        return jsonify({"erro": erro}), 400
    return jsonify(os_criada), 201


@os_bp.route('/os', methods=['GET'])
@requires_auth
def listar_os():
    status = request.args.get('status')
    operador_id = request.args.get('operador_id')

    if g.current_user['role'] == 'operador':
        operador_id = _current_actor_id()

    resultado = OSService.listar_os(status=status, operador_id=operador_id)
    return jsonify(resultado), 200


@os_bp.route('/os/<int:os_id>', methods=['GET'])
@requires_auth
def buscar_os(os_id):
    os_encontrada = OSService.buscar_os(os_id)
    if not os_encontrada:
        return jsonify({"erro": "OS não encontrada"}), 404
    return jsonify(os_encontrada), 200


def _transicionar(os_id: int, novo_status: str, exigir_laudo: bool = False):
    dados = request.get_json(silent=True) or {}
    resultado, erro, status_code = OSService.transicionar_status(
        os_id=os_id,
        novo_status=novo_status,
        tecnico_id=_current_actor_id(),
        laudo=dados.get('laudo') if exigir_laudo else None,
    )
    if erro:
        return jsonify({"erro": erro}), status_code
    return jsonify(resultado), 200


@os_bp.route('/os/<int:os_id>/aceitar', methods=['PATCH'])
@requires_role('tecnico', 'admin')
def aceitar_os(os_id):
    return _transicionar(os_id, 'aceita')


@os_bp.route('/os/<int:os_id>/recusar', methods=['PATCH'])
@requires_role('tecnico', 'admin')
def recusar_os(os_id):
    return _transicionar(os_id, 'recusada')


@os_bp.route('/os/<int:os_id>/iniciar', methods=['PATCH'])
@requires_role('tecnico', 'admin')
def iniciar_os(os_id):
    return _transicionar(os_id, 'em_andamento')


@os_bp.route('/os/<int:os_id>/concluir', methods=['PATCH'])
@requires_role('tecnico', 'admin')
def concluir_os(os_id):
    return _transicionar(os_id, 'concluida', exigir_laudo=True)


@os_bp.route('/os/<int:os_id>/materiais', methods=['POST'])
@requires_role('tecnico', 'admin')
def registrar_material(os_id):
    dados = request.get_json(silent=True) or {}
    resultado, erro, status_code = OSService.registrar_material(os_id, dados)
    if erro:
        return jsonify({"erro": erro}), status_code
    return jsonify(resultado), status_code


@os_bp.route('/os/<int:os_id>/materiais', methods=['GET'])
@requires_auth
def listar_materiais(os_id):
    resultado, erro, status_code = OSService.listar_materiais(os_id)
    if erro:
        return jsonify({"erro": erro}), status_code
    return jsonify(resultado), 200

