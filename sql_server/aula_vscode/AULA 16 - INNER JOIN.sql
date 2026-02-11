-- AULA16 - INNER JOIN + VARIAÇÕES --

/*Existem 3 tipos gerais de joins:
inner join, outer join e self join
*/

select top 10 *
from person.person 

select top 10 *
from Person.EmailAddress

select 
p.businessentityid, 
p.firstname,
p.lastname, 
pe.EmailAddress
from 
Person.Person as P
inner join Person.EmailAddress PE on
p.BusinessEntityID = pe.BusinessEntityID

select 
pr.listprice, 
pr.name, 
pc.name
from Production.Product pr
inner join Production.ProductSubcategory pc on
pc.ProductCategoryID = 
pr.ProductSubcategoryID

select top 10 * 
from person.person

select top 10 * 
from person.person

select top 10 * 
from Person.EmailAddress

select pr.listprice, 
pr.name, 
pc.name 
from Production.Product pr
inner join Production.ProductSubcategory pc on pc.ProductSubcategoryID = 
pr.ProductSubcategoryID


select * from 
person.PhoneNumberType

select * from 
person.PersonPhone

select
pp.businessentityid, 
pt.name, 
pt.phonenumbertypeid, 
pp.phonenumber
from Person.PersonPhone pp
inner join person.PhoneNumberType pt on
pt.PhoneNumberTypeID = pp.PhoneNumberTypeID

-- businessentityid, name, phonenumbertypeid, phonenumber --

select * from
person.PhoneNumberType

select * from 
Person.PersonPhone

select 
pb.businessentityid, 
pt.name, 
pt.phonenumbertypeid,
pb.phonenumber
from Person.PersonPhone pb
inner join Person.Phoneselce
pb.PhoneNumberTypeID


-- addressid,city, stateprovinceid, namestate --

select * from 
Person.StateProvince

select * from 
Person.Address

select 
pa.addressid, 
pa.city, 
ps.stateprovinceid,
ps.countryregioncode
from Person.Address pa
inner join Person.StateProvince ps on
ps.StateProvinceID = 
pa.StateProvinceID

select * 
from Person.Person

select *
from Person.EmailAddress

-- bussinessentityid, firstname, lastname, emailaddress --

select 
pp.businessentityid, 
pp.firstname, 
pp.lastname, 
pe.emailaddress
from Person.Person as pp 
inner join  Person.EmailAddress pe on
pp.BusinessEntityID = 
pe.BusinessEntityID


select 
pp.businessentityid, 
pp.firstname, 
pp.emailpromotion, 
pe.emailaddress, 
pe.modifieddate
from Person.person as pp
inner join Person.EmailAddress as pe on
pp.BusinessEntityID =
pe.BusinessEntityID


-- listprice, nome do produto, nome da subcategoria --

select * 
from Production.Product

select * 
from Production.ProductCategory

select 
pp.listprice, 
pp.name,
pc.name
from Production.Product as pp
inner join Production.ProductCategory as pc on
pp.ProductSubcategoryID = 
pc.ProductCategoryID

select *
from person.address

-- addressid, city, stateprovinceid, namestate --

select 
pa.addressid, 
pa.city, 
ps.stateprovinceid, 
ps.name
from Person.StateProvince as ps
inner join Person.Address as pa on
ps.StateProvinceID = 
pa.StateProvinceID