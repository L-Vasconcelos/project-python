create table Autor (
IdAutor smallint identity, -- identity -> ao inserir o nome do autor, um novo id vai ser criado automaticamente 
NomeAutor varchar(50) not null,
SobrenomeAutor varchar(60) not null, 
constraint pk_id_autor primary key (IdAutor)
);

sp_help Autor; --consulta de tabela criada com especificações 

create table Editora(
IdEditora smallint primary key identity,
NomeEditora varchar(50) not null
);

create table Assunto(
IdAssunto tinyint primary key identity,
NomeAssunto varchar (25) not null
);

create table Livro(
IdLivro smallint not null primary key identity(100,1), --gerando numero a partir de 100 de 1 em 1
NomeLivro varchar (70) not null, 
ISBN13 char (13) unique not null,  -- unique cada livro tem seu cód <>, não podemos deixar que se repita para livros diferentes 
DataPub date, 
PreçoLivro money not null, 
NumeroPaginas smallint not null,
IdEditora smallint not null,
IdAssunto tinyint not null,
constraint fk_id_editora foreign key (IdEditora) -- puxando chave estrangeira 
references Editora (IdEditora) on delete cascade, -- caso delete na tabela Editora, automaticamente deleta na tabeala Livro
constraint fk_id_assunto foreign key (IdAssunto)
references Assunto (IdAssunto) on delete cascade,
constraint verifica_preco check (PreçoLivro >=0) --condição para que o valor do livro não seja negativo, caso venha a ser, valor entra como null
);

create table LivroAutor(
IdLivro smallint not null,
IdAutor smallint not null,
constraint fk_id_livros foreign key (IdLivro) references Livro (IdLivro),
constraint fk_id_autores foreign key (IdAutor) references Autor (IdAutor),
constraint pk_livro_autor primary key (IdLivro, IdAutor)
);

select name from biblioteca.sys.tables
order by name;