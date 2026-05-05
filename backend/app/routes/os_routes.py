from flask import Blueprint, request, jsonify
from app.services.os_service import OSService

os_bp = Blueprint('os', __name__)


@os_bp.route('/os', methods=['POST'])
def criar_os():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Body JSON obrigatório"}), 400

    os_criada, erro = OSService.criar_os(dados)
    if erro:
        return jsonify({"erro": erro}), 400

    return jsonify(os_criada), 201


@os_bp.route('/os', methods=['GET'])
def listar_os():
    status = request.args.get('status')
    operador_id = request.args.get('operador_id')
    resultado = OSService.listar_os(status=status, operador_id=operador_id)
    return jsonify(resultado), 200


@os_bp.route('/os/<int:os_id>', methods=['GET'])
def buscar_os(os_id):
    os_encontrada = OSService.buscar_os(os_id)
    if not os_encontrada:
        return jsonify({"erro": "OS não encontrada"}), 404
    return jsonify(os_encontrada), 200


@os_bp.route('/os/<int:os_id>/aceitar', methods=['PATCH'])
def aceitar_os(os_id):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Body JSON obrigatório"}), 400

    resultado, erro, status_code = OSService.transicionar_status(
        os_id=os_id,
        novo_status='aceita',
        tecnico_id=dados.get('tecnico_id')
    )

    if erro:
        return jsonify({"erro": erro}), status_code
    return jsonify(resultado), 200


@os_bp.route('/os/<int:os_id>/recusar', methods=['PATCH'])
def recusar_os(os_id):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Body JSON obrigatório"}), 400

    resultado, erro, status_code = OSService.transicionar_status(
        os_id=os_id,
        novo_status='recusada',
        tecnico_id=dados.get('tecnico_id')
    )

    if erro:
        return jsonify({"erro": erro}), status_code
    return jsonify(resultado), 200


@os_bp.route('/os/<int:os_id>/iniciar', methods=['PATCH'])
def iniciar_os(os_id):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Body JSON obrigatório"}), 400

    resultado, erro, status_code = OSService.transicionar_status(
        os_id=os_id,
        novo_status='em_andamento',
        tecnico_id=dados.get('tecnico_id')
    )

    if erro:
        return jsonify({"erro": erro}), status_code
    return jsonify(resultado), 200


@os_bp.route('/os/<int:os_id>/concluir', methods=['PATCH'])
def concluir_os(os_id):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Body JSON obrigatório"}), 400

    resultado, erro, status_code = OSService.transicionar_status(
        os_id=os_id,
        novo_status='concluida',
        tecnico_id=dados.get('tecnico_id'),
        laudo=dados.get('laudo')
    )

    if erro:
        return jsonify({"erro": erro}), status_code
    return jsonify(resultado), 200


@os_bp.route('/os/<int:os_id>/materiais', methods=['POST'])
def registrar_material(os_id):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Body JSON obrigatório"}), 400

    resultado, erro, status_code = OSService.registrar_material(os_id, dados)
    if erro:
        return jsonify({"erro": erro}), status_code
    return jsonify(resultado), status_code


@os_bp.route('/os/<int:os_id>/materiais', methods=['GET'])
def listar_materiais(os_id):
    resultado, erro, status_code = OSService.listar_materiais(os_id)
    if erro:
        return jsonify({"erro": erro}), status_code
    return jsonify(resultado), 200
