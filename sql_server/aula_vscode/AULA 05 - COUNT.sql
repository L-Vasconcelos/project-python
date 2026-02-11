-- AULA 05 - COUNT <> VARIAÇÕES --

select count(*)
from person.person

select count (distinct title)
from person.person;


/*Desafio 1
quantos produtos temos cadastrados em nossa tabela de produtos (production.product)*/

select count(*) as 'qtd produto'
from Production.Product; 

/*Desafio 2
Quantos tamanhos de produtos te,ps cadastrado em nossa tabela*/

select count (size)
from Production.Product;