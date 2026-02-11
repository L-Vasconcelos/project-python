select numemp, tipcol, numcad, nomfun from capital.	VW_R034FUN_MERIDIONAL as "nome funcionario";

select * from capital.	VW_R010SIT_MERIDIONAL; --ok
select * from capital.	VW_R034FUN_MERIDIONAL as "tabela fato" order by nomfun asc; --ok
select * from capital.	VW_R026FPV_MERIDIONAL as "Salario";
select top 5 * from capital.	VW_R018CCU_MERIDIONAL as "setores"; --ok
select top 5 * from capital.	VW_R008TOT_MERIDIONAL as "descrição_horas";--ok
select * from capital.	VW_R030FIL_MERIDIONAL as "filial";
select * from capital.	VW_R146PRV_MERIDIONAL as "valores" order by NumCad asc;--ok
select * from capital.	VW_R046VER_MERIDIONAL; --verificar
select * from capital.	VW_R066SIT_MERIDIONAL; --verificar
select * from capital.VW_R024CAR_MERIDIONAL as "cargos";--ok



select 
r34.codccu,
r34.numemp,
r34.tipcol,
r34.numcad,
r34.nomfun,
r34.datadm,
r34.tipsex,
r34.valsal,
r34.codban,
r18.nomccu
from capital.VW_R034FUN_meridional as r34
inner join capital.VW_R018CCU_meridional as r18 on
r34.codccu = r18.CodCcu
order by nomfun asc;


-------------------------------------------------------------------------------

select * from capital.	VW_R008TOT_MERIDIONAL as "descrição_horas";
select * from capital.	VW_R146PRV_MERIDIONAL as "valores" order by NumCad asc;
select top 5 * from capital.	VW_R034FUN_MERIDIONAL as "nome funcionario";

select top 50
r08.TabEve,
r08.tipsom,
r08.DesTot, 
r14.NumCad,
r14.MesAno,
r14.tipprv,
r14.tipval,
r14.PrvMes
from capital.VW_R008TOT_meridional as r08
inner join capital.VW_R146PRV_meridional as r14 on
r08.TabEve = r14.TipPrv
order by MesAno asc;