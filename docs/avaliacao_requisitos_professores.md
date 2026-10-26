# Conferência dos requisitos do 4º bimestre

Esta conferência separa o que existe no código do que depende de configuração e demonstração. Não é uma declaração de aprovação do professor. Para cumprir os requisitos específicos de SGBD, não basta deixar SQLite como padrão: configure e teste PostgreSQL seguindo `docs/POSTGRESQL_E_SEGURANCA.md`.

| Disciplina / requisito | Situação no projeto | Observação / próximo passo |
|---|---|---|
| Projeto e Desenvolvimento — link do GitHub e deploy no relatório do AVA | **Externo ao código** | Inserir o link do repositório e o endereço público real do deploy no AVA. Não inventar URL de deploy. |
| Kanban no GitHub Project, participação, atividades e pitch | **Externo ao código** | Manter o quadro atualizado, registrar contribuições e preparar apresentação/demonstração. |
| Banco de Dados II — modelo lógico e físico | **Documentado** | Ver `docs/modelo_logico_fisico.md`. |
| Banco de Dados II — dump da base | **Incluído** | `database/dump_agrocalc_vazio.sql` e `calculadora_agricola.db` sem registros para testes. Para entrega final, gerar também um dump atualizado com dados de demonstração, se permitido. |
| Banco de Dados II — gatilho | **Implementado nos dois modos** | SQLite tem triggers de auditoria; PostgreSQL usa `trg_auditoria_recomendacao_solo`. |
| Banco de Dados II — pelo menos dois usuários do SGBD | **Preparado para PostgreSQL** | `database/postgresql_setup.sql` cria `agrocalc_admin` e `agrocalc_app`; execute o script no PostgreSQL e use `AGROCALC_DATABASE_URL` para a aplicação usar a conta restrita. SQLite continua sendo o modo local padrão. |
| Banco de Dados II — função/procedimento armazenado | **Preparado para PostgreSQL** | O script cria `fn_auditar_recomendacao_solo`, trigger de auditoria e `sp_marcar_solicitacao_atendida`, usado pelo fluxo da aplicação no modo PostgreSQL. |
| Programação Web — Flask e interface responsiva | **Implementado** | Flask, templates Jinja, CSS responsivo e mensagens de retorno. Testar manualmente em desktop e celular. |
| Programação Web — SQL Injection | **Mitigado nas consultas verificadas** | As consultas usam parâmetros; manter essa regra para novas rotas. |
| Programação Web — senha com hash, autenticação, autorização, CSRF e sessão | **Implementado parcialmente/funcional no código** | Senhas com Werkzeug hash, controle de papel, token CSRF e flags de sessão. Definir `AGROCALC_SECRET_KEY` e senha administrativa forte no ambiente de deploy. |
| Programação Web — CRUD usando GET, POST, PUT e DELETE corretamente | **Implementado no código; requer teste manual no navegador** | Listagem usa GET, criação POST, edição PUT e exclusão DELETE. Um adaptador JavaScript envia PUT/DELETE reais com token CSRF. Calcários e fertilizantes também têm CRUD. |
| Segurança da Informação — ao menos dois mecanismos CID | **Implementado** | Controle de acesso por papel, gerenciamento de sessão/CSRF, hash de senha e auditoria. Demonstrar e documentar em apresentação. |
| Segurança — logs e backup | **Parcial** | Auditoria e triggers estão incluídos; documentar a rotina de backup/recuperação e demonstrar restauração. |
| Redes de Computadores | **Aguardando critérios** | O próprio documento informa que o professor ainda enviará os requisitos. |

## Fluxo de geração de relatório

Ao atender uma solicitação, o agrônomo deve selecionar manualmente o talhão e a cultura. A tela não pré-seleciona automaticamente nenhum dos dois. Para uma solicitação, as opções são limitadas aos dados do produtor, com culturas gerais do catálogo também disponíveis. A rota de formulário valida a compatibilidade do talhão e da cultura.


## Evolução do cálculo de adubação

O formulário de análise inclui um bloco opcional para o agrônomo informar metas técnicas de N, P₂O₅ e K₂O (kg/ha) e selecionar fertilizantes cadastrados. O sistema converte cada meta em dose de produto pela relação `dose do produto (kg/ha) = meta do nutriente (kg/ha) / (teor percentual / 100)` e calcula o total para a área do talhão. Os itens são persistidos em `recomendacao_adubacao_itens`, relacionados à recomendação de solo, e aparecem no resultado e no documento.

**Limitação técnica explícita:** esta etapa converte metas previamente definidas pelo agrônomo; não determina automaticamente a necessidade de N, P₂O₅ ou K₂O a partir dos resultados laboratoriais. Para automatizar essa interpretação, é necessário incorporar tabelas técnicas validadas para a cultura, região, produtividade esperada, método de extração do laboratório e sistema de manejo. Fertilizantes compostos também exigem contabilizar os nutrientes secundários fornecidos para evitar duplicidade ou excesso.
