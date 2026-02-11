-- inserir registros

-- tabela de assuntos
insert into Assunto (NomeAssunto)
values
('Ficção Científica'), ('Botânica'),
('Eletronica'), ('Matemática'),
('Aventura'), ('Romance'), 
('Finanças'), ('Gastronomia'),
('Terror'), ('Administração'), 
('Informatica'), ('Suspense');

insert into Editora (NomeEditora)
values
('Prentice Hall'), ('O Reilly');

insert into Editora (NomeEditora)
values 
('Aleph'), ('Microsoft Press'),
('Wiley'), ('HarperCollins'),
('Érica'), ('Novatec'),
('McGraw-Hill'), ('Sybex'), 
('Globo'), ('Companhia das Letras'),
('Morro Branco'), ('Penguin Books'), ('Matin Claret'),
('Record'), ('Springer'), ('Melhoramentos'), 
('Oxford'), ('Taschen'), ('Ediouro'), ('Bookman');


insert into Editora (NomeEditora)
values 
('Apress'), ('Francisco Alves');

-- tabela de autores 

-- 1. inserir um linha única
insert into Autor (NomeAutor, SobrenomeAutor)
values ('Umberto', 'Eco');

insert into Autor (NomeAutor, SobrenomeAutor)
values 
('Daniel', 'Barret'), ('Gerald', 'Carter'), ('Mark', 'Sobell'),
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

--  tabela de livros
insert into Livro (NomeLivro, ISBN13, DataPub, 
PreçoLivro, NumeroPaginas, IdAssunto, IdEditora)
values 
(' A Arte da Eletrônica', 
'9788582604342', '20170308', 
300.74, 1160, 3, 24);

insert into Livro (NomeLivro, ISBN13, DataPub, 
PreçoLivro, NumeroPaginas, IdAssunto, IdEditora)
values 
('Vinte Mil Léguas Submarinas', '9788582850022', '2014-09-16', 24.50, 448, 1, 16), -- Júlio Verne
('O Investidor Inteligente', '9788595080805', '2016-01-25', 79.90, 450, 7, 6); -- Benjamin Graham

-- insetir um lote (bulk) a partir de arquivo csv
insert into Livro (NomeLivro, ISBN13, DataPub,
PreçoLivro, NumeroPaginas, IdEditora, IdAssunto)
select 
NomeLivro, ISBN13, DataPub, PrecoLivro,
NumeroPaginas, IdEditora, IdAssunto
from openrowset(
bulk 'C:\Program Files\Microsoft SQL Server\Livros.csv',
formatfile = 'C:\Program Files\Microsoft SQL Server\Formato.xml',
codepage = '65001', -- UTF-8
firstrow = 2 -- a partir da linha 2, pois a primeira é o cabeçalho 
)
as LivrosCVS; -- idetificador do openrowset

insert into LivroAutor (IdLivro, IdAutor)
values 
(100,15),
(100,16),
(101,27),
(102,26),
(103,41),
(104,24),
(105,32),
(106,20),
(107,27),
(108,1),
(109,22),
(110,10),
(111,21),
(112,5),
(113,10),
(114,8),
(115,18),
(115,19),
(116,31),
(117,22);

select * from Livro
select * from LivroAutor
select * from Autor

select 
l.NomeLivro, 
a.NomeAutor,
a.SobrenomeAutor
from Livro as l
inner join LivroAutor as la on
l.IdLivro = la.IdLivro
inner join Autor as a on 
a.IdAutor = la.IdAutor
order by NomeLivro;

