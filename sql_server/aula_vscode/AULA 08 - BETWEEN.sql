-- AULA 08 - Between --

/*O Between é usado para encontrar valor entre um valor minímo e valor máximo
'valor' between mínimo and máximo
'valor >= mínimo and valor <= máximo;
*/

select *
from Production.Product
where listprice between 100 and 1500;

select * 
from Production.Product
where listprice not between
100 and 1500;

select * from 
HumanResources.Employee

select * from 
HumanResources.Employee
where HireDate 
between '2009/01/01 and 2010/01/01'
order by HireDate