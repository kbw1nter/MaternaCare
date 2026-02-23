DROP DATABASE IF EXISTS maternidade;
CREATE DATABASE maternidade;
USE maternidade;

CREATE TABLE Quarto (
    id_quarto INT AUTO_INCREMENT PRIMARY KEY,
    numero_quarto INT UNIQUE NOT NULL,
    tipo VARCHAR(50) NOT NULL -- ex: 'UTI Neonatal', 'Berçário Comum'
);

CREATE TABLE Funcionario (
    id_funcionario INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cargo VARCHAR(50) NOT NULL,
    crm_coren VARCHAR(30) UNIQUE
);

CREATE TABLE Responsavel (
    id_responsavel INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    telefone VARCHAR(20),
    -- endereço normalizado (1FN)
    endereco VARCHAR(255),
    -- controle de status
    status VARCHAR(20) DEFAULT 'Ativo',
    data_saida DATETIME NULL
);

CREATE TABLE Notificacao (
    id_notificacao INT AUTO_INCREMENT PRIMARY KEY,
    mensagem TEXT NOT NULL,
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    lida BOOLEAN DEFAULT FALSE
);

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

-- triggers 
DELIMITER //

CREATE TRIGGER verifica_data_evolucao
BEFORE INSERT ON Evolucao_Clinica
FOR EACH ROW
BEGIN
    DECLARE data_nasc DATETIME;
    
    SELECT data_nascimento INTO data_nasc FROM Bebe WHERE id_bebe = NEW.id_bebe;
    
    IF NEW.data_hora < data_nasc THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Erro de Integridade: A evolução não pode ser anterior ao nascimento do bebê.';
    END IF;
END;
//

DELIMITER ;

-- inserção de dados

-- quartos
INSERT INTO Quarto (numero_quarto, tipo) VALUES 
(101, 'Berçário Comum'),
(102, 'Berçário Comum'),
(200, 'UTI Neonatal');

-- leitos vinculados aos quartos
INSERT INTO Leito (id_quarto, numero_berco) VALUES 
(1, 1), (1, 2), (1, 3), (1, 4), -- Quarto 101
(2, 5), (2, 6), (2, 7), (2, 8), -- Quarto 102
(3, 1), (3, 2);                 -- Quarto 200 (UTI)

-- funcionários
INSERT INTO Funcionario (nome, cargo, crm_coren) VALUES 
('Dr. Roberto Almeida', 'Pediatra', 'CRM-RS 12345'),
('Enf. Joana Silva', 'Enfermeira', 'COREN-RS 54321');

-- notificação Inicial
INSERT INTO Notificacao (mensagem) VALUES ('Bem-vindo ao sistema MaternaCare!');

-- dados de teste (responsáveis e Bebês)
INSERT INTO Responsavel (nome, cpf, telefone, status) VALUES 
('Julia Silveira', '111.222.333-44', '(53) 99999-1111', 'Ativo');

INSERT INTO Bebe (nome, data_nascimento, peso_nascimento, altura_nascimento, id_leito, status) VALUES 
('Bebê da Julia', DATE_SUB(NOW(), INTERVAL 1 DAY), 3.450, 49.5, 1, 'Ativo');

INSERT INTO Responsavel_Bebe (id_responsavel, id_bebe, parentesco) VALUES (1, 1, 'Mãe');

INSERT INTO Evolucao_Clinica (id_bebe, id_funcionario, descricao, peso_atual) VALUES 
(1, 1, 'Bebê estável, amamentando bem.', 3.400);

-- teste inserindo bebê no neonatal
INSERT INTO Bebe (nome, data_nascimento, peso_nascimento, altura_nascimento, id_leito, status) 
VALUES ('Bebê Prematuro (Teste)', NOW(), 2.100, 42.0, 9, 'Ativo');

-- consultas de exemplo

-- consulta 1: listagem simples de bebês
SELECT nome, data_nascimento, peso_nascimento FROM Bebe WHERE status = 'Ativo';

-- consulta 2: contagem de leitos por tipo de quarto
SELECT q.tipo, COUNT(l.id_leito) as qtd_bercos 
FROM Leito l JOIN Quarto q ON l.id_quarto = q.id_quarto GROUP BY q.tipo;

-- consulta 3: mapa do berçário completo (LEFT JOIN)
SELECT q.numero_quarto, q.tipo, l.numero_berco, b.nome as ocupante
FROM Leito l
JOIN Quarto q ON l.id_quarto = q.id_quarto
LEFT JOIN Bebe b ON l.id_leito = b.id_leito
ORDER BY q.numero_quarto, l.numero_berco;

-- consulta 4: responsáveis e seus bebês (DUPLO JOIN)
SELECT r.nome as responsavel, rb.parentesco, b.nome as bebe
FROM Responsavel r
JOIN Responsavel_Bebe rb ON r.id_responsavel = rb.id_responsavel
JOIN Bebe b ON rb.id_bebe = b.id_bebe;

-- consulta 5: histórico clínico com o médico responsável (DUPLO JOIN)
SELECT b.nome as paciente, e.data_hora, e.descricao, f.nome as medico_assinante
FROM Evolucao_Clinica e
JOIN Bebe b ON e.id_bebe = b.id_bebe
JOIN Funcionario f ON e.id_funcionario = f.id_funcionario
ORDER BY e.data_hora DESC;

-- consulta 6: ocupação atual das UTIs neonatais (JOIN)
SELECT b.nome as bebe_em_uti, l.numero_berco, q.numero_quarto
FROM Bebe b
JOIN Leito l ON b.id_leito = l.id_leito
JOIN Quarto q ON l.id_quarto = q.id_quarto
WHERE q.tipo = 'UTI Neonatal';

-- teste de trigger
INSERT INTO Evolucao_Clinica (id_bebe, id_funcionario, data_hora, descricao, peso_atual) 
VALUES (1, 1, '2020-01-01 10:00:00', 'Tentativa de fraude na data', 3.000);