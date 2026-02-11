--FA_FORMAT

% Diferença Total R$ = FORMAT(
    [LM total R$],
    " ▲ + 0.0% vs mês anterior ;
      ▼ - 0.0% vs mês anterior")
-----------------------------------------------------------------------------------------
--FA

LM total R$ = 
VAR vMesAtual = [Total R$]

VAR vMesAnterior = CALCULATE(
    [Total R$],
    PREVIOUSMONTH(dCalendario[Data])
)
VAR vPorcentagem = DIVIDE(
    vMesAtual - 
    vMesAnterior, vMesAnterior,
    0)

    RETURN
    vPorcentagem
-----------------------------------------------------------------------------------------
--FORMAT_DINAMICO

VAR vValor = [$ Faturamento]

RETURN
"""" &
SWITCH(
    TRUE(),
    vValor >= 1000000000, FORMAT(vValor, "#,,,. Bi"),
    vValor >= 1000000, FORMAT(vValor, "#,,. 0 Mi"),
    vValor >= 1000, FORMAT(vValor, "#,. K"),
    FORMAT(vValor, "R$ #")
)
&""""
-----------------------------------------------------------------------------------------
--SOMA_SE

Medida = 
var Vme = CALCULATE(MAX(Base_Suprema[Volume]),
Base_Suprema[Mercado]  = "mi" || Base_Suprema[Indicador] = "saída planejada")
-----------------------------------------------------------------------------------------
--SOMA_SE

VAR Vmi =  CALCULATE(MAX(Base_Suprema[Volume]),
Base_Suprema[Mercado]  = "me" || Base_Suprema[Indicador] = "saída planejada")
VAR vresult = vme + Vmi
RETURN vresult
-----------------------------------------------------------------------------------------
--ACUMULADO

Acumulado entrada realizada = CALCULATE(
    [Entrada Realizada],
    DATESMTD(
       dCalendario[Data]
    ))
-----------------------------------------------------------------------------------------
--ACUMULADO

	Média Acumulada Vendas = 
VAR MediaAcumulada =
    CALCULATE (
        AVERAGEX (
            FILTER (
                ALLSELECTED ( Faturamento[Data] ),
                Faturamento[Data] <= MAX ( Faturamento[Data] )
            ),
            Faturamento[Vendas]
        )
    )
RETURN
    MediaAcumulada
-----------------------------------------------------------------------------------------
--ACUMULADO

 Total Acumulado Entrada Realizada = 
CALCULATE(
	[Entrada Realizada],
	FILTER(
		CALCULATETABLE(
			SUMMARIZE('dCalendario', 'dCalendario'[AnoMesINT], 'dCalendario'[Data]),
			ALLSELECTED('dCalendario')
		),
		ISONORAFTER(
			'dCalendario'[AnoMesINT], MAX('dCalendario'[AnoMesINT]), DESC,
			'dCalendario'[Data], MAX('dCalendario'[Data]), DESC
		)
	)
)
-----------------------------------------------------------------------------------------
--LINGUAGEM_M_DATE

#datetime(1970,1,1,0,0,0) + #duration(0,0,0, Number.From([timestamp])))
-----------------------------------------------------------------------------------------
--LINGUAGEM_M_DATE

(Date.StartOfWeek([Data])-Date.StartOfWeek(DateTime.Date(DateTime.LocalNow())))/7
-----------------------------------------------------------------------------------------