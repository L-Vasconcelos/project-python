-- AULA 14 - HAVING -- 

 /*O having é basicamente muito usado em juñção com o gourp by para filtrar
 resultados de um agrupamento
 De formo mais simples, um where para dados agrupados
 Difereça entre os dois é que o group by é aplicado depois que os dados já foram agrupados,
 enquanto o where é aplicado antes dos dados serem agrupados.
 */

 select firstname, 
 count(FirstName) as "Quantidade"
 from Person.Person
 group by firstname
 having count(firstname) > 10

 select productid, 
 sum(linetotal) as "total"
 from sales.SalesOrderDetail
 group by productid
 having sum(linetotal)
 between 162000 and 500000

select firstname, 
count(firstname) as "Quantidade"
from person	.person 
where title = 'mr.'
group by firstname 
having count(firstname) > 10

/*1 - Estamos querendo identificar as provincias(stateprovinceid) com o maior numero
de cadastros no nosso sistema, então é preciso encontrar quais províncias 
stateprovinceid) esstão regisdtrados no banco de dados mais que 1000 vezes 
> tabela person.address
> usar havinf, count, e operadores matemáticos
*/

select * from 
person.Address

select StateProvinceID, 
count(stateprovinceid) as "Quantidade"
from person.address
group by stateprovinceid 
having count (stateprovinceid) > 1000

select postalcode, 
count(postalcode) as "Quantidade"
from person.address
group by PostalCode
having count (PostalCode) >100

/*2- Sendo que se trata de uma multinacional, os gerentes querem saber quais prdutos (produtcid)
não estão trazendo em média no mínimo 1 milhão em total de vendas (linetotal)
> Tabela sales.salesorderdetaial
> usar having, count, e operradores matemáticos
*/

select * from 
Sales.SalesOrderDetail

select productid, 
avg (linetotal)
from Sales.SalesOrderDetail
group by productid
having avg(linetotal) < 100000