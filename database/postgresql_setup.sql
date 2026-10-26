-- AgroCalc - configuração PostgreSQL para Banco de Dados II.
-- Execute UMA vez com psql como um administrador PostgreSQL (ex.: postgres).
-- Altere as senhas antes de executar. Não reutilize as senhas de exemplo em produção.
CREATE ROLE agrocalc_admin LOGIN PASSWORD 'TROQUE_SENHA_ADMIN_FORTE';
CREATE ROLE agrocalc_app LOGIN PASSWORD 'TROQUE_SENHA_APLICACAO_FORTE';
CREATE DATABASE agrocalc OWNER agrocalc_admin;
\connect agrocalc

SET ROLE agrocalc_admin;
CREATE TABLE produtores (
  id BIGSERIAL PRIMARY KEY, nome VARCHAR(160) NOT NULL, telefone VARCHAR(40)
);
CREATE TABLE usuarios (
  id BIGSERIAL PRIMARY KEY, nome VARCHAR(160) NOT NULL, email VARCHAR(254) NOT NULL UNIQUE,
  senha_hash TEXT NOT NULL, papel VARCHAR(16) NOT NULL CHECK (papel IN ('produtor','agronomo')),
  produtor_id BIGINT UNIQUE REFERENCES produtores(id) ON DELETE CASCADE,
  ativo BOOLEAN NOT NULL DEFAULT TRUE, criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE propriedades (
  id BIGSERIAL PRIMARY KEY, produtor_id BIGINT NOT NULL REFERENCES produtores(id) ON DELETE CASCADE,
  nome_propriedade VARCHAR(160) NOT NULL, municipio VARCHAR(120), estado VARCHAR(2)
);
CREATE TABLE talhoes (
  id BIGSERIAL PRIMARY KEY, propriedade_id BIGINT NOT NULL REFERENCES propriedades(id) ON DELETE CASCADE,
  nome_talhao VARCHAR(160) NOT NULL, area_ha DOUBLE PRECISION NOT NULL CHECK (area_ha > 0)
);
CREATE TABLE culturas (
  id BIGSERIAL PRIMARY KEY, nome_cultura VARCHAR(120) NOT NULL, v2_alvo DOUBLE PRECISION NOT NULL CHECK (v2_alvo > 0 AND v2_alvo <= 100),
  propriedade_id BIGINT REFERENCES propriedades(id) ON DELETE CASCADE
);
CREATE TABLE corretivos_calcario (
  id BIGSERIAL PRIMARY KEY, nome_comercial VARCHAR(160) NOT NULL,
  prnt_porcento DOUBLE PRECISION NOT NULL CHECK (prnt_porcento > 0 AND prnt_porcento <= 100),
  tipo_calcario VARCHAR(40) NOT NULL DEFAULT 'Não informado'
);
CREATE TABLE fertilizantes (
  id BIGSERIAL PRIMARY KEY, nome_comercial VARCHAR(160) NOT NULL,
  teor_n DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (teor_n BETWEEN 0 AND 100),
  teor_p2o5 DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (teor_p2o5 BETWEEN 0 AND 100),
  teor_k2o DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (teor_k2o BETWEEN 0 AND 100)
);
CREATE TABLE recomendacoes_solo (
  id BIGSERIAL PRIMARY KEY, talhao_id BIGINT NOT NULL REFERENCES talhoes(id) ON DELETE CASCADE,
  cultura_id BIGINT NOT NULL REFERENCES culturas(id) ON DELETE CASCADE,
  calcario_id BIGINT REFERENCES corretivos_calcario(id), data_coleta DATE,
  ph DOUBLE PRECISION, v1_atual DOUBLE PRECISION, v2_alvo DOUBLE PRECISION, ctc_t DOUBLE PRECISION,
  ca DOUBLE PRECISION, mg DOUBLE PRECISION, k DOUBLE PRECISION, p DOUBLE PRECISION, h_al DOUBLE PRECISION, argila DOUBLE PRECISION,
  nc_ha DOUBLE PRECISION, dose_calcario_ha DOUBLE PRECISION, total_calcario_talhao DOUBLE PRECISION,
  k_original DOUBLE PRECISION, unidade_k VARCHAR(32), consistencia_status VARCHAR(24) NOT NULL DEFAULT 'CONSISTENTE', consistencia_detalhes TEXT
);
CREATE TABLE recomendacao_adubacao_itens (
  id BIGSERIAL PRIMARY KEY, recomendacao_id BIGINT NOT NULL REFERENCES recomendacoes_solo(id) ON DELETE CASCADE,
  nutriente VARCHAR(8) NOT NULL CHECK (nutriente IN ('N','P2O5','K2O')),
  fertilizante_id BIGINT NOT NULL REFERENCES fertilizantes(id), alvo_kg_ha DOUBLE PRECISION NOT NULL CHECK (alvo_kg_ha >= 0),
  dose_kg_ha DOUBLE PRECISION NOT NULL CHECK (dose_kg_ha >= 0), total_kg DOUBLE PRECISION NOT NULL CHECK (total_kg >= 0)
);
CREATE TABLE solicitacoes_relatorio (
  id BIGSERIAL PRIMARY KEY, produtor_id BIGINT NOT NULL REFERENCES produtores(id) ON DELETE CASCADE,
  motivos TEXT NOT NULL, outro VARCHAR(500), status VARCHAR(24) NOT NULL DEFAULT 'Pendente' CHECK (status IN ('Pendente','Em atendimento','Atendida')),
  mensagem_produtor TEXT, recomendacao_id BIGINT REFERENCES recomendacoes_solo(id) ON DELETE SET NULL,
  criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, atendido_em TIMESTAMPTZ
);
CREATE TABLE novidades_produtor (
  id BIGSERIAL PRIMARY KEY, produtor_id BIGINT NOT NULL REFERENCES produtores(id) ON DELETE CASCADE,
  tipo VARCHAR(40) NOT NULL, entidade_id BIGINT, descricao TEXT NOT NULL, visto_admin INTEGER NOT NULL DEFAULT 0 CHECK (visto_admin IN (0,1)),
  criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE auditoria (
  id BIGSERIAL PRIMARY KEY, usuario_id BIGINT REFERENCES usuarios(id) ON DELETE SET NULL,
  acao VARCHAR(80) NOT NULL, entidade VARCHAR(80) NOT NULL, entidade_id BIGINT,
  criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_propriedades_produtor ON propriedades(produtor_id);
CREATE INDEX idx_talhoes_propriedade ON talhoes(propriedade_id);
CREATE INDEX idx_recomendacoes_talhao ON recomendacoes_solo(talhao_id);
CREATE INDEX idx_solicitacoes_produtor_status ON solicitacoes_relatorio(produtor_id,status);

-- Função e trigger exigidos: toda inserção/alteração/exclusão de relatório gera auditoria.
CREATE OR REPLACE FUNCTION fn_auditar_recomendacao_solo()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    INSERT INTO auditoria(usuario_id, acao, entidade, entidade_id)
    VALUES (NULL, 'DELETE_TRIGGER', 'recomendacoes_solo', OLD.id);
    RETURN OLD;
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO auditoria(usuario_id, acao, entidade, entidade_id)
    VALUES (NULL, 'UPDATE_TRIGGER', 'recomendacoes_solo', NEW.id);
    RETURN NEW;
  ELSE
    INSERT INTO auditoria(usuario_id, acao, entidade, entidade_id)
    VALUES (NULL, 'INSERT_TRIGGER', 'recomendacoes_solo', NEW.id);
    RETURN NEW;
  END IF;
END;
$$;
CREATE TRIGGER trg_auditoria_recomendacao_solo
AFTER INSERT OR UPDATE OR DELETE ON recomendacoes_solo
FOR EACH ROW EXECUTE FUNCTION fn_auditar_recomendacao_solo();

-- Procedimento armazenado utilizado pelo fluxo de atendimento do relatório.
CREATE OR REPLACE PROCEDURE sp_marcar_solicitacao_atendida(p_solicitacao_id BIGINT, p_recomendacao_id BIGINT)
LANGUAGE plpgsql AS $$
BEGIN
  UPDATE solicitacoes_relatorio
  SET status='Atendida', recomendacao_id=p_recomendacao_id,
      atendido_em=CURRENT_TIMESTAMP,
      mensagem_produtor='Solicitação atendida: Relatório atualizado com sucesso!'
  WHERE id=p_solicitacao_id AND status <> 'Atendida';
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Solicitação inexistente ou já atendida';
  END IF;
END;
$$;

-- A conta da aplicação não pode criar/alterar estrutura ou administrar usuários.
GRANT CONNECT ON DATABASE agrocalc TO agrocalc_app;
GRANT USAGE ON SCHEMA public TO agrocalc_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO agrocalc_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO agrocalc_app;
GRANT EXECUTE ON FUNCTION fn_auditar_recomendacao_solo() TO agrocalc_app;
GRANT EXECUTE ON PROCEDURE sp_marcar_solicitacao_atendida(BIGINT, BIGINT) TO agrocalc_app;
ALTER DEFAULT PRIVILEGES FOR ROLE agrocalc_admin IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO agrocalc_app;
ALTER DEFAULT PRIVILEGES FOR ROLE agrocalc_admin IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO agrocalc_app;
RESET ROLE;
