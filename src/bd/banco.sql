-- 1. Criação do Banco
DROP DATABASE IF EXISTS maternidade;
CREATE DATABASE maternidade;
USE maternidade;

-- ==========================================
-- TABELAS FORTES (Sem chaves estrangeiras)
-- ==========================================

CREATE TABLE Quarto (
    id_quarto INT AUTO_INCREMENT PRIMARY KEY,
    numero_quarto INT UNIQUE NOT NULL,
    tipo VARCHAR(50) NOT NULL -- Ex: 'UTI Neonatal', 'Berçário Comum'
);

CREATE TABLE Funcionario (
    id_funcionario INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cargo VARCHAR(50) NOT NULL,
    crm_coren VARCHAR(30) UNIQUE -- Registro profissional
);

CREATE TABLE Responsavel (
    id_responsavel INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    telefone VARCHAR(20),
    -- Endereço Normalizado (1FN)
    logradouro VARCHAR(150),
    numero VARCHAR(10),
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    estado CHAR(2),
    -- Controle de Status
    status VARCHAR(20) DEFAULT 'Ativo',
    data_saida DATETIME NULL
);

CREATE TABLE Notificacao (
    id_notificacao INT AUTO_INCREMENT PRIMARY KEY,
    mensagem TEXT NOT NULL,
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    lida BOOLEAN DEFAULT FALSE
);

-- ==========================================
-- TABELAS COM DEPENDÊNCIAS (Chaves estrangeiras)
-- ==========================================

CREATE TABLE Leito (
    id_leito INT AUTO_INCREMENT PRIMARY KEY,
    id_quarto INT NOT NULL,
    numero_berco INT NOT NULL,
    FOREIGN KEY (id_quarto) REFERENCES Quarto(id_quarto) ON DELETE CASCADE
);

CREATE TABLE Bebe (
    id_bebe INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100),
    data_nascimento DATETIME NOT NULL,
    peso_nascimento DECIMAL(4,3),
    altura_nascimento DECIMAL(4,2),
    id_leito INT UNIQUE,
    status VARCHAR(20) DEFAULT 'Ativo',
    data_saida DATETIME NULL,
    FOREIGN KEY (id_leito) REFERENCES Leito(id_leito) ON DELETE SET NULL
);

CREATE TABLE Responsavel_Bebe (
    id_responsavel INT,
    id_bebe INT,
    parentesco VARCHAR(50) NOT NULL,
    PRIMARY KEY (id_responsavel, id_bebe),
    FOREIGN KEY (id_responsavel) REFERENCES Responsavel(id_responsavel) ON DELETE CASCADE,
    FOREIGN KEY (id_bebe) REFERENCES Bebe(id_bebe) ON DELETE CASCADE
);

CREATE TABLE Evolucao_Clinica (
    id_evolucao INT AUTO_INCREMENT PRIMARY KEY,
    id_bebe INT NOT NULL,
    id_funcionario INT NOT NULL, 
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    descricao TEXT NOT NULL,
    peso_atual DECIMAL(6,3),
    FOREIGN KEY (id_bebe) REFERENCES Bebe(id_bebe) ON DELETE CASCADE,
    FOREIGN KEY (id_funcionario) REFERENCES Funcionario(id_funcionario)
);

-- ==========================================
-- GATILHOS (TRIGGERS)
-- ==========================================

DELIMITER //

CREATE TRIGGER verifica_data_evolucao
BEFORE INSERT ON Evolucao_Clinica
FOR EACH ROW
BEGIN
    DECLARE data_nasc DATETIME;
    
    -- busca a data de nascimento do bebê que está recebendo a evolução
    SELECT data_nascimento INTO data_nasc
    FROM Bebe
    WHERE id_bebe = NEW.id_bebe;
    
    -- se a data da evolução for menor (anterior) que o nascimento, cancela com erro
    IF NEW.data_hora < data_nasc THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Erro de Integridade: A evolução não pode ser anterior ao nascimento do bebê.';
    END IF;
END;
//

DELIMITER ;