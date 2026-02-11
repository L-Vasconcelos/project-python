-- Criando a tabela de Empresa
CREATE TABLE Empresa (
    id_empresa SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL
);

-- Criando a tabela de Moeda
CREATE TABLE Moeda (
    id_moeda SERIAL PRIMARY KEY,
    nome VARCHAR(50) NOT NULL,
    taxa_cambio DECIMAL(10,4)
);

-- Criando a tabela de Faturamento
CREATE TABLE Faturamento (
    id_faturamento SERIAL PRIMARY KEY,
    id_empresa INT REFERENCES Empresa(id_empresa),
    id_moeda INT REFERENCES Moeda(id_moeda),
    data DATE NOT NULL,
    valor DECIMAL(15,2) NOT NULL
);

-- Criando a tabela de Vendas
CREATE TABLE Vendas (
    id_venda SERIAL PRIMARY KEY,
    id_empresa INT REFERENCES Empresa(id_empresa),
    data DATE NOT NULL,
    qtd_vendida_mi DECIMAL(15,2),
    qtd_vendida_me DECIMAL(15,2)
);