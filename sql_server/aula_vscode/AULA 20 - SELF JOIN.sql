-- AULA 20 - SELF JOIN --
select * from   
Customers

select a.contactname, a.region, b.contactname, b.region
from Customers a, Customers b 
where a.region = b.region

-- Eu quero encontrar nome e data de contratação, de todos --
-- os funionários que foram contratados no mesmo ano -- 

select * from 
Employees

select
a.firstname, a.hiredate, s.firstname, s.hiredate
from Employees as a, Employees as s
where DATEPART(year, a.HireDate) =
DATEPART(year, s.HireDate)

-- Eu quero saber na tabela detalhe do pedido (order details) --
-- Quas produtostem o mesmo percentual de desconto --

select * from 
[Order Details]

select
a.productid, a.discount, 
s.productid, s.discount
from [Order Details] as a, [Order Details] as s
where a.Discount = s.Discount



