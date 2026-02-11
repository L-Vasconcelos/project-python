create table Autor (
id_autor smallint identity, -- geral  id de forma automatica
nome_autor varchar (50) not null,
sobrenome_autor varchar (60) not null, 
constraint pk_id_autor primary key (id_autor)
);

sp_help autor; -- verificação de criação de tabela

---------------------------------------------------------------------

create table Editora(
id_editora smallint primary key identity,
nome_editora varchar (50) not null);

---------------------------------------------------------------------

create table Assunto(
id_assunto tinyint primary key identity,
nome_assunto varchar (25) not null);

---------------------------------------------------------------------

create table Livro(
id_livro smallint not null primary key identity (100,1),
nome_livro varchar (70) not null, 
isbn13 char (13) unique not null, 
data_pub date,
preco_livro money not null,
numero_paginas smallint not null,
id_editora smallint not null,
id_assunto tinyint not  null, 
constraint fk_id_editora foreign key (id_editora)
references Editora(id_editora) on delete cascade, /* cascade, se o a informação for excluida na tavbela editora, sera atualizada automaticamente */
constraint fk_id_assunto foreign key (id_assunto)
references Assunto (id_assunto) on delete cascade,
constraint verifica_preco check (preco_livro >=0));

---------------------------------------------------------------------

create table Livro_Autor(
id_livro smallint not null,
id_autor smallint not null,
constraint fk_id_livros foreign key (id_livro) references Livro (id_livro),
constraint fk_id_autores foreign key (id_autor) references Autor (id_autor),
constraint pk_livro_autor primary key (id_livro, id_autor));

select name from biblioteca_02.sys.tables; -- verificação de tabelas

---------------------------------------------------------------------