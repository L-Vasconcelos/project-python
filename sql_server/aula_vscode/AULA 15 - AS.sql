-- AULA 15 - AS -- 
/*Renomear colunas e agregações
*/

select top 10 ListPrice as "Preço"
from Production.Product

select top 10 
avg(listprice) as "Média de Preço"
from Production.Product


--1) Econtrar o firstname e lastname person.peron 
--2) Productnumber da tabela production.product "Numero do Produto"
--2) Sales,slaesorderdetail unitprice "Preço Unitário"

select top 10 
firstname as " Nome", 
lastname as "Sobrenome"
from Person.person

select top 10 
productnumber as "Numero do Produto "
from production.product

select unitprice as "Preço Unitário"
from Sales.SalesOrderDetail