select * from 
BaseEqmbarque

select
cliente,replace (Cliente, ' -',''), SUBSTRING(Cliente,1,6)
from BaseEqmbarque


---------------------------------------------------------------

create or alter view vw_dCliente as 
select distinct
cliente
from 
BaseEqmbarque
go

---------------------------------------------------------------

create or alter view vw_dMunicipio as 
select distinct
municipio
from 
BaseEqmbarque
go

---------------------------------------------------------------

create or alter view vw_dProduto as 
select distinct
produto
from 
BaseEqmbarque
go

---------------------------------------------------------------

create or alter view vw_dVendedor as 
select distinct
vendedor 
from 
BaseEqmbarque
go

---------------------------------------------------------------

create or alter view vw_fVendas as 
select
Mês, 
semana, 
[Data Mov],
nf,
cliente,
Municipio,
produto, 
Quant#kg,
[Valor Unitario],
[Vendedor ]
from BaseEqmbarque
go

