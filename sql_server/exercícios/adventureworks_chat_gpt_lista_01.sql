-- Exercício: Liste todos os produtos disponíveis no inventário, mostrando o nome e a quantidade em estoque.

select * from Production.Product;
select * from Production.ProductInventory;

select 
pp.name, 
pi.quantity
from Production.Product as pp
left join Production.ProductInventory as pi on
pp.ProductID = pi.ProductID 
order by name asc;

-- Exercício: Encontre todos os clientes que residem na cidade de "Seattle".

select * from Person.Person;
select * from Person.Address;
select * from Person.BusinessEntityAddress;

select 
pp.firstname, 
pp.lastname,
pa.city
from Person.Person as pp 
left join Person.BusinessEntityAddress as pe on
pp.BusinessEntityID = pe.BusinessEntityID
left join Person.Address as pa on
pa.AddressID = pe.AddressID
where City = 'seattle';

-- Exercício: Calcule o total de vendas por cada vendedor.

select * from Sales.SalesOrderHeader;

select 
salesorderid as id_venda, 
sum(totaldue) as total_venda
from Sales.SalesOrderHeader
group by SalesOrderID;

-- Exercício: Liste os pedidos e os respectivos clientes que os realizaram.

