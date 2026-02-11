select * from 
Person.Person

select * from 
Person.Person
where LastName = 'miller' AND
FirstName = 'anna'

select * from 
Production.Product

select * from Production.Product
where color = 'blue' or color = 'black'

select * from Production.Product
where ListPrice > 1500 and ListPrice < 5000

select * from Production.Product
where color <> 'red'

select * from 
Production.Product

-- exercicio 
select * from Production.Product
where Weight > 500 and Weight < = 700

select * from HumanResources.Employee
where MaritalStatus = 'm' and SalariedFlag = '1'

select * from Person.Person
select * from Person.EmailAddress

select 
pp.BusinessEntityID,
pp.firstname,
pp.lastname,
pe.emailaddress
from Person.Person as pp
left join Person.EmailAddress as pe on
pp.BusinessEntityID = pe.BusinessEntityID
where FirstName = 'peter' and LastName = 'krebs'

select count (*) as contagem
 from Person.Person

 select count(distinct Title) 
 as "contagem"
 from Person.Person

 --exercicio

select * from Production.Product

select count(*) as "contagem"
from Production.Product

select count (size) as "contagem"
from Production.Product

select count (distinct size) as "contagem"
from Production.Product

select * from Person.Person
ORDER BY FirstName ASC

select * from Person.Person
ORDER BY FirstName DESC

select 
firstname, 
lastname
from Person.Person
ORDER BY FirstName ASC,
lastname DESC

--exercicio 

select * from Production.Product

select top 10 ProductID 
from Production.Product
ORDEr BY ListPrice DESC

select top 4 
name,
productnumber 
from Production.Product
ORDER BY ProductID ASC

select * from Production.Product
where ListPrice BETWEEN 1000 and 1500

select * from Production.Product
where ListPrice not BETWEEN 1000 and 1500

select * from HumanResources.Employee

select * FROM HumanResources.Employee
where HireDate 
BETWEEN '2009/01/01' and '2010/01/01'
ORDER BY HireDate ASC

select * from Person.Person

select * from Person.Person
where BusinessEntityID in (2,7,13)

select * from Person.Person
where not BusinessEntityID in (2,7,13)

select * from Production.Product

select  count(listprice) as "contagem"
from Production.Product
where ListPrice >= 1500

select * from Person.Person

select count(lastname) as "contagem"
from Person.Person
where LastName like 'p%'

select * from Person.Address

select count (distinct city) as "contagem"
from Person.Address

select COUNT (distinct city) as "contagem"
from Person.Address
