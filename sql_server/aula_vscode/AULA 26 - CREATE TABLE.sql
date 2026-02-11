-- AULA 26 - CREATE TABLE 

/* CREATE TABLE nome da tabela (
    coluna1 tipo restriçãodacoluna,
    coluna2 tipo ,
    coluna3 tipo ,
);

/* Principais tipos de restrições que podem ser aplicadas 
 - NOT NULL - Não permite nulos 
 - UNIQUE - Força que todos os valores em uma coluna sejam diferentes
 - PRIMARY KEY - uMA JUNÇÃO do NOT NULL e UNIQUE 
 - FORIGN KEY - Identifica unicamente uma linha em outra tabela 
 - CHECK -- força uma condição especifíca em uma coluna 
 - DEFAULT - força uma valor padrão quando nenhem valor é passado */

create table Canal (
CanalId int primary key,
Nome Varchar (150) not null,
ContagemInscritos int default 0,
DataCriacao datetime not null 
);

create table Video (
VideoId int primary key,
Nome varchar(150) not null, 
vizualizacoes int default 0,
Likes int default 0, 
Dislikes int default 0, 
Duracao int not null,
CanalId int foreign key references Canal(CanalId)
);

