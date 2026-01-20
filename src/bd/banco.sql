-- Active: 1765237773821@@127.0.0.1@3306@maternidade
CREATE DATABASE IF NOT EXISTS maternidade;
USE maternidade;

CREATE TABLE Responsavel (
    id_responsavel INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    telefone VARCHAR(20),
    endereco TEXT
);

CREATE TABLE Leito (
    id_leito INT AUTO_INCREMENT PRIMARY KEY,
    numero_quarto INT NOT NULL,
    numero_berco INT NOT NULL,
    tipo VARCHAR(50) -- Ex: UTI, Berçário
);

CREATE TABLE Bebe (
    id_bebe INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100),
    data_nascimento DATETIME NOT NULL,
    peso_nascimento DECIMAL(4,3),
    altura_nascimento DECIMAL(4,2),
    id_leito INT UNIQUE,
    FOREIGN KEY (id_leito) REFERENCES Leito(id_leito)
);

CREATE TABLE Responsavel_Bebe (
    id_responsavel INT,
    id_bebe INT,
    parentesco VARCHAR(50), -- 'Mãe', 'Pai', 'Tio'
    PRIMARY KEY (id_responsavel, id_bebe),
    FOREIGN KEY (id_responsavel) REFERENCES Responsavel(id_responsavel),
    FOREIGN KEY (id_bebe) REFERENCES Bebe(id_bebe)
);

CREATE TABLE Evolucao_Clinica (
    id_evolucao INT AUTO_INCREMENT PRIMARY KEY,
    id_bebe INT NOT NULL,
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    descricao TEXT,
    id_funcionario INT, 
    FOREIGN KEY (id_bebe) REFERENCES Bebe(id_bebe) ON DELETE CASCADE
);

USE maternidade;

ALTER TABLE Evolucao_Clinica 
ADD COLUMN peso_atual DECIMAL(4,3) AFTER descricao;

-- dados de teste
INSERT INTO Leito (numero_quarto, numero_berco, tipo) VALUES (101, 1, 'Berçário Comum');
INSERT INTO Bebe (nome, data_nascimento, peso_nascimento, altura_nascimento, id_leito) 
VALUES ('Bebê Teste', NOW(), 3.500, 48.0, 1);

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

-- consultas Obrigatórias --

-- 1. listagem simples de bebês
SELECT * FROM Bebe ORDER BY nome;

-- 2. contagem de bebês por leito
SELECT id_leito, COUNT(*) as qtd_bebes FROM Bebe GROUP BY id_leito;

-- 3. bebês e seus respectivos quartos 
SELECT b.nome, l.numero_quarto, l.tipo 
FROM Bebe b 
JOIN Leito l ON b.id_leito = l.id_leito;

-- 4. responsáveis e seus Bebês
SELECT r.nome as responsavel, rb.parentesco, b.nome as bebe
FROM Responsavel r
JOIN Responsavel_Bebe rb ON r.id_responsavel = rb.id_responsavel
JOIN Bebe b ON rb.id_bebe = b.id_bebe;

-- 5. mapa do berçário completo
SELECT l.numero_berco, l.numero_quarto, b.nome as ocupante
FROM Leito l
LEFT JOIN Bebe b ON l.id_leito = b.id_leito
ORDER BY l.numero_quarto;

-- 6. histórico clínico detalhado 
SELECT b.nome, e.data_hora, e.descricao, e.peso_atual
FROM Evolucao_Clinica e
JOIN Bebe b ON e.id_bebe = b.id_bebe
ORDER BY e.data_hora DESC;