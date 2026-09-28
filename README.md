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

O AgroCalc também possui estrutura para trabalhar com informações de fertilizantes e culturas, permitindo organizar os dados utilizados no processo de recomendação de adubação.

A proposta é relacionar:

```text
Análise de solo
       +
Cultura
       +
Necessidade de nutrientes
       +
Fertilizante selecionado
       ↓
Recomendação
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
