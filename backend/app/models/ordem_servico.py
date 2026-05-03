from app.database import get_connection
from datetime import datetime


class OrdemServico:

    PRIORIDADES_VALIDAS = ('baixa', 'media', 'alta', 'critica')
    STATUS_VALIDOS = ('aberta', 'aceita', 'em_andamento', 'concluida', 'recusada')

    @staticmethod
    def criar(titulo, descricao, setor, equipamento, prioridade, operador_id):
        if prioridade not in OrdemServico.PRIORIDADES_VALIDAS:
            raise ValueError(f"Prioridade inválida: {prioridade}")

        conn = get_connection()
        cursor = conn.cursor()
        agora = datetime.utcnow().isoformat() + "Z"

        cursor.execute("""
            INSERT INTO ordem_servico (titulo, descricao, setor, equipamento, prioridade, operador_id, criado_em, atualizado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (titulo, descricao, setor, equipamento, prioridade, operador_id, agora, agora))

        conn.commit()
        os_id = cursor.lastrowid
        os_criada = OrdemServico.buscar_por_id(os_id)
        conn.close()
        return os_criada

    @staticmethod
    def listar(status=None, operador_id=None):
        conn = get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM ordem_servico WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)
        if operador_id:
            query += " AND operador_id = ?"
            params.append(operador_id)

        query += " ORDER BY criado_em DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def buscar_por_id(os_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ordem_servico WHERE id = ?", (os_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def atualizar_status(os_id, novo_status, tecnico_id=None, laudo=None):
        if novo_status not in OrdemServico.STATUS_VALIDOS:
            raise ValueError(f"Status inválido: {novo_status}")

        conn = get_connection()
        cursor = conn.cursor()
        agora = datetime.utcnow().isoformat() + "Z"

        campos = ["status = ?", "atualizado_em = ?"]
        valores = [novo_status, agora]

        if tecnico_id:
            campos.append("tecnico_id = ?")
            valores.append(tecnico_id)

        if laudo:
            campos.append("laudo = ?")
            valores.append(laudo)

        valores.append(os_id)

        cursor.execute(
            f"UPDATE ordem_servico SET {', '.join(campos)} WHERE id = ?",
            valores
        )

        conn.commit()
        os_atualizada = OrdemServico.buscar_por_id(os_id)
        conn.close()
        return os_atualizada
