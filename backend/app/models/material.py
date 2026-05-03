from app.database import get_connection


class Material:

    @staticmethod
    def criar(ordem_servico_id, nome, quantidade):
        if quantidade <= 0:
            raise ValueError("Quantidade deve ser maior que zero")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO material (ordem_servico_id, nome, quantidade)
            VALUES (?, ?, ?)
        """, (ordem_servico_id, nome, quantidade))

        conn.commit()
        material_id = cursor.lastrowid
        material = Material.buscar_por_id(material_id)
        conn.close()
        return material

    @staticmethod
    def listar_por_os(ordem_servico_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM material WHERE ordem_servico_id = ?",
            (ordem_servico_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def buscar_por_id(material_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM material WHERE id = ?", (material_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
