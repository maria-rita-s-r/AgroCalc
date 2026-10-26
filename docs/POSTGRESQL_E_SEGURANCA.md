# PostgreSQL, permissões e procedimento do AgroCalc

## Por que há dois modos de banco?

- **Desenvolvimento/teste local:** por padrão, o projeto usa SQLite e cria um banco vazio automaticamente.
- **Demonstração do requisito de Banco de Dados II:** use PostgreSQL, que permite contas do SGBD com permissões diferentes e procedimentos armazenados. O script `database/postgresql_setup.sql` cria o banco, as tabelas, índices, a função/trigger de auditoria e o procedimento `sp_marcar_solicitacao_atendida`.

## Preparação PostgreSQL

1. Instale PostgreSQL e `psql`.
2. Abra `database/postgresql_setup.sql` e substitua as duas senhas de exemplo por senhas fortes e diferentes.
3. Execute o script **uma única vez** com uma conta administrativa do PostgreSQL:

   ```bash
   psql -U postgres -f database/postgresql_setup.sql
   ```

4. Instale as dependências Python:

   ```bash
   pip install -r requirements.txt
   ```

5. Configure a URL da conta restrita da aplicação. Linux/macOS:

   ```bash
   export AGROCALC_DATABASE_URL='postgresql://agrocalc_app:SENHA_DA_APLICACAO@localhost:5432/agrocalc'
   export AGROCALC_SECRET_KEY='DEFINA_UMA_CHAVE_ALEATORIA_LONGA'
   export AGROCALC_ADMIN_EMAIL='admin@seudominio.local'
   export AGROCALC_ADMIN_PASSWORD='DEFINA_UMA_SENHA_FORTE'
   python app.py
   ```

   No PowerShell, use `$env:AGROCALC_DATABASE_URL=...` e equivalentes.

6. A conta `agrocalc_app` pode consultar e alterar registros do banco AgroCalc, mas não pode criar tabelas, administrar roles nem acessar outros bancos. `agrocalc_admin` é a conta administrativa do SGBD. A conta de agrônomo criada pelo aplicativo é um usuário de negócio, diferente da conta administrativa PostgreSQL.

> Execute o script de instalação como administrador apenas na configuração inicial. Não coloque senhas reais no GitHub. Em produção, use variáveis de ambiente e HTTPS.

## Procedimento e trigger

- `fn_auditar_recomendacao_solo()` + `trg_auditoria_recomendacao_solo`: registra INSERT/UPDATE/DELETE em `recomendacoes_solo` na tabela `auditoria`.
- `sp_marcar_solicitacao_atendida(...)`: marca a solicitação como atendida, registra o relatório associado e prepara a mensagem exibida ao produtor. O fluxo da aplicação usa esse procedimento quando o backend é PostgreSQL; em SQLite executa a atualização equivalente.

## Backup e restauração PostgreSQL

Backup lógico:

```bash
pg_dump -U agrocalc_admin -d agrocalc -Fc -f backup_agrocalc.dump
```

Restaurar em um banco previamente criado:

```bash
pg_restore -U agrocalc_admin -d agrocalc --clean --if-exists backup_agrocalc.dump
```

O arquivo de setup é um esquema inicial vazio. Para entrega, faça também um dump real após validar a aplicação e confirme que não inclui dados pessoais de teste que não devam ser compartilhados.
