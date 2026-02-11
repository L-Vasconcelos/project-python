/* select coluna(s)
into nova_tabela
from tabela_atual*/

select NomeLivro, ISBN13
into LivroISBN
from livro;

drop table LivroISBN;

select * from Livro

select 
NomeLivro, 
PreçoLivro,
DataPub
from Livro

select * from Autor

select 
NomeAutor
from Autor

select * from Assunto