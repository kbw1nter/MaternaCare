# 🏥 MaternaCare - Sistema de Gestão de Maternidade

Sistema web desenvolvido para o gerenciamento de pacientes neonatais, alocação de leitos e registros clínicos em uma maternidade.

Este projeto foi desenvolvido como requisito avaliativo para a disciplina de **Banco de Dados** do curso de Ciência da Computação.

## 📋 Sobre o Projeto

O **MaternaCare** é uma aplicação completa que permite o controle do fluxo de uma maternidade, desde o nascimento do bebê até a alta, passando pelo controle de evoluções clínicas e vínculo com responsáveis.

O foco principal do projeto é a implementação prática de conceitos de Banco de Dados Relacional, incluindo:
- Modelagem Entidade-Relacionamento (DER).
- Relacionamentos 1:N e N:N.
- Restrições de Integridade (Foreign Keys).
- **Gatilhos (Triggers)** para validação de dados.
- Consultas SQL complexas com JOINS.

## 🚀 Funcionalidades

- **Dashboard em Tempo Real:** Visualização de taxa de ocupação, total de internados e notificações recentes.
- **Gestão de Pacientes (Bebês):** Cadastro completo, visualização de histórico e status.
- **Gestão de Leitos (Berçário):** Mapa visual de leitos ocupados/disponíveis e sistema de alocação.
- **Prontuário Eletrônico:** Registro de pesagens diárias e evoluções clínicas (medicação/observação).
- **Responsáveis:** Cadastro de familiares e vínculo N:N (Mãe/Pai) com os bebês.
- **Sistema de Notificações:** Alertas automáticos no sistema ao realizar cadastros.

## 🛠 Tecnologias Utilizadas

- **Back-end:** Python 3.9+, Flask.
- **Banco de Dados:** MySQL (Driver: mysql-connector-python).
- **Front-end:** HTML5, CSS3 (Tailwind CSS via CDN), JavaScript.
- **IDE:** VS Code.

## 🗄️ Estrutura do Banco de Dados

O banco de dados `maternidade` conta com as seguintes estruturas principais:

1.  **Tabelas Principais:** `Bebe`, `Leito`, `Responsavel`, `Evolucao_Clinica`.
2.  **Tabela Associativa (N:N):** `Responsavel_Bebe` (permite que um bebê tenha vários responsáveis e vice-versa).
3.  **Triggers:**
    * `verifica_data_evolucao`: Garante a integridade dos dados impedindo que um registro clínico seja criado com data anterior ao nascimento do bebê.