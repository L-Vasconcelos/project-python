-- AULA 07 - ORDER BY <> VARIAÇÕES --

select *
from person.Person
order by firstname desc

select *
from person.Person
order by firstname asc

select firstname as 'Primeiro Nome',
lastname as 'Ultimo Nome'
from person.Person
order by firstname asc, 
lastname desc

/*Desafio 1
Obter o productid dos 10 produtos mais caros cadstrados no sistema, listando do 
mais caro para o mais barato*/

select top 10 Productid
from Production.Product
order by listprice desc

/*Desafio 2
Obter o nome e numero do produto que tem o productid entre 1~4
*/

select top 4 name, productnumber 
from production.product 
order by productid asc