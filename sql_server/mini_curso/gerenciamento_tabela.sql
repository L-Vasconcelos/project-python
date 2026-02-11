-- gerenciamento de tabelas
-- alter, drop, rename

-- alter table NomeTabela
-- add, alter, drop Objeto;

-- adicionar uma nova coluna
alter table Livro
add Edição smallint;

-- alterar o tipo de dado de uma coluna 
alter table Livro
alter column Edição tinyint;

-- adicionar chave primária
alter table NomeTabela
add primary key (coluna);

-- excluir uma constrsint de uma coluna 
alter table NomeTabela 
drop constraint NomeConstraint;

-- verificar o nome das constraints
sp_help Livro;

-- excluir uma coluna de uma tabela
alter table Livro
drop column Edição;

-- excluir uma tabela 
drop table NomeTebala;

-- renomear uma tabela 
-- sp_rename 'nome atual', 'nome nome';

sp_rename 'Livro', 'tbl_livros';




