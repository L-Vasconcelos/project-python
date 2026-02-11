select * from 
Boletim


---------------------------------------------------------------

create or alter view vw_dProduto as 
select distinct
[Id Produto], 
produto,
grupo,
[Sub Grupo] 
from Boletim
go

--------------------------------------------------------------

select * from 
vw_dProduto

---------------------------------------------------------------

create or alter view vw_dCliente as 
select
cliente
from Boletim
go

---------------------------------------------------------------

select * from 
vw_dCliente


