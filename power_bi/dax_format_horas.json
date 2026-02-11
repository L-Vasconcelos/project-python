--TEMPO_MEDIO_DECIMAL

tempo_medio_decimal =
var v1 = AVERAGEX(
    carregamento, 
    DATEDIFF(carregamento[ENTRADA DATA], carregamento[SAIDA DATA], HOUR))
return v1
-----------------------------------------------------------------------------------------
--TEMPO_MEDIO_FORMAT

tempo_total_fabrica_hh_mm = 
var v1 = SUMX(
    carregamento, 
    DATEDIFF(carregamento[ENTRADA DATA], carregamento[SAIDA DATA], HOUR)
)
var v2 = 
    INT(v1) & "h " & 
    INT((v1 - INT(v1)) * 60) & "m " & 
    ROUND(((v1 - INT(v1)) * 60 - INT((v1 - INT( v1)) * 60)) * 60, 0) & "s"

return v2
-----------------------------------------------------------------------------------------
HorasDecimais dif emissao = 
HOUR([DIF EMISSÃO]) + MINUTE([DIF EMISSÃO]) / 60 + SECOND([DIF EMISSÃO]) / 3600
