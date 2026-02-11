select * from Person.Person;
select * from Person.Password;
select * from Person.EmailAddress;
select * from Sales.SalesPerson;


select distinct 
businessentityid,
firstname + ' ' + lastname as 'FullName'
from Person.Person
order by BusinessEntityID asc;

select
pp.BusinessEntityID,
pp.firstname + ' ' + lastname as 'FullName',
ps.PasswordHash,
ps.PasswordHash,
pa.EmailAddress,
sp.territoryid,
sp.commissionpct,
sp.salesytd,
sp.saleslastyear,
sp.modifieddate
from Person.Person as pp
left join Person.Password as ps on
pp.BusinessEntityID = ps.BusinessEntityID
left join Person.EmailAddress as pa on
pa.BusinessEntityID = pp.BusinessEntityID
left join Sales.SalesPerson as sp on
sp.BusinessEntityID = pp.BusinessEntityID
order by BusinessEntityID asc;

/*select distinct
businessentityid,
territoryid,
modifieddate,
commissionpct,
salesytd,
saleslastyear
from Sales.SalesPerson
order by BusinessEntityID asc;
*/

select * from Sales.SalesOrderDetail
select * from Sales.SalesTerritory
