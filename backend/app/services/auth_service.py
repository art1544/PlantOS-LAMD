"""Camada de serviço de autenticação: cadastro e login."""

import sqlite3

from app.auth import generate_token, hash_password, verify_password
from app.models.usuario import Usuario


class AuthService:

    @staticmethod
    def registrar(dados: dict):
        campos = ['nome', 'login', 'senha', 'role']
        for campo in campos:
            if not dados.get(campo):
                return None, f"Campo obrigatório ausente: {campo}", 400

        if dados['role'] not in Usuario.ROLES_VALIDOS:
            return None, f"Role inválido. Use: {', '.join(Usuario.ROLES_VALIDOS)}", 400

        if len(dados['senha']) < 6:
            return None, "Senha deve ter no mínimo 6 caracteres", 400

        try:
            usuario = Usuario.criar(
                nome=dados['nome'],
                login=dados['login'],
                senha_hash=hash_password(dados['senha']),
                role=dados['role'],
            )
        except sqlite3.IntegrityError:
            return None, "Login já cadastrado", 409
        except ValueError as e:
            return None, str(e), 400

        return Usuario.to_public_dict(usuario), None, 201

    @staticmethod
    def login(dados: dict):
        if not dados.get('login') or not dados.get('senha'):
            return None, "Campos obrigatórios: login, senha", 400

        usuario = Usuario.buscar_por_login(dados['login'])
        if not usuario or not verify_password(dados['senha'], usuario['senha']):
            return None, "Credenciais inválidas", 401

        if not usuario['ativo']:
            return None, "Usuário inativo", 403

        token = generate_token(
            user_id=usuario['id'],
            login=usuario['login'],
            role=usuario['role'],
        )
        return {
            'token': token,
            'usuario': Usuario.to_public_dict(usuario),
        }, None, 200
