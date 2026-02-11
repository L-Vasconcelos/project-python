-- tabela assunto

insert into Assunto (nome_assunto)
values 
('Ficção Científica'), ('Botânica'),
('Eletrônica'), ('Matemática'), 
('Finanças'), ('Administração'),
('Programação'), ('Suspense');


select * from Assunto;

sp_help assunto;

---------------------------------------------------------------------

-- tabela editora

insert into Editora (nome_editora)
values 
('Pretince Hall'), ('Burguer Paradise'),
('Zézão Company'), ('Magrão Sinistro');

insert into Editora (nome_editora)
values 
('Aleph'), ('Microsoft Press'),
('Wiley'), ('HarperCollins'),
('Érica'), ('Novatec'),
('McGraw-Hill'), ('Apress'),
('Francisco Alves'), ('Sybex'),
('Globo'), ('Companhia das Letras'),
('Morro Branco'), ('Penguin Books'), ('Martin Claret'),
('Record'), ('Springer'), ('Melhoramentos'),
('Oxford'), ('Taschen'), ('Ediouro'),('Bookman');

select * from Editora;

---------------------------------------------------------------------

-- tabela autores

insert into Autor (nome_autor, sobrenome_autor)
values 
('Umberto', 'Eco');

insert into Autor (nome_autor, sobrenome_autor) -- preenchimento de duas colunas em conjunto
values 
('Daniel', 'Fraga'), ('Gerald', 'Carter'), ('Mark', 'Sobell'),
('William', 'Stanek'), ('Christine', 'Bresnahan'), ('William', 'Gibson'),
('James', 'Joyce'), ('John', 'Emsley'), ('José', 'Saramago'),
('Richard', 'Silverman'), ('Robert', 'Byrnes'), ('Jay', 'Ts'),
('Robert', 'Eckstein'), ('Paul', 'Horowitz'), ('Winfield', 'Hill'),
('Joel', 'Murach'), ('Paul', 'Scherz'), ('Simon', 'Monk'),
('George', 'Orwell'), ('Ítalo','Calvino'), ('Machado','de Assis'),
('Oliver', 'Sacks'), ('Ray', 'Bradbury'), ('Walter', 'Isaacson'),
('Benjamin','Graham'), ('Júlio','Verne'), ('Marcelo', 'Gleiser'),
('Harri','Lorenzi'), ('Humphrey', 'Carpenter'), ('Isaac', 'Asimov'),
('Aldous', 'Huxley'), ('Arthur','Conan Doyle'), ('Blaise', 'Pascal'),
('Jostein', 'Gaarder'), ('Stephen', 'Hawking'), ('Stephen', 'Jay Gould'),
('Neil', 'De Grasse Tyson'), ('Charles', 'Darwin'), ('Alan', 'Turing'), ('Arthur', 'C. Clarke');

select * from Autor;

---------------------------------------------------------------------

-- tabela livros

insert into Livro (nome_livro, isbn13, data_pub, preco_livro,
numero_paginas, id_editora, id_assunto)
values
('A Arte da Eletrônica', '9788582604342',
'20170308', 300.74,  1160, 3, 24);

insert into Livro (nome_livro, isbn13, data_pub, preco_livro,
numero_paginas, id_editora, id_assunto)
values
('A Arte da Eletrônica 2', '9788582604343',
'20180308', 320.74,  1580, 24, 3);

insert into Livro (nome_livro, isbn13, data_pub, preco_livro,
numero_paginas, id_editora, id_assunto)
values
('A Arte da Eletrônica 3', '9788582604344',
'20190308', 340.74,  1650, 24, 3);


-- inserção de dados em massa bulk (formato csv_xml)

insert into Livro (nome_livro, isbn13, data_pub, preco_livro, 
numero_paginas, id_editora, id_assunto)
select 
	nome_livro, isbn13, data_pub, preco_livro, 
	numero_paginas, id_editora, id_assunto
from openrowset (
	bulk 'C:\Mini_Curso_SQL\biblioteca_02\Livros.csv',
	formatfile = 'C:\Mini_Curso_SQL\biblioteca_02\Formato.xml',
	codepage = '65001', -- UFT-8
	firstrow = 2
	) as livros_csv;

	select * from Livro;
	select * from Assunto;