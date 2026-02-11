--PARETO_ACUMULADO

t_acumulado = 
var v1 = [Faturamento]

var v2 = SUMMARIZE(
    ALLSELECTED('fMovimentação'),
    dProduto[Sub Grupo],
    "@faturamento", [Faturamento])
    
var v3 = IF([Faturamento] > 0,
SUMX(FILTER(v2, [@faturamento] >= v1), [Faturamento]
))

return v3
-----------------------------------------------------------------------------------------
--PARETO_ACUMULADO

fat_acumulado_% = 
var v1 = [Faturamento]
var fat_total = CALCULATE([Faturamento], 
ALLSELECTED(dProduto[Sub Grupo]))

var v2 = SUMMARIZE(
    ALLSELECTED('fMovimentação'),
   'dProduto'[Sub Grupo],
    "@faturamento", [Faturamento])

var v3 = IF([Faturamento] > 0,
SUMX(FILTER(v2, [@faturamento] >= v1), [Faturamento]
))

return 
DIVIDE(v3, fat_total, 0)
-----------------------------------------------------------------------------------------
--FAT_PRODUTO_08

faturamento produtos 80% = 
SUMX(
    FILTER(
    VALUES(dProduto[Sub Grupo]),
    [fat_acumulado_%] <= 0.8),
    [Faturamento])
-----------------------------------------------------------------------------------------
--QTD_PRODUTO_08

qtd_pareto acima de 80% = 
var v1 = COUNTROWS(
    FILTER(
        VALUES(dProduto[Sub Grupo]),
        [fat_acumulado_%] >= 0.8)
)

return v1
-----------------------------------------------------------------------------------------
--SUB_TITULO

sub titulo pareto = 
[qtd_pareto acima de 80%] & " Sub Grupos representam 80% do Faturamento no total de 
" & FORMAT([faturamento produtos 80%], " R$ #,#00.00 ")