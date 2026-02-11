-- AULA 23 - SUBQUERY

-- Monte um relatório para mim de todos os porodutos 
-- cadastrados que tem preço de venda acima da média

select * from 
Production.Product

-- Maneira não funcional de aplicar o problema em questão

select 
AVG(listprice) as 'Média'
from 
Production.Product

select * from 
Production.Product
where ListPrice > 438.66

-- Maneira usual para solução do problema

select * from 
Production.Product
where ListPrice > (select avg(ListPrice) 
from Production.Product)

-- Eu quero saber o nome dos meus funcionários que tenham
-- o cargo de 'Design Enginner'

select * from 
Person.Person

select * from 
HumanResources.Employee

select
firstname
from Person.Person
where BusinessEntityID IN
(select BusinessEntityID
from HumanResources.Employee
where JobTitle = 'design engineer')

select 
firstname as 'Nome',
lastname as 'Sobrenome',
additionalcontactinfo as 'Adional'
from Person.Person
where BusinessEntityID in 
(select BusinessEntityID 
from HumanResources.Employee
where JobTitle = '-design engineer')

-- Variação com JOIN 

select * from 
Person.Person

select * from 
HumanResources.Employee

select 
p.firstname
from Person.Person as p
inner join HumanResources.Employee as e 
on p.BusinessEntityID = 
e.BusinessEntityID 
and
e.JobTitle = 'design engineer'

-- Encontre todos os endereços que estão no estado de 'Alberta'
-- pode trazer todas as informações 
-- usar person.address e person.stateprovince

select * from 
Person.Address

select * from 
Person.StateProvince

select *
from Person.Address
where StateProvinceID IN
(select StateProvinceID
from Person.StateProvince
where name = 'alberta')

