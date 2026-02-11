-- AULA 12 - min max sum avg --

/*Funções de agregação basicamente agregam ou combinam dados de uma tabela em 1 resultado
*/

select * from 
sales.salesorderdetail 

select top 10 sum(linetotal) as "Soma"
from sales.salesorderdetail

select min(linetotal) as "Minimo"
from Sales.SalesOrderDetail

select avg(linetotal) as "Média"
from sales.SalesOrderDetail

select max(linetotal) as "Maximo"
from Sales.SalesOrderDetail