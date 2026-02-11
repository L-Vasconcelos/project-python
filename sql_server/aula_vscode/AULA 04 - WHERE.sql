
-- AULA 04 - WHERE --

SELECT * 
FROM person.Person
WHERE LastName = 'miller'

SELECT *
FROM person.Person
WHERE lastname = 'miller' AND firstname = 'anna'

SELECT *
FROM Production.Product
WHERE color = 'blue' OR color = 'black'

SELECT *
FROM production.Product
WHERE listprice > 1500

SELECT *
FROM production.Product
WHERE listprice > 1500 AND ListPrice < 5000

SELECT *
FROM production.Product
WHERE color <> 'red'

/* A equipe de produção de produtos precisa do nome de todas as peças que pesam mais que 500kg, 
mas não mais de 700kg para inspeção 
-- weight
*/

SELECT name 
FROM production.Product
WHERE Weight > 500 AND weight < 700

-- Desafio 2 
Foi pedido pelo mkt uma relação de todos os empregados (employees) que são casados 
(single = solteiro, married = casado) e são assalariados (salaried)
*/

SELECT*
FROM HumanResources.Employee
WHERE MaritalStatus = 'm' AND SalariedFlag = 1 

-- Desafio 3
Um usuário chamado Peter Krebs está devendo um pagamento, consiga o e-mail dele para que
possamos enviar uma cobrança!
(usar a tabela person.person e depois a tabela person.emailaddress)
*/

SELECT *
FROM person.Person 
WHERE firstname = 'peter' AND lastname = 'krebs'


select * from 
person.EmailAddress
where BusinessEntityID = 26