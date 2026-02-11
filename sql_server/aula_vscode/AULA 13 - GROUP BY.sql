-- AULA 13 - GROUP BY --

/*
Divide o resltado da sua pesquisa em grupos
Para cada grupo você pode aplicar uma função de agregação, 
Calcular a soma de itens
contar o número de itens naquele grupo
*/

select 
color, 
AVG(listprice) as "media de preco"
from Production.Product
where color = 
'Silver' or color = 'black'
group by color 

select * from 
Sales.SalesOrderDetail

select specialofferid, sum(unitprice) as "Soma"
from Sales.SalesOrderDetail
group by SpecialOfferID

select productid, count(productid) as"Contagem"
from Sales.SalesOrderDetail
group by ProductID

select * from 
Person.Person

select firstname, 
count(firstname)
from Person.Person
group by firstname

select * from 
Production.Product

select color,
avg(listprice) as "Média"
from Production.Product
group by color

select color, 
avg(listprice) as "Média"
from Production.Product
where color = 'silver'
group by color

/*1 - Eu preciso saber quantas pessoas tem o mesmo middlename agrupadas por middlename
*/

select middlename, 
count(middlename) as "Quantidade"
from Person.person
group by MiddleName

/*2 - Eu preciso saber em média qual é a quantidade que cada produto é vendida na loja
> tabela sales.salesorderdetail
> usar group by e um códido de agragação
*/

select * from 
Sales.SalesOrderDetail

select Productid,
avg(orderqty) as "média"
from Sales	.SalesOrderDetail
group by ProductID

/*3 - Eu quero saber qual foram as 10 vendas que no total tiveram os maiores valores de venda por
produto do maior valor para o menor
> tabelasales.salesorderdetail 
> usar group by e um código de agragação
> se atantar a por o que você está ordenando
*/

select top 10 Productid, 
sum(linetotal) as "Soma Total"
from Sales.SalesOrderDetail
group by productid
order by sum(linetotal) desc

/*4 - Eu preciso saber quantos produtos e qual quantidade média de produtos temos 
cadastrados nas nossas ordens de serviço
> usar a tabela production.workorder
> usar group by e uma função de agragação
*/

select * from 
Production.WorkOrder

select productid,
count(productid) as "Contagem",
avg(orderqty) as "Média"
from Production.WorkOrder
group by productid