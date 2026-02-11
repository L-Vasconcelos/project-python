-- AULA 10 - LIKE -- 

/*Vamos dizer que voce quer encontrar uma pessoa no banco de dados 
que vc sabe que o nome dlea era ....... alguma coisa, alguma parte do nome 
*/

select * from Person.Person
where firstname like 
'ovi%'

select * from Person.Person
where firstname like 
'%essa%'

/*Desafios 
1 - Quantos produtos temos cadastrados no sistema que custam mais que 1500?
> tera que usar a tabela production.product
>terá que usar count e where e mais algum operador de comparação
*/

select count(listprice)
from Production.Product
where ListPrice >1500

/*2 - Quantas pessoas atemos com o sobrenome que inicia com a letra P?
> terá que usar a tabela person.person
> terá que usar count, where e like
*/

select count(lastname)
from Person.Person
where lastname like 'p%'

/*3 - Em quantas cidades unicas estão cadastrados nossos clientes
> terá que usar a tabela person.address
> terá que usar count, distinct 
*/

select count(distinct(city)
from person.address

/*4 - Quais são as cidades únicas que temos cadastrados em nosso sistema? 
> terá que usar a tabela person.address
> será bem similar a resposta anterior
*/

select distinct (city)
from person.person

/*5 - Quantos perodutos vermelhos tem preço entre 500 a 100 dolares 
> terá que usar a tebala prodcution.product 
> terá que usar where, between
*/

select count(*)
from production.product 
where color = 'red'
and listprice between 500 and 1000 

/*6 - Quantos proutos cadastrados tem a palavra 'road' no nome deles? 
> terá que usar a tabela production.product 
> terá que usar count, like
*/

select count(*)
form production.product
where name like '%road%';