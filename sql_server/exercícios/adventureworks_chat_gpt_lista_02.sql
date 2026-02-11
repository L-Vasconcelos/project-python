-- Instrução: Selecione os primeiros 10 funcionários na tabela HumanResources.Employee, incluindo BusinessEntityID, JobTitle, HireDate.

select * from HumanResources.Employee;

select top 10 
businessentityid as 'id_colaborador',
jobtitle as 'cargo',
HireDate as 'data'
from HumanResources.Employee

-- Instrução: Selecione os primeiros 10 nomes de funcionários usando as colunas FirstName, LastName e concatene os valores.

select * from Person.Person;

select top 10 
firstname + ' ' + lastname as 'nome_completo'
from Person.Person;

-- Instrução: Selecione ProductID, Name, ListPrice na tabela Production.Product e filtre produtos com preço maior que 1000.

select * from Production.Product;

select 
productid,
name, 
listprice
from Production.Product
where listprice >= 1000;

-- Instrução: Selecione CustomerID, FirstName, LastName, CountryRegionCode da tabela Person.Person e filtre por clientes cujo país seja 'BR'.

select * from Person.Person;

select 
businessentityid,
persontype,
firstname + ' ' + lastname as 'full_name'
from Person.Person
where PersonType = 'IN';

-- Instrução: Usando JobTitle, conte quantos funcionários existem em cada cargo na tabela HumanResources.Employee.

select * from HumanResources.Employee;

select 
jobtitle,
count (JobTitle) as num_employess
from HumanResources.Employee
group by JobTitle order by JobTitle asc;

-- Instrução: Na tabela Production.Product, agrupe por ProductCategoryID e calcule o preço médio (ListPrice).

select * from Production.Product;

select
ProductSubcategoryID,
avg (listprice) as 'média'
from Production.Product
group by ProductSubcategoryID
order by média desc;

-- Instrução: Realize uma junção entre Production.Product e Production.ProductCategory para listar ProductID, Name do produto e Name da categoria.

select * from Production.Product;
select * from Production.ProductCategory;
select * from Production.ProductSubcategory;



