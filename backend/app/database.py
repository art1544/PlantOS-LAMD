import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'plantos.db')


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS ordem_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            setor TEXT NOT NULL,
            equipamento TEXT NOT NULL,
            prioridade TEXT NOT NULL CHECK(prioridade IN ('baixa', 'media', 'alta', 'critica')),
            status TEXT NOT NULL DEFAULT 'aberta' CHECK(status IN ('aberta', 'aceita', 'em_andamento', 'concluida', 'recusada')),
            operador_id TEXT NOT NULL,
            tecnico_id TEXT,
            laudo TEXT,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
            atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS material (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ordem_servico_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            quantidade INTEGER NOT NULL CHECK(quantidade > 0),
            FOREIGN KEY (ordem_servico_id) REFERENCES ordem_servico(id)
        );

        CREATE TRIGGER IF NOT EXISTS trg_ordem_servico_atualizado_em
        AFTER UPDATE ON ordem_servico
        FOR EACH ROW
        BEGIN
            UPDATE ordem_servico
            SET atualizado_em = CURRENT_TIMESTAMP
            WHERE id = OLD.id;
        END;
                         
         CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            login TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'operador' CHECK(role IN ('operador', 'tecnico', 'admin')),
            ativo INTEGER NOT NULL DEFAULT 1 CHECK(ativo IN (0, 1)),
            criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );                 

        CREATE TRIGGER IF NOT EXISTS trg_usuario_atualizado_em
        AFTER UPDATE ON usuario
        FOR EACH ROW
        BEGIN
            UPDATE usuario
            SET atualizado_em = CURRENT_TIMESTAMP
            WHERE id = OLD.id;
        END;

        -- Tabela de auditoria de eventos consumidos do RabbitMQ (Sprint 2).
        -- Cada linha representa uma mensagem efetivamente processada pelo
        -- worker consumidor, comprovando a comunicação assíncrona via MOM.
        CREATE TABLE IF NOT EXISTS evento_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fila TEXT NOT NULL,
            routing_key TEXT NOT NULL,
            payload TEXT NOT NULL,
            recebido_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()
