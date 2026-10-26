"""Acesso ao banco AgroCalc: SQLite para desenvolvimento ou PostgreSQL via DATABASE_URL.

Para PostgreSQL, execute database/postgresql_setup.sql como administrador do servidor
antes de iniciar a aplicação e configure AGROCALC_DATABASE_URL com a conta agrocalc_app.
"""
from __future__ import annotations
import os
import re
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE = os.environ.get("AGROCALC_SQLITE_PATH", str(BASE_DIR / "calculadora_agricola.db"))
DATABASE_URL = os.environ.get("AGROCALC_DATABASE_URL") or os.environ.get("DATABASE_URL")

class _PostgresCursor:
    def __init__(self, cursor, lastrowid=None):
        self._cursor = cursor
        self.lastrowid = lastrowid
        self.rowcount = cursor.rowcount
    def fetchone(self): return self._cursor.fetchone()
    def fetchall(self): return self._cursor.fetchall()

class _PostgresConnection:
    """Adaptador pequeno para preservar a API execute/commit usada pelo app."""
    def __init__(self, connection): self._connection = connection
    def execute(self, sql, params=()):
        query = sql.strip()
        is_insert = bool(re.match(r"(?is)^INSERT\s+INTO\b", query))
        if is_insert and not re.search(r"(?is)\bRETURNING\b", query):
            query = query.rstrip(";") + " RETURNING id"
        query = query.replace("?", "%s")
        cursor = self._connection.execute(query, tuple(params or ()))
        lastrowid = None
        if is_insert:
            row = cursor.fetchone()
            if row:
                lastrowid = row.get("id") if isinstance(row, dict) else row[0]
        return _PostgresCursor(cursor, lastrowid)
    def commit(self): self._connection.commit()
    def rollback(self): self._connection.rollback()
    def close(self): self._connection.close()


def conectar_banco():
    if DATABASE_URL:
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError("PostgreSQL configurado, mas falta instalar psycopg[binary]. Execute pip install -r requirements.txt.") from exc
        raw = psycopg.connect(DATABASE_URL, row_factory=dict_row)
        return _PostgresConnection(raw)
    conexao = sqlite3.connect(DATABASE)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON;")
    return conexao


def is_integrity_error(exc):
    if isinstance(exc, sqlite3.IntegrityError):
        return True
    try:
        import psycopg
        return isinstance(exc, psycopg.IntegrityError)
    except ImportError:
        return False


def criar_banco_de_dados():
    # Em PostgreSQL, schema, função e trigger são criados pelo script versionado.
    # A conta da aplicação recebe permissões restritas e não pode criar objetos no banco.
    if DATABASE_URL:
        return

    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS produtores (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, telefone TEXT);""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS propriedades (
        id INTEGER PRIMARY KEY AUTOINCREMENT, produtor_id INTEGER NOT NULL,
        nome_propriedade TEXT NOT NULL, municipio TEXT, estado TEXT,
        FOREIGN KEY (produtor_id) REFERENCES produtores(id) ON DELETE CASCADE);""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS talhoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, propriedade_id INTEGER NOT NULL,
        nome_talhao TEXT NOT NULL, area_ha REAL NOT NULL,
        FOREIGN KEY (propriedade_id) REFERENCES propriedades(id) ON DELETE CASCADE);""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS culturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome_cultura TEXT NOT NULL, v2_alvo REAL NOT NULL,
        propriedade_id INTEGER REFERENCES propriedades(id) ON DELETE CASCADE);""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS corretivos_calcario (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome_comercial TEXT NOT NULL,
        prnt_porcento REAL NOT NULL, tipo_calcario TEXT NOT NULL DEFAULT 'Não informado');""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS fertilizantes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome_comercial TEXT NOT NULL,
        teor_n REAL DEFAULT 0, teor_p2o5 REAL DEFAULT 0, teor_k2o REAL DEFAULT 0);""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
        senha_hash TEXT NOT NULL, papel TEXT NOT NULL CHECK (papel IN ('produtor','agronomo')),
        produtor_id INTEGER UNIQUE, ativo INTEGER NOT NULL DEFAULT 1,
        criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (produtor_id) REFERENCES produtores(id) ON DELETE CASCADE);""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS recomendacoes_solo (
        id INTEGER PRIMARY KEY AUTOINCREMENT, talhao_id INTEGER NOT NULL, cultura_id INTEGER NOT NULL,
        calcario_id INTEGER, data_coleta TEXT, ph REAL, v1_atual REAL, v2_alvo REAL, ctc_t REAL,
        ca REAL, mg REAL, k REAL, p REAL, h_al REAL, argila REAL, nc_ha REAL,
        dose_calcario_ha REAL, total_calcario_talhao REAL, k_original REAL, unidade_k TEXT,
        consistencia_status TEXT NOT NULL DEFAULT 'CONSISTENTE', consistencia_detalhes TEXT,
        FOREIGN KEY (talhao_id) REFERENCES talhoes(id) ON DELETE CASCADE,
        FOREIGN KEY (cultura_id) REFERENCES culturas(id) ON DELETE CASCADE,
        FOREIGN KEY (calcario_id) REFERENCES corretivos_calcario(id));""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS recomendacao_adubacao_itens (
        id INTEGER PRIMARY KEY AUTOINCREMENT, recomendacao_id INTEGER NOT NULL, nutriente TEXT NOT NULL CHECK (nutriente IN ('N','P2O5','K2O')),
        fertilizante_id INTEGER NOT NULL, alvo_kg_ha REAL NOT NULL, dose_kg_ha REAL NOT NULL, total_kg REAL NOT NULL,
        FOREIGN KEY (recomendacao_id) REFERENCES recomendacoes_solo(id) ON DELETE CASCADE,
        FOREIGN KEY (fertilizante_id) REFERENCES fertilizantes(id));
    """)
    cursor.execute("""CREATE TABLE IF NOT EXISTS solicitacoes_relatorio (
        id INTEGER PRIMARY KEY AUTOINCREMENT, produtor_id INTEGER NOT NULL, motivos TEXT NOT NULL,
        outro TEXT, status TEXT NOT NULL DEFAULT 'Pendente' CHECK (status IN ('Pendente','Em atendimento','Atendida')),
        mensagem_produtor TEXT, recomendacao_id INTEGER, criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        atendido_em TEXT, FOREIGN KEY (produtor_id) REFERENCES produtores(id) ON DELETE CASCADE,
        FOREIGN KEY (recomendacao_id) REFERENCES recomendacoes_solo(id) ON DELETE SET NULL);""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS novidades_produtor (
        id INTEGER PRIMARY KEY AUTOINCREMENT, produtor_id INTEGER NOT NULL, tipo TEXT NOT NULL,
        entidade_id INTEGER, descricao TEXT NOT NULL, visto_admin INTEGER NOT NULL DEFAULT 0,
        criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (produtor_id) REFERENCES produtores(id) ON DELETE CASCADE);""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS auditoria (
        id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER, acao TEXT NOT NULL,
        entidade TEXT NOT NULL, entidade_id INTEGER, criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL);""")
    # Migração idempotente para bases SQLite já existentes.
    for table, column, definition in [
        ("corretivos_calcario", "tipo_calcario", "TEXT NOT NULL DEFAULT 'Não informado'"),
        ("culturas", "propriedade_id", "INTEGER REFERENCES propriedades(id) ON DELETE CASCADE"),
        ("recomendacoes_solo", "k_original", "REAL"), ("recomendacoes_solo", "unidade_k", "TEXT"),
        ("recomendacoes_solo", "consistencia_status", "TEXT NOT NULL DEFAULT 'CONSISTENTE'"),
        ("recomendacoes_solo", "consistencia_detalhes", "TEXT"), ("recomendacoes_solo", "v2_alvo", "REAL")]:
        try: cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        except sqlite3.OperationalError: pass
    cursor.execute("""CREATE TRIGGER IF NOT EXISTS trg_auditoria_relatorio_insert AFTER INSERT ON recomendacoes_solo
        BEGIN INSERT INTO auditoria(usuario_id,acao,entidade,entidade_id) VALUES(NULL,'INSERT_TRIGGER','recomendacoes_solo',NEW.id); END;""")
    cursor.execute("""CREATE TRIGGER IF NOT EXISTS trg_auditoria_relatorio_update AFTER UPDATE ON recomendacoes_solo
        BEGIN INSERT INTO auditoria(usuario_id,acao,entidade,entidade_id) VALUES(NULL,'UPDATE_TRIGGER','recomendacoes_solo',NEW.id); END;""")
    cursor.execute("""CREATE TRIGGER IF NOT EXISTS trg_auditoria_relatorio_delete AFTER DELETE ON recomendacoes_solo
        BEGIN INSERT INTO auditoria(usuario_id,acao,entidade,entidade_id) VALUES(NULL,'DELETE_TRIGGER','recomendacoes_solo',OLD.id); END;""")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_propriedades_produtor ON propriedades(produtor_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_talhoes_propriedade ON talhoes(propriedade_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recomendacoes_talhao ON recomendacoes_solo(talhao_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_solicitacoes_produtor_status ON solicitacoes_relatorio(produtor_id,status)")
    conexao.commit(); conexao.close()


def marcar_solicitacao_atendida(conexao, solicitacao_id, recomendacao_id):
    """Usa o procedimento armazenado no PostgreSQL e SQL equivalente no SQLite."""
    if DATABASE_URL:
        conexao.execute("CALL sp_marcar_solicitacao_atendida(?, ?)", (solicitacao_id, recomendacao_id))
    else:
        conexao.execute("UPDATE solicitacoes_relatorio SET status='Atendida', recomendacao_id=?, atendido_em=CURRENT_TIMESTAMP, mensagem_produtor='Solicitação atendida: Relatório atualizado com sucesso!' WHERE id=? AND status!='Atendida'", (recomendacao_id, solicitacao_id))

if __name__ == "__main__":
    criar_banco_de_dados()
