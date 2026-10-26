-- AgroCalc: dump de estrutura vazio (SQLite).
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE auditoria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        acao TEXT NOT NULL,
        entidade TEXT NOT NULL,
        entidade_id INTEGER,
        criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
    );
CREATE TABLE corretivos_calcario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_comercial TEXT NOT NULL,
        prnt_porcento REAL NOT NULL,
        tipo_calcario TEXT NOT NULL DEFAULT 'Não informado'
    );
CREATE TABLE culturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_cultura TEXT NOT NULL,
        v2_alvo REAL NOT NULL
    , propriedade_id INTEGER REFERENCES propriedades(id) ON DELETE CASCADE);
CREATE TABLE fertilizantes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_comercial TEXT NOT NULL,
        teor_n REAL DEFAULT 0,
        teor_p2o5 REAL DEFAULT 0,
        teor_k2o REAL DEFAULT 0
    );
CREATE TABLE novidades_produtor (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produtor_id INTEGER NOT NULL,
        tipo TEXT NOT NULL,
        entidade_id INTEGER,
        descricao TEXT NOT NULL,
        visto_admin INTEGER NOT NULL DEFAULT 0,
        criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (produtor_id) REFERENCES produtores(id) ON DELETE CASCADE
    );
CREATE TABLE produtores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        telefone TEXT
    );
CREATE TABLE propriedades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produtor_id INTEGER NOT NULL,
        nome_propriedade TEXT NOT NULL,
        municipio TEXT,
        estado TEXT,
        FOREIGN KEY (produtor_id) REFERENCES produtores(id) ON DELETE CASCADE
    );
CREATE TABLE recomendacoes_solo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        talhao_id INTEGER NOT NULL,
        cultura_id INTEGER NOT NULL,
        calcario_id INTEGER,
        data_coleta TEXT,
        ph REAL,
        v1_atual REAL,
        ctc_t REAL,
        ca REAL,
        mg REAL,
        k REAL,
        p REAL,
        h_al REAL,
        argila REAL,
        nc_ha REAL,
        dose_calcario_ha REAL,
        total_calcario_talhao REAL, k_original REAL, unidade_k TEXT, consistencia_status TEXT NOT NULL DEFAULT 'CONSISTENTE', consistencia_detalhes TEXT, v2_alvo REAL,
        FOREIGN KEY (talhao_id) REFERENCES talhoes(id) ON DELETE CASCADE,
        FOREIGN KEY (cultura_id) REFERENCES culturas(id) ON DELETE CASCADE,
        FOREIGN KEY (calcario_id) REFERENCES corretivos_calcario(id)
    );
CREATE TABLE recomendacao_adubacao_itens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recomendacao_id INTEGER NOT NULL,
        nutriente TEXT NOT NULL CHECK (nutriente IN ('N','P2O5','K2O')),
        fertilizante_id INTEGER NOT NULL,
        alvo_kg_ha REAL NOT NULL,
        dose_kg_ha REAL NOT NULL,
        total_kg REAL NOT NULL,
        FOREIGN KEY (recomendacao_id) REFERENCES recomendacoes_solo(id) ON DELETE CASCADE,
        FOREIGN KEY (fertilizante_id) REFERENCES fertilizantes(id)
    );
CREATE TABLE solicitacoes_relatorio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produtor_id INTEGER NOT NULL,
        motivos TEXT NOT NULL,
        outro TEXT,
        status TEXT NOT NULL DEFAULT 'Pendente' CHECK (status IN ('Pendente','Em atendimento','Atendida')),
        mensagem_produtor TEXT,
        recomendacao_id INTEGER,
        criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        atendido_em TEXT,
        FOREIGN KEY (produtor_id) REFERENCES produtores(id) ON DELETE CASCADE,
        FOREIGN KEY (recomendacao_id) REFERENCES recomendacoes_solo(id) ON DELETE SET NULL
    );
CREATE TABLE talhoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        propriedade_id INTEGER NOT NULL,
        nome_talhao TEXT NOT NULL,
        area_ha REAL NOT NULL,
        FOREIGN KEY (propriedade_id) REFERENCES propriedades(id) ON DELETE CASCADE
    );
CREATE TABLE usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        senha_hash TEXT NOT NULL,
        papel TEXT NOT NULL CHECK (papel IN ('produtor', 'agronomo')),
        produtor_id INTEGER UNIQUE,
        ativo INTEGER NOT NULL DEFAULT 1,
        criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (produtor_id) REFERENCES produtores(id) ON DELETE CASCADE
    );
CREATE TRIGGER trg_auditoria_relatorio_insert
        AFTER INSERT ON recomendacoes_solo
        BEGIN
            INSERT INTO auditoria (usuario_id, acao, entidade, entidade_id)
            VALUES (NULL, 'INSERT_TRIGGER', 'recomendacoes_solo', NEW.id);
        END;
CREATE TRIGGER trg_auditoria_relatorio_update
        AFTER UPDATE ON recomendacoes_solo
        BEGIN
            INSERT INTO auditoria (usuario_id, acao, entidade, entidade_id)
            VALUES (NULL, 'UPDATE_TRIGGER', 'recomendacoes_solo', NEW.id);
        END;
CREATE TRIGGER trg_auditoria_relatorio_delete
        AFTER DELETE ON recomendacoes_solo
        BEGIN
            INSERT INTO auditoria (usuario_id, acao, entidade, entidade_id)
            VALUES (NULL, 'DELETE_TRIGGER', 'recomendacoes_solo', OLD.id);
        END;
CREATE INDEX idx_propriedades_produtor ON propriedades(produtor_id);
CREATE INDEX idx_talhoes_propriedade ON talhoes(propriedade_id);
CREATE INDEX idx_recomendacoes_talhao ON recomendacoes_solo(talhao_id);
CREATE INDEX idx_solicitacoes_produtor_status ON solicitacoes_relatorio(produtor_id, status);
DELETE FROM "sqlite_sequence";
COMMIT;
PRAGMA foreign_keys=ON;
