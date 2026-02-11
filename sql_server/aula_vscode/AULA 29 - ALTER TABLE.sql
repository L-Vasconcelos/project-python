-- AULA 29 - ALTER TABLE

-- Adicionar Informação

alter table redTube
add ativo BIT

select * from 
RedTube

-- Alteração de condicionais da tabela 

alter table redtube 
alter column categoria 
varchar (300) not null

-- Alteração de nome de coluna / tabela 

EXEC sp_rename 'RedTube2.0', 'RedTube'

select * from 
RedTube