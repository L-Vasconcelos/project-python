-- AULA 20 - DATAPART

select * from 
Sales.SalesOrderHeader

select
salesorderid, 
DATEPART(month, orderdate) as Mês
from Sales.SalesOrderHeader

select AVG(totaldue) as Média, 
DATEPART(month, orderdate) as Mês
from Sales.SalesOrderHeader
GROUP BY DATEPART(month, orderdate)
order by DATEPART(month, OrderDate) DESC

-- Pratica 

select * from 
Sales.SalesOrderHeader

select 
avg(totaldue) as Média, 
SUM(subtotal) as Total,
DATEPART(year,orderdate) as Ano
from sales.SalesOrderHeader
group by DATEPART(year, orderdate)
order by ano DESC

