-- AULA 17 - INNER JOIN + VARIAÇÕES --
/*
left join retorna um conjuneto de todos os registros da tabelaA,
e alem disso, os registros correspondentes (quando disponíveis) na 
tabelaB. Se não houver registtros correspondentes ele simplesmente
vai preencher null.

inner join retorna apenas os resultados que correspondem (existem)
tanto na tabelaA como na tabelaB
*/ 

select *  from 
Person.Person

select * from 
Person.BusinessEntity

select 
pp.businessentityid, 
pp.firstname, 
pp.lastname, 
additionalcontactinfo, 
pe.rowguid
from Person.Person as pp
inner join Person.BusinessEntity as pe on
pp.BusinessEntityID = 
pe.BusinessEntityID

select * from 
Person.Person

select * from 
Person.EmailAddress

select 
pp.businessentityid, 
pp.firstname, 
pp.lastname, 
additionalcontactinfo, 
pe.emailaddress
from Person.Person as pp
inner join Person.EmailAddress as pe on
pp.BusinessEntityID = 
pe.BusinessEntityID

select * from 
Person.PhoneNumberType

select * from 
Person.PersonPhone

select 
pt.phonenumbertypeid, 
pt.name, 
pp.phonenumber
from person.PhoneNumberType as pt
inner join Person.PersonPhone as pp on 
pt.PhoneNumberTypeID = 
pp.PhoneNumberTypeID

select * from 
Person.StateProvince

select * from 
Person.Address

select 
ps.stateprovinceid, 
ps.stateprovincecode,
pa.city,
ps.name, 
pa.addressline1, 
pa.postalcode
from Person.StateProvince as ps
inner join Person.Address as pa on
ps.StateProvinceID = 
pa.StateProvinceID

select * from 
Production.Product

select * from 
Production.ProductCategory

select 
pc.productcategoryid, 
pp.name, 
pc.name,
pp.productnumber, 
pp.listprice
from Production.ProductCategory as pc
inner join Production.Product as pp on
pc.ProductCategoryID = 
pp.ProductSubcategoryID

select * from 
sales.SalesOrderHeader

select * from 
Sales.SalesOrderDetail

select 
po.salesorderid, 
po.salespersonid,
po.orderdate, 
po.shipdate, 
po.salesordernumber, 
ps.unitprice, 
ps.linetotal
from Sales.SalesOrderHeader as po 
inner join Sales.SalesOrderDetail as ps on
po.SalesOrderID = 
ps.SalesOrderID

select * from 
Production.ProductCategory

select * from 
Production.ProductSubcategory

select 
pc.productcategoryid, 
pc.name, 
pb.name
from Production.ProductCategory as pc
inner join Production.ProductSubcategory as pb on
pc.ProductCategoryID = 
pb.ProductCategoryID

select * from 
Purchasing.ProductVendor

select * from
Purchasing.Vendor

select 
pp.businessentityid, 
pp.averageleadtime, 
pp.standardprice, 
pv.accountnumber, 
pv.name, 
purchasingwebserviceurl
from Purchasing.ProductVendor as pp
left join Purchasing.Vendor as pv on
pp.BusinessEntityID = 
pv.BusinessEntityID
where pv.AccountNumber is null

select 
pp.businessentityid, 
pp.averageleadtime, 
pp.standardprice, 
pv.accountnumber, 
pv.name, 
purchasingwebserviceurl
from Purchasing.ProductVendor as pp
inner join Purchasing.Vendor as pv on
pp.BusinessEntityID = 
pv.BusinessEntityID


-- Prática LEFT JOIN --

select * from 
Sales.PersonCreditCard

select * from 
Person.Person

select * from 
Person.Person as pp
inner join Sales.PersonCreditCard as pc on
pp.BusinessEntityID = 
pc.BusinessEntityID

select top 10 * from 
Person.Person as pp
left join  Sales.PersonCreditCard as pc ON
pp.BusinessEntityID = 
pc.BusinessEntityID
where pc.BusinessEntityID is NULL

select 
pp.businessentityid,
pp.firstname, 
pb.addressid,
pb.addresstypeid
from 
Person.Person as pp
left join Person.BusinessEntityAddress as pb on 
pp.BusinessEntityID = pb.BusinessEntityID
where pp.BusinessEntityID >= 5000
order by pp.BusinessEntityID asc

select * from 
Person.Person

select * from 
Person.BusinessEntity

select 
pp.businessentityid, 
pp.firstname, 
pp.lastname, 
pb.modifieddate
from 
Person.Person as pp 
inner JOIN Person.BusinessEntity as pb on 
pp.BusinessEntityID = 
pb.BusinessEntityID

-- group by exercicios --

select * from 
Sales.SalesOrderDetail

select 
color, 
AVG(listprice) as "media de preco"
from Production.Product
where color = 
'Silver' or color = 'black'
group by color 

select * from Production.Product

select
color,
max(listprice) as "Preço Max"
from Production.Product
where color = 
'silver' or Color = 'black' 
group by color

/*1 - Eu preciso saber quantas pessoas tem o mesmo middlename agrupadas por middlename*/

select * from 
Person.Person

select 
middlename, 
count(middlename) as 'QTD MIDDLE'
from Person.Person
group by MiddleName

/*2 - Eu preciso saber em média qual é a quantidade que cada produto é vendida na loja
> tabela sales.salesorderdetail
> usar group by e um códido de agragação
*/

select * from 
Sales.SalesOrderDetail

select 
ProductID, 
AVG(orderqty) as 'Média de Qtd Vendida'
from Sales.SalesOrderDetail
group by ProductID

/*3 - Eu quero saber qual foram as 10 vendas que no total tiveram os maiores valores de venda por
produto do maior valor para o menor
> tabelasales.salesorderdetail 
> usar group by e um código de agragação
> se atantar a por o que você está ordenando
*/

select * from 
Sales.SalesOrderDetail

select top 10 
productid, 
SUM(linetotal) as 'Valor Total'
from Sales.SalesOrderDetail
group by ProductID
order by SUM(linetotal) desc

select top 10 Productid, 
sum(linetotal) as "Soma Total"
from Sales.SalesOrderDetail
group by productid
order by sum(linetotal) desc

select * from 
Sales.SalesOrderDetail

select * from 
Sales.SalesOrderHeader

select 
ss.salesorderid, 
ss.unitprice, 
ss.linetotal,
so.orderdate
from Sales.SalesOrderDetail as ss 
inner join Sales.SalesOrderHeader as so ON
ss.SalesOrderID = 
so.SalesOrderID

select * from
Sales.SalesOrderDetail

select top 10
ProductID,
AVG(unitprice) as 'Média Unitário',
SUM(linetotal) as 'Valor Total'
FROM Sales.SalesOrderDetail
group by ProductID

/*4 - Eu preciso saber quantos produtos e qual quantidade média de produtos temos 
cadastrados nas nossas ordens de serviço
> usar a tabela production.workorder
> usar group by e uma função de agragação
*/

select * from 
Production.WorkOrder

select 
productid,
AVG(orderqty) as 'Média'
from Production.WorkOrder
group by ProductID


 select firstname, 
 count(FirstName) as "Quantidade"
 from Person.Person
 group by firstname
 having count(firstname) > 10 

-- Prática LEFT JOIN --

select * from 
Sales.PersonCreditCard

select * from 
Person.Person

select * from 
Person.Person as pp
inner join Sales.PersonCreditCard as pc on
pp.BusinessEntityID = 
pc.BusinessEntityID

select top 10 * from 
Person.Person as pp
left join  Sales.PersonCreditCard as pc ON
pp.BusinessEntityID = 
pc.BusinessEntityID
where pc.BusinessEntityID is NULL

-- UNION | VARIAÇÕES --
-- Operador union combina dois ou mais resultados de um select em um resultado apenas --

select * from 
Person.Person

select 
firstname, 
title, 
middlename
from Person.Person
where title = 'MR.'

select 
firstname, 
title, 
middlename
from Person.Person
where middlename = 'A'

select 
firstname as 'Nome', 
title as 'Título',
middlename as 'Sobrenome'
from Person.Person
UNION
select 
firstname as 'Nome', 
title as 'Título', 
middlename as 'Sobrenome'
from Person.Person

select * from 
Sales.SalesOrderDetail

select top 10
productid,
OrderQty, 
UnitPrice,
LineTotal
from sales.salesorderdetail
    where LineTotal >= 86.000000
UNION
select top 10
    productid, 
    orderqty, 
    unitprice, 
    linetotal
    from Sales.SalesOrderDetail
        where LineTotal <= 86.000000