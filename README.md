# 🌱 AgroCalc

### Calculadora de Recomendação de Adubação e Calagem

O **AgroCalc** é uma aplicação desenvolvida para auxiliar produtores rurais e profissionais da área agrícola na **interpretação de dados de análise de solo e na recomendação de corretivos e fertilizantes**.

A proposta surgiu a partir de um problema comum no processo de manejo do solo: transformar os dados presentes em um laudo de análise de solo em recomendações práticas exige cálculos matemáticos que podem ser repetitivos e sujeitos a erros quando realizados manualmente.

Com o AgroCalc, essas informações podem ser inseridas no sistema para que os cálculos sejam realizados de forma mais organizada, rápida e padronizada.

---

## 🌾 O problema

A análise de solo é uma ferramenta importante para auxiliar na tomada de decisões relacionadas à fertilidade do solo.

Entretanto, após receber um laudo do laboratório, o produtor ou profissional responsável ainda precisa interpretar diversos parâmetros e realizar cálculos para determinar a necessidade de aplicação de corretivos e fertilizantes.

Entre esses dados estão informações como:

* V% atual;
* CTC;
* pH;
* Cálcio (Ca);
* Magnésio (Mg);
* Potássio (K);
* Fósforo (P);
* H + Al;
* Argila;
* entre outros parâmetros utilizados no processo de recomendação.

A realização manual desses cálculos pode tornar o processo mais demorado e aumentar a possibilidade de erros de cálculo ou de preenchimento.

---

## 💡 Nossa solução

O **AgroCalc** foi desenvolvido para transformar os dados da análise de solo em informações mais fáceis de interpretar e utilizar.

O sistema permite cadastrar as informações necessárias da propriedade, do talhão, da cultura e da análise de solo e, a partir desses dados, realizar os cálculos relacionados à recomendação de calagem e adubação.

### Fluxo básico do AgroCalc

```text
Laudo de análise de solo
          ↓
    Entrada dos dados
          ↓
   Análise das informações
          ↓
       Cálculos
          ↓
 Recomendação de manejo
          ↓
      Resultado
```

O objetivo é reduzir cálculos manuais repetitivos e centralizar as informações necessárias para o processo de recomendação.

---

## 🎯 Objetivo

O principal objetivo do AgroCalc é **facilitar e agilizar o processo de interpretação de análises de solo**, fornecendo cálculos e recomendações de forma organizada.

A aplicação busca contribuir para:

* ⏱️ redução do tempo gasto com cálculos manuais;
* 📊 organização das informações das análises de solo;
* 🧮 automatização de cálculos repetitivos;
* 🌱 apoio ao planejamento da correção e adubação do solo;
* 📋 armazenamento das recomendações realizadas;
* 📈 melhor organização das informações relacionadas às propriedades e talhões.

---

## 👨‍🌾 Para quem é o AgroCalc?

O sistema foi pensado principalmente para pessoas que trabalham com **manejo e fertilidade do solo**, podendo auxiliar:

* produtores rurais;
* técnicos agrícolas;
* profissionais da área agronômica;
* estudantes da área agrícola;
* propriedades que realizam acompanhamento de análises de solo.

O AgroCalc busca atuar como uma **ferramenta de apoio**, facilitando a transformação dos dados do laudo em informações úteis para o planejamento do manejo.

> **Importante:** as recomendações geradas pelo sistema devem ser utilizadas como apoio e seguir o método técnico adotado no projeto e as orientações de um profissional habilitado quando necessário.

---

## 🧮 O que o sistema gerencia?

O AgroCalc foi estruturado para organizar informações relacionadas a:

### 👤 Produtores

Cadastro e gerenciamento dos produtores associados às propriedades.

### 🏡 Propriedades

Registro das propriedades rurais utilizadas no sistema.

### 🌱 Talhões

Organização das áreas da propriedade utilizadas para o cultivo.

### 🌾 Culturas

Cadastro das culturas utilizadas nas recomendações.

### 🧪 Análises de solo

Registro dos principais dados obtidos a partir do laudo laboratorial, como:

* V% atual;
* CTC;
* pH;
* Ca;
* Mg;
* K;
* P;
* H + Al;
* argila.

### 🪨 Corretivos

Informações utilizadas para calcular a necessidade de aplicação de corretivos, considerando parâmetros como o PRNT.

### 🌿 Fertilizantes

Cadastro de fertilizantes e suas respectivas concentrações de nutrientes.

### 📋 Recomendações

Armazenamento dos resultados obtidos a partir dos dados da análise de solo e das informações cadastradas no sistema.

---

## 🪨 Cálculo de calagem

Um dos principais recursos do AgroCalc é o cálculo da necessidade de calagem.

A aplicação utiliza os dados da análise de solo, como **V% atual e CTC**, juntamente com o valor de saturação por bases desejado e as características do corretivo selecionado.

De forma simplificada:

```text
Dados da análise
       +
V% desejado
       +
Características do corretivo
       ↓
Necessidade de calagem
       ↓
Resultado em t/ha
```

O sistema também considera a área do talhão para auxiliar na obtenção da quantidade necessária para a área cadastrada.

---

## 🌿 Recomendação de adubação

O AgroCalc permite registrar um planejamento de adubação em que o agrônomo informa metas técnicas de N, P₂O₅ e K₂O (kg/ha) e seleciona fertilizantes cadastrados. O sistema converte essas metas em dose de produto usando o teor percentual cadastrado e calcula a quantidade total para a área do talhão. Os itens ficam vinculados à recomendação e aparecem no resultado e no documento.

**Limite importante:** as metas de nutrientes precisam ser definidas pelo agrônomo com base em recomendação técnica regional. O sistema ainda não classifica automaticamente os níveis de P e K do laudo para determinar essas metas. Para automatizar essa etapa, é necessário incorporar tabelas técnicas validadas para a cultura, região, produtividade esperada, método laboratorial e sistema de manejo. Fertilizantes compostos exigem contabilizar todos os nutrientes fornecidos para evitar duplicidade ou excesso.

```text
Laudo + cultura + critério técnico definido pelo agrônomo
                         ↓
          Meta de nutriente (kg/ha)
                         +
            Fertilizante e teor (%)
                         ↓
       Dose do produto (kg/ha) e total
```

---

## 📊 Organização das informações

Uma das características do AgroCalc é a organização hierárquica das informações:

```text
Produtor
   │
   └── Propriedade
          │
          └── Talhão
                 │
                 ├── Cultura
                 │
                 └── Análise de Solo
                        │
                        └── Recomendação
```

Essa estrutura permite relacionar a análise de solo ao local onde ela foi realizada e manter um histórico das recomendações.

---

## 🚀 Tecnologias

O projeto utiliza tecnologias voltadas para o desenvolvimento de aplicações web:

* 🐍 **Python**
* 🌐 **Flask**
* 🗄️ **Banco de dados**
* 🧱 **HTML**
* 🎨 **CSS**
* ⚙️ **JavaScript**

---

## 🏗️ Estrutura do projeto

```text
AgroCalc/
│
├── app.py
├── bancoDB.py
├── requirements.txt
├── README.md
│
├── templates/
│   └── páginas HTML
│
├── static/
│   └── arquivos CSS e recursos
│
└── banco de dados
```

A estrutura poderá ser aprimorada durante o desenvolvimento para separar melhor as responsabilidades da aplicação e facilitar sua manutenção.

---

## 🔬 Como funciona?

De maneira geral, o usuário realiza o seguinte processo:

### 1. Cadastro

São cadastradas as informações do produtor, propriedade, talhão e cultura.

### 2. Entrada da análise

Os dados presentes no laudo de análise de solo são inseridos no sistema.

### 3. Processamento

O AgroCalc utiliza os dados fornecidos para realizar os cálculos necessários.

### 4. Recomendação

Os resultados são apresentados ao usuário de forma organizada, incluindo a quantidade recomendada de corretivo ou fertilizante conforme o cálculo realizado.

### 5. Histórico

As recomendações podem ser armazenadas para consulta posterior.

---

## 🌱 Nossa proposta de valor

O AgroCalc busca transformar uma tarefa que pode ser **manual, repetitiva e sujeita a erros de cálculo** em um processo mais **organizado, rápido e automatizado**.

### Antes

```text
Laudo
  ↓
Interpretação manual
  ↓
Fórmulas
  ↓
Calculadora
  ↓
Novos cálculos
  ↓
Anotações
  ↓
Resultado
```

### Com o AgroCalc

```text
Laudo
  ↓
AgroCalc
  ↓
Processamento dos dados
  ↓
Recomendação
```

A ideia é tornar o processo mais simples sem perder as informações importantes utilizadas na análise.

---

## 🎓 Projeto interdisciplinar

O AgroCalc está sendo desenvolvido como um projeto interdisciplinar, envolvendo conhecimentos de:

* Desenvolvimento de Sistemas;
* Banco de Dados;
* Programação Web;
* Segurança da Informação;
* Redes de Computadores.

Dessa forma, o projeto não se limita à criação de uma calculadora, mas busca integrar **desenvolvimento, banco de dados, segurança, interface e infraestrutura** em uma única aplicação.

---

## 👥 Equipe

Projeto desenvolvido por:

* **Maria Rita**
* **Ketelin Wliane**
* **Maria Clara**

---

## 📌 Status do projeto

🚧 **Em desenvolvimento**

O AgroCalc está em processo de evolução e novas funcionalidades, melhorias de segurança, banco de dados, interface e infraestrutura serão incorporadas ao projeto.

---

## 🌐 Projeto


**Aplicação:**
*A ser disponibilizada*

---

## 📄 Licença

Projeto acadêmico desenvolvido para fins educacionais.

## Acesso por perfil (versão com autenticação)

O AgroCalc agora apresenta uma página inicial com três caminhos: entrar como administrador/agrônomo, cadastrar-se como produtor e entrar como produtor. Os produtores acessam apenas suas próprias terras, talhões, culturas vinculadas e relatórios. O agrônomo mantém o gerenciamento geral de produtores, terras, talhões, culturas e recomendações.

### Executar localmente

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

A aplicação usa SQLite no arquivo `calculadora_agricola.db`. Configure a chave de sessão e as credenciais iniciais do agrônomo por variáveis de ambiente antes de publicar:

- `AGROCALC_SECRET_KEY`: chave longa, aleatória e privada.
- `AGROCALC_ADMIN_EMAIL`: e-mail da conta inicial do agrônomo (padrão local: `admin@agrocalc.local`).
- `AGROCALC_ADMIN_PASSWORD`: senha inicial do agrônomo (padrão local: `AgroCalc@123`). **Troque a senha padrão antes de qualquer publicação e não use credenciais de exemplo em produção.**
- `FLASK_HTTPS_ONLY=1`: habilita o atributo Secure do cookie quando o site estiver servido exclusivamente por HTTPS.

O banco cria a conta inicial do agrônomo apenas se o e-mail configurado ainda não existir. Para ambientes reais, use uma senha forte e exclusiva e mantenha o arquivo de banco de dados e a chave secreta fora do controle de versão.

### Segurança e limites

- Senhas armazenadas com hash seguro do Werkzeug; não são salvas em texto puro.
- Token CSRF nos formulários de autenticação e nas operações de cadastro/alteração/exclusão implementadas nas telas de produtor.
- Consultas SQL parametrizadas e validação de vínculo entre a conta do produtor e os registros acessados.
- A calculadora registra a recomendação de calagem usando a fórmula já presente no projeto: `NC = ((V% alvo - V% atual) * CTC T) / 100`, com ajuste pelo PRNT cadastrado. O resultado é uma estimativa do projeto e deve ser conferido por profissional agrônomo com base no laudo e nas recomendações técnicas locais.

A aplicação deve ser validada em ambiente com as dependências instaladas antes de publicar o deploy. Este pacote foi verificado quanto à sintaxe dos arquivos Python; não foi possível executar testes HTTP completos neste ambiente porque o Flask não estava instalado.


## Base técnica e limites do cálculo de calagem

O AgroCalc utiliza o método de saturação por bases para estimar a necessidade de calagem na camada de referência de 0–20 cm, com CTC a pH 7: `NC base (t/ha) = max(0, CTC × (V2 − V1) / 100)`. A dose do produto comercial é `NC base × (100 / PRNT)` e o total para o talhão é a dose por hectare multiplicada pela área. A implementação separa explicitamente NC equivalente a PRNT 100% da dose corrigida pelo PRNT para evitar aplicar o fator duas vezes.

O cálculo atende qualquer cultura cadastrada: usa o V2 (V% alvo) configurado no cadastro da cultura selecionada, sem impor um valor exclusivo para soja nem presumir que uma única referência sirva para todas as culturas. O V2 precisa ser definido de acordo com a cultura, região, características do solo e sistema de manejo, com base em recomendação técnica regional ou orientação de profissional habilitado. O AgroCalc não determina automaticamente um V2 universal para cada cultura. A fórmula não substitui a interpretação do laudo nem a validação agronômica.

Como exemplo de referência específica, a Embrapa publica recomendações para soja em Rondônia, mas esse material não deve ser generalizado para outras culturas: https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/983788/1/CT54soja.pdf.


### Validações adicionais da análise de solo

- O potássio informado em mg/dm³ é convertido para cmolc/dm³ dividindo por 391,0; valores já informados em cmolc/dm³ não são convertidos novamente.
- A data da coleta é obrigatória, não pode estar no futuro e laudos com mais de 730 dias são bloqueados para cálculo de recomendação de campo. Esse limite é uma proteção operacional do sistema, não uma regra agronômica universal; o responsável técnico pode ajustá-lo conforme cultura, manejo e protocolo local.
- O resultado exibe o V% alvo usado e alerta quando o V% atual é igual ou superior ao alvo. O V% alvo continua dependendo de validação técnica para cultura, região e manejo.
- Testes unitários: execute `python -m unittest discover -s tests -v` no diretório do projeto.

---

## Entrega e requisitos do 4º bimestre

- O modelo lógico/físico e a análise dos critérios estão em `docs/modelo_logico_fisico.md` e `docs/avaliacao_requisitos_professores.md`.
- O dump vazio da estrutura do banco está em `database/dump_agrocalc_vazio.sql`; a cópia SQLite `calculadora_agricola.db` também está sem registros para testes.
- O banco inclui gatilhos de auditoria para inserção, alteração e exclusão de recomendações de solo.
- Para executar, crie um ambiente virtual, instale `requirements.txt` e inicie com `python app.py`.
- Antes de publicar, defina `AGROCALC_SECRET_KEY` e `AGROCALC_ADMIN_PASSWORD` por variáveis de ambiente com valores fortes. Não use as credenciais padrão em produção.
- **Limitação de Banco de Dados II:** o projeto ainda usa SQLite, que não suporta usuários de SGBD nem procedures/funções armazenadas. Consulte a análise de requisitos antes da entrega para planejar uma migração/alternativa aprovada pelo professor.


## Métodos HTTP no CRUD

As operações de consulta utilizam `GET`; os cadastros utilizam `POST`; as edições utilizam `PUT`; e as exclusões utilizam `DELETE`. Como formulários HTML tradicionais só enviam `GET` e `POST`, `templates/base.html` intercepta os formulários de edição/exclusão e os envia por `fetch` com o método HTTP correto. O token CSRF é enviado no corpo da requisição e validado nas rotas que alteram dados. As rotas continuam aplicando controle de acesso por perfil e validação dos campos antes de persistir alterações.

Para conferir o contrato, procure as rotas de edição (`methods=["GET", "PUT"]`) e exclusão (`methods=["DELETE"]`) em `app.py`. Não remova o script de adaptação do `base.html`, pois ele faz a ponte entre os formulários HTML e os métodos `PUT`/`DELETE`.


## Banco de dados e requisitos de Banco de Dados II

O projeto mantém SQLite como modo padrão para desenvolvimento/teste local. Para usar PostgreSQL com usuários de SGBD separados, função/trigger e procedimento armazenado, consulte `docs/POSTGRESQL_E_SEGURANCA.md` e execute `database/postgresql_setup.sql` uma única vez com uma conta administrativa PostgreSQL. Depois configure `AGROCALC_DATABASE_URL` para a conta restrita `agrocalc_app`. A aplicação não cria tabelas com essa conta: o esquema é instalado previamente pelo script.

O catálogo de calcários e fertilizantes tem cadastro, consulta, edição e exclusão. Edições usam `PUT` e exclusões usam `DELETE` reais por meio do adaptador JavaScript dos formulários, com validação CSRF.
