# AgroCalc — modelo lógico e físico do banco de dados

## Modelo lógico

- **Produtor** (1) — (N) **Propriedade**: cada propriedade pertence a um produtor.
- **Propriedade** (1) — (N) **Talhão**: cada talhão pertence a uma propriedade.
- **Propriedade** (0..1) — (N) **Cultura**: uma cultura pode pertencer a uma propriedade específica ou ser um item geral do catálogo.
- **Talhão** (1) — (N) **Recomendação de solo**: cada recomendação identifica o talhão analisado.
- **Cultura** (1) — (N) **Recomendação de solo**: cada recomendação usa uma cultura e seu V% alvo.
- **Calcário** (0..1) — (N) **Recomendação de solo**: a recomendação pode registrar o corretivo utilizado.
- **Produtor** (1) — (N) **Solicitação de relatório**: o produtor solicita atualização e a solicitação pode apontar para uma recomendação gerada.
- **Usuário** (0..1) — (1) **Produtor**: contas com papel `produtor` ficam vinculadas a um produtor; a conta `agronomo` não precisa desse vínculo.
- **Usuário** (0..1) — (N) **Auditoria**: registra a autoria quando a ação parte de uma sessão da aplicação; gatilhos do banco podem registrar `usuario_id` nulo.
- **Produtor** (1) — (N) **Novidade de produtor**: avisa o agrônomo sobre cadastros feitos pelo produtor.

## Modelo físico

O sistema entregue utiliza **SQLite** no arquivo `calculadora_agricola.db`. As tabelas são `produtores`, `propriedades`, `talhoes`, `culturas`, `corretivos_calcario`, `fertilizantes`, `recomendacoes_solo`, `usuarios`, `solicitacoes_relatorio`, `novidades_produtor` e `auditoria`. As chaves estrangeiras são habilitadas por conexão. O arquivo `database/dump_agrocalc_vazio.sql` contém a estrutura sem registros; `calculadora_agricola.db` é a cópia de segurança vazia incluída no pacote.

## Gatilhos (triggers)

Os gatilhos `trg_auditoria_relatorio_insert`, `trg_auditoria_relatorio_update` e `trg_auditoria_relatorio_delete` escrevem na tabela `auditoria` quando uma recomendação é inserida, atualizada ou excluída, inclusive se a alteração não passar por uma rota Flask.

## Limitação importante para a avaliação de Banco de Dados II

SQLite **não possui contas de banco de dados com privilégios independentes nem procedimentos/funções armazenados** como PostgreSQL/MySQL. Portanto, embora o projeto tenha autenticação de usuários da aplicação, controle de acesso, dump, modelo e gatilhos SQLite, os itens “dois usuários do SGBD (administrador + aplicação)” e “procedimento/função armazenada” **não ficam plenamente atendidos enquanto a aplicação permanecer em SQLite**. Para fechar esses itens, o professor precisa aceitar outro mecanismo documentado ou o projeto precisará migrar o banco para um SGBD que ofereça esses recursos.
