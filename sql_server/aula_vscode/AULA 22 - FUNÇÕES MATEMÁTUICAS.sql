-- AULA 22 FUNÇÕES MATEMÁTUICAS

select * from 
Sales.SalesOrderDetail

select 
productid,
orderqty * unitprice as 'Valor Total'
from
Sales.SalesOrderDetail
order by [Valor Total] desc
 
