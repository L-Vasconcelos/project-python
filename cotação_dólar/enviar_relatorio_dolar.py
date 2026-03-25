"""
enviar_relatorio_dolar.py
Dashboard Streamlit — Fechamento PTAX (Dólar e Euro)
Versão: 2.0 — Corrigido e otimizado
"""

import streamlit as st
import pandas as pd
import pyodbc
import plotly.graph_objects as go
import holidays
from datetime import datetime
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Relatório Fechamento Câmbio", layout="wide")

# --- CSS: FORMATAÇÃO DE IMPRESSÃO ---
st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 0rem; padding-left: 2rem; padding-right: 2rem; }
    h1 { font-size: 2.5rem !important; text-align: center; }
    h2 { font-size: 2.0rem !important; color: #1f77b4; margin-bottom: 0px;}
    h3 { font-size: 1.8rem !important; }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; }
    [data-testid="stMetricLabel"] { font-size: 1.2rem !important; }
    [data-testid="stMetricDelta"] { font-size: 1.1rem !important; }
    div[data-testid="stDataFrame"] table { width: 100%; }
    div[data-testid="stTable"] td, div[data-testid="stTable"] th,
    div[data-testid="stDataFrame"] td, div[data-testid="stDataFrame"] th {
        font-size: 1.2rem !important;
        padding: 10px !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# CONEXÃO COM BANCO DE DADOS
# ---------------------------------------------------------------------------

def carregar_dados(nome_tabela: str) -> pd.DataFrame | None:
    """
    Carrega dados do SQL Server filtrando pelo ano corrente.

    CORREÇÃO #1: Query alterada de TOP 60 para filtro por ano,
    garantindo que a média anual reflita o ano completo e não apenas
    os últimos ~3 meses úteis.

    CORREÇÃO #2: Adicionado retry automático (2 tentativas) antes de
    falhar, absorvendo instabilidades de rede sem travar o dashboard.
    """
    dados_conexao = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=CORPORATIVOMTCS;"
        "Database=Financeiro;"
        "Trusted_Connection=yes;"
    )

    ano_atual = datetime.now().year

    # Filtra pelo ano atual — garante média anual real
    query = f"""
        SELECT DataCotacao, ValorCompra, ValorVenda
        FROM {nome_tabela}
        WHERE YEAR(DataCotacao) = {ano_atual}
        ORDER BY DataCotacao ASC
    """

    ultimo_erro = None
    for tentativa in range(1, 3):  # 2 tentativas
        try:
            conn = pyodbc.connect(dados_conexao, timeout=15)
            df = pd.read_sql(query, conn)
            conn.close()

            if df.empty:
                st.error(f"❌ TABELA VAZIA: {nome_tabela} não retornou registros para {ano_atual}.")
                return None

            df['DataCotacao'] = pd.to_datetime(df['DataCotacao'])
            return df

        except Exception as e:
            ultimo_erro = e
            if tentativa < 2:
                time.sleep(5)  # aguarda antes de retentar

    # Ambas as tentativas falharam
    st.error(f"❌ ERRO CRÍTICO DE CONEXÃO ({nome_tabela}) após 2 tentativas: {ultimo_erro}")
    return None


# ---------------------------------------------------------------------------
# UTILITÁRIOS
# ---------------------------------------------------------------------------

def estilo_variacao(val):
    if pd.isna(val):
        return 'color: white'
    color = '#4CAF50' if val > 0 else '#FF4B4B' if val < 0 else 'white'
    return f'color: {color}; font-weight: bold'


def calcular_dias_uteis_desde(data_ref: pd.Timestamp) -> int:
    """
    CORREÇÃO #3: Calcula dias úteis reais entre data_ref e hoje,
    substituindo a comparação por dias corridos que gerava falsos positivos
    em feriados prolongados e fins de semana estendidos.
    """
    hoje = pd.Timestamp(datetime.now().date())
    if data_ref >= hoje:
        return 0
    # bdate_range conta apenas dias úteis (seg-sex), excluindo fins de semana
    # Feriados nacionais não são excluídos nativamente — tolerância de 1 dia extra
    dias = len(pd.bdate_range(start=data_ref + pd.Timedelta(days=1), end=hoje))
    return dias


# ---------------------------------------------------------------------------
# GERAÇÃO DO PAINEL POR MOEDA
# ---------------------------------------------------------------------------

def gerar_painel_moeda(df_raw: pd.DataFrame, nome_moeda: str, icone: str) -> bool:
    """
    Gera o painel visual completo para a moeda especificada.

    Retorna True se o painel foi gerado com sucesso, False caso contrário.
    O valor de retorno é usado pelo robô (Selenium) para validar se o
    envio do e-mail deve prosseguir.
    """

    if df_raw is None or df_raw.empty:
        st.error(f"❌ DADOS NÃO LOCALIZADOS: {nome_moeda}")
        return False

    # --- FILTRO: Dias úteis e feriados brasileiros ---
    df_clean = df_raw[df_raw['DataCotacao'].dt.dayofweek < 5].copy()
    feriados_br = holidays.BR()
    mask_feriados = ~df_clean['DataCotacao'].apply(lambda x: x in feriados_br)
    df_clean = df_clean[mask_feriados].reset_index(drop=True)

    if len(df_clean) < 2:
        st.error(f"❌ DADOS INSUFICIENTES: {nome_moeda} possui menos de 2 dias úteis válidos.")
        return False

    reg_ultimo    = df_clean.iloc[-1]
    reg_penultimo = df_clean.iloc[-2]
    data_ref      = reg_ultimo['DataCotacao']

    # -------------------------------------------------------------------
    # CORREÇÃO #3 — Validação de recência usando dias úteis reais
    # Se dado tiver mais de 2 dias úteis de atraso, BLOQUEIA o envio
    # -------------------------------------------------------------------
    dias_defasagem = calcular_dias_uteis_desde(data_ref)
    if dias_defasagem > 2:
        st.error(
            f"🚨 DADO DESATUALIZADO — {nome_moeda}: "
            f"último registro é {data_ref.strftime('%d/%m/%Y')} "
            f"({dias_defasagem} dias úteis atrás). "
            f"Envio BLOQUEADO para evitar informação incorreta."
        )
        return False  # impede o envio pelo robô

    # --- MÉTRICAS PRINCIPAIS ---
    venda_atual    = reg_ultimo['ValorVenda']
    venda_anterior = reg_penultimo['ValorVenda']
    delta_venda    = ((venda_atual - venda_anterior) / venda_anterior) * 100

    compra_atual    = reg_ultimo['ValorCompra']
    compra_anterior = reg_penultimo['ValorCompra']
    delta_compra    = ((compra_atual - compra_anterior) / compra_anterior) * 100

    # --- ESTATÍSTICAS DO ANO (baseadas no filtro por ano do SQL) ---
    media_ano_compra = df_clean['ValorCompra'].mean()
    media_ano_venda  = df_clean['ValorVenda'].mean()
    max_ano          = df_clean['ValorVenda'].max()
    min_ano          = df_clean['ValorVenda'].min()

    # --- PREPARAÇÃO DA TABELA (últimos 10 dias úteis) ---
    df_recorte = df_clean.iloc[-11:].copy()
    df_recorte['DataStr']  = df_recorte['DataCotacao'].dt.strftime('%d/%m')
    df_recorte['MediaDia'] = (df_recorte['ValorCompra'] + df_recorte['ValorVenda']) / 2

    df_tabela = df_recorte.sort_values(by='DataCotacao', ascending=False).copy()
    df_tabela['Variação (%)'] = df_tabela['ValorVenda'].pct_change(-1) * 100
    df_tabela_final = df_tabela.head(10)

    df_view = df_tabela_final[['DataCotacao', 'MediaDia', 'ValorCompra', 'ValorVenda', 'Variação (%)']].copy()
    df_view.rename(columns={'MediaDia': 'Média (C/V)'}, inplace=True)
    df_view['DataCotacao'] = df_view['DataCotacao'].dt.strftime('%d/%m/%Y')

    styler_tabela = (
        df_view.style
        .map(estilo_variacao, subset=['Variação (%)'])
        .map(lambda _: 'color: #FFD700; font-weight: bold', subset=['Média (C/V)'])
        .format({
            'ValorCompra':  'R$ {:.4f}',
            'ValorVenda':   'R$ {:.4f}',
            'Média (C/V)':  'R$ {:.4f}',
            'Variação (%)': '{:+.2f}%'
        })
    )

    # --- GRÁFICO ---
    df_grafico = df_recorte.iloc[1:].copy()
    media_periodo_constante = df_grafico['MediaDia'].mean()

    # --- RENDERIZAÇÃO ---
    st.markdown(
        f"<h2>{icone} Fechamento {nome_moeda} (PTAX) — {data_ref.strftime('%d/%m/%Y')}</h2>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Fechamento (Compra)", f"R$ {compra_atual:.4f}", f"{delta_compra:.2f}%")
    col2.metric("Fechamento (Venda)",  f"R$ {venda_atual:.4f}",  f"{delta_venda:.2f}%")
    col3.metric("Média Compra (Ano)",  f"R$ {media_ano_compra:.4f}")
    col4.metric("Média Venda (Ano)",   f"R$ {media_ano_venda:.4f}")
    col5.metric("Máxima Ano",          f"R$ {max_ano:.4f}")
    col6.metric("Mínima Ano",          f"R$ {min_ano:.4f}")

    col_esq, col_dir = st.columns([0.45, 0.55])

    with col_esq:
        st.subheader("📋 Últimos 10 Dias Úteis")
        st.dataframe(styler_tabela, use_container_width=True, height=400, hide_index=True)

    with col_dir:
        st.subheader("📈 Tendência (Média Geral)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_grafico['DataStr'],
            y=df_grafico['MediaDia'],
            mode='lines+markers+text',
            text=df_grafico['MediaDia'].apply(lambda x: f"{x:.3f}"),
            textposition="top center",
            name='Média Dia',
            textfont=dict(size=14),
            line=dict(color='#1f77b4', width=3)
        ))
        fig.add_trace(go.Scatter(
            x=df_grafico['DataStr'],
            y=[media_periodo_constante] * len(df_grafico),
            mode='lines',
            name='Média Período',
            line=dict(color='#ff7f0e', width=2, dash='dot')
        ))
        fig.update_layout(
            margin=dict(l=10, r=10, t=30, b=10),
            height=400,
            template="plotly_white",
            showlegend=False,
            xaxis=dict(type='category', tickmode='linear', tickfont=dict(size=12)),
            yaxis=dict(tickfont=dict(size=12))
        )
        st.plotly_chart(fig, use_container_width=True)

    return True


# ---------------------------------------------------------------------------
# EXECUÇÃO PRINCIPAL
# ---------------------------------------------------------------------------

st.title("📊 Relatório Executivo de Câmbio")

sucesso_dolar = False
sucesso_euro  = False

df_dolar = carregar_dados('CotacaoDolar')
if df_dolar is not None:
    sucesso_dolar = gerar_painel_moeda(df_dolar, "Dólar", "💵")

st.markdown("<br><br>", unsafe_allow_html=True)

df_euro = carregar_dados('CotacaoEuro')
if df_euro is not None:
    sucesso_euro = gerar_painel_moeda(df_euro, "Euro", "💶")

# ---------------------------------------------------------------------------
# MARCADOR PARA O SELENIUM — NÃO REMOVER
# ---------------------------------------------------------------------------
# O robô (enviar_robo.py) aguarda um destes elementos para decidir
# se o e-mail será enviado ou abortado.
# ---------------------------------------------------------------------------

if sucesso_dolar and sucesso_euro:
    st.markdown('<div id="dashboard-ready" style="display:none">READY</div>', unsafe_allow_html=True)
else:
    st.markdown('<div id="dashboard-error" style="display:none">ERROR</div>', unsafe_allow_html=True)