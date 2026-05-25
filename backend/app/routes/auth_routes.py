"""Blueprint de autenticação: registro, login e perfil do usuário autenticado."""

from flask import Blueprint, request, jsonify, g

from app.auth import requires_auth, requires_role
from app.services.auth_service import AuthService
from app.models.usuario import Usuario


auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    dados = request.get_json(silent=True) or {}
    resultado, erro, status_code = AuthService.registrar(dados)
    if erro:
        return jsonify({"erro": erro}), status_code
    return jsonify(resultado), status_code


@auth_bp.route('/login', methods=['POST'])
def login():
    dados = request.get_json(silent=True) or {}
    resultado, erro, status_code = AuthService.login(dados)
    if erro:
        return jsonify({"erro": erro}), status_code
    return jsonify(resultado), status_code


@auth_bp.route('/me', methods=['GET'])
@requires_auth
def me():
    user = Usuario.buscar_por_id(g.current_user['id'])
    if not user:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    return jsonify(Usuario.to_public_dict(user)), 200


@auth_bp.route('/usuarios', methods=['GET'])
@requires_role('admin')
def listar_usuarios():
    return jsonify(Usuario.listar()), 200
