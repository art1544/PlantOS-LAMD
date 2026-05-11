from app.models.ordem_servico import OrdemServico
from app.models.material import Material
from app.messaging.publisher import publish_event


TRANSICOES_VALIDAS = {
    'aberta': ['aceita', 'recusada'],
    'aceita': ['em_andamento'],
    'em_andamento': ['concluida'],
}

EVENTO_POR_STATUS = {
    'aceita': 'os.aceita',
    'recusada': 'os.recusada',
    'em_andamento': 'os.em_andamento',
    'concluida': 'os.concluida',
}


class OSService:

    @staticmethod
    def criar_os(dados):
        campos_obrigatorios = ['titulo', 'descricao', 'setor', 'equipamento', 'prioridade', 'operador_id']
        for campo in campos_obrigatorios:
            if campo not in dados or not dados[campo]:
                return None, f"Campo obrigatório ausente: {campo}"

        try:
            os_criada = OrdemServico.criar(
                titulo=dados['titulo'],
                descricao=dados['descricao'],
                setor=dados['setor'],
                equipamento=dados['equipamento'],
                prioridade=dados['prioridade'],
                operador_id=dados['operador_id']
            )
        except ValueError as e:
            return None, str(e)

        try:
            publish_event('os.criada', os_criada)
        except Exception:
            pass

        return os_criada, None

    @staticmethod
    def listar_os(status=None, operador_id=None):
        return OrdemServico.listar(status=status, operador_id=operador_id)

    @staticmethod
    def buscar_os(os_id):
        return OrdemServico.buscar_por_id(os_id)

    @staticmethod
    def transicionar_status(os_id, novo_status, tecnico_id=None, laudo=None):
        os_atual = OrdemServico.buscar_por_id(os_id)
        if not os_atual:
            return None, "OS não encontrada", 404

        status_atual = os_atual['status']
        transicoes_permitidas = TRANSICOES_VALIDAS.get(status_atual, [])

        if novo_status not in transicoes_permitidas:
            erro = f"Transição inválida. Status atual: {status_atual}. Esperado: {', '.join(transicoes_permitidas) if transicoes_permitidas else 'nenhuma transição possível'}"
            return None, erro, 409

        if not tecnico_id:
            return None, "Campo obrigatório ausente: tecnico_id", 400

        if novo_status == 'concluida' and not laudo:
            return None, "Campo obrigatório ausente: laudo", 400

        os_atualizada = OrdemServico.atualizar_status(
            os_id=os_id,
            novo_status=novo_status,
            tecnico_id=tecnico_id,
            laudo=laudo
        )

        try:
            routing_key = EVENTO_POR_STATUS[novo_status]
            publish_event(routing_key, os_atualizada)
        except Exception:
            pass

        return os_atualizada, None, 200

    @staticmethod
    def registrar_material(os_id, dados):
        os_existente = OrdemServico.buscar_por_id(os_id)
        if not os_existente:
            return None, "OS não encontrada", 404

        if 'nome' not in dados or not dados['nome']:
            return None, "Campo obrigatório ausente: nome", 400
        if 'quantidade' not in dados:
            return None, "Campo obrigatório ausente: quantidade", 400
        if not isinstance(dados['quantidade'], int) or dados['quantidade'] <= 0:
            return None, "quantidade deve ser um inteiro maior que zero", 400

        try:
            material = Material.criar(
                ordem_servico_id=os_id,
                nome=dados['nome'],
                quantidade=dados['quantidade']
            )
        except ValueError as e:
            return None, str(e), 400

        return material, None, 201

    @staticmethod
    def listar_materiais(os_id):
        os_existente = OrdemServico.buscar_por_id(os_id)
        if not os_existente:
            return None, "OS não encontrada", 404

        materiais = Material.listar_por_os(os_id)
        return materiais, None, 200
