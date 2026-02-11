-- AULA 21 - STRING

select * from 
Person.Person

select 
firstname, 
substring (firstname,1,3)
from Person.Person

select 
CONCAT(firstname,' - ', lastname) as Nome
from Person.Person

select * from 
Production.Product

select 
productnumber, 
REPLACE(productnumber, '-', '#')
from Production.Product


