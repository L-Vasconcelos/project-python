Eixo Dinamico = 
VAR vTabela = ALLSELECTED(dCalendario[MesAbre])
VAR vMaiorValor = MAXX(vTabela,[$ Faturamento])
VAR vDeslocamento = 1.4
RETURN
vMaiorValor * vDeslocamento
-----------------------------------------------------------------------
Eixo Dinamico new = 
VAR vTbela = ALLSELECTED(dCalendario[Data])
VAR vMaior_valor_atual = MAXX('fMovimentação', [# Projeção Dia])
VAR vMaior_valor_anterior = MAXX('fMovimentação', [$ Faturamento])
VAR vCheck = MAX(vMaior_valor_atual, vMaior_valor_anterior)
RETURN vCheck *1.4