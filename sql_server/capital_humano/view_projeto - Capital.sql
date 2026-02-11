-- vw_ficha_colaborador_01
select 
r34.codccu,
r34.codcar,
r34.numemp,
r34.tipcol,
r34.numcad,
r34.nomfun,
r34.datadm,
r34.datccu,
r34.datsal,
r34.sitafa as "tipsit",
r34.tipsex,
r34.valsal,
r34.codban,
r18.nomccu
from capital.VW_R034FUN_meridional as r34
inner join capital.VW_R018CCU_meridional as r18 on
r34.codccu = r18.CodCcu;

-- vw_ficha_colaborador_02
select
r34.codccu,
r34.codcar,
r34.numemp,
r34.tipcol,
r34.numcad,
r34.nomfun,
r34.datadm,
r34.sitafa as "tipsit",
r34.tipsex,
r34.valsal,
r34.codban,
r18.nomccu,
r024.titred
from capital.VW_R034FUN_meridional as r34
inner join capital.VW_R018CCU_meridional as r18 on
r34.codccu = r18.CodCcu
inner join capital.VW_R024CAR_meridional as r024 on
r34.codcar = r024.CodCar;

-- vw_lista_colaborador
select 
numcad,
sitafa,
nomfun,
datadm
from capital.VW_R034FUN_meridional;

-- vw_situacao
select
codsit,
dessit,
tipsit
from capital.VW_R010SIT_meridional;

-- vw_setores
select 
numemp,
codccu,
nomccu
from capital.VW_R018CCU_meridional;

-- vw_descricao_hora_extra
select 
r08.TabEve,
r08.tipsom,
r08.CodTot, --verificar 11/09
r08.DesTot, 
r14.NumCad,
r14.MesAno,
r14.tipprv,
r14.tipval,
r14.PrvMes
from capital.VW_R008TOT_meridional as r08
inner join capital.VW_R146PRV_meridional as r14 on
r08.TabEve = r14.TipPrv;

-- vw_cargo
select
r38.numcad,
r38.codcar,
r38.DatAlt,
r24.titred
from capital.VW_R038HCA_meridional as r38
inner join capital.VW_R024CAR_meridional as r24 on
r38.CodCar = r24.CodCar;
