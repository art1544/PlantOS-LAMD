"""Modelo Usuario — CRUD da tabela `usuario` no SQLite."""

from app.database import get_connection
from datetime import datetime, timezone


class Usuario:

    ROLES_VALIDOS = ('operador', 'tecnico', 'admin')

    @staticmethod
    def criar(nome: str, login: str, senha_hash: str, role: str):
        if role not in Usuario.ROLES_VALIDOS:
            raise ValueError(f"Role inválido: {role}")

        conn = get_connection()
        try:
            cursor = conn.cursor()
            agora = datetime.now(timezone.utc).isoformat()
            cursor.execute(
                """
                INSERT INTO usuario (nome, login, senha, role, ativo, criado_em, atualizado_em)
                VALUES (?, ?, ?, ?, 1, ?, ?)
                """,
                (nome, login, senha_hash, role, agora, agora),
            )
            conn.commit()
            user_id = cursor.lastrowid
            cursor.execute("SELECT * FROM usuario WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def buscar_por_login(login: str):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuario WHERE login = ?", (login,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def buscar_por_id(user_id: int):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuario WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def listar():
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nome, login, role, ativo, criado_em, atualizado_em FROM usuario ORDER BY id"
            )
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def to_public_dict(user: dict) -> dict:
        """Remove campos sensíveis (hash de senha) antes de serializar para o cliente."""
        return {k: v for k, v in user.items() if k != 'senha'}
