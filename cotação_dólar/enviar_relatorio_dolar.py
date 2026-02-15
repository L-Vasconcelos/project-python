import streamlit as st
import pandas as pd
import pyodbc
import plotly.graph_objects as go
import holidays
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Relatório Fechamento Dólar", layout="wide")

# --- CSS: FORMATAÇÃO DE IMPRESSÃO ---
st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 0rem; padding-left: 2rem; padding-right: 2rem; }
    h1 { font-size: 2.5rem !important; }
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

# --- CONEXÃO ---


@st.cache_data(ttl=3600)
def carregar_dados():
    dados_conexao = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=CORPORATIVOMTCS;"
        "Database=Financeiro;"
        "Trusted_Connection=yes;"
    )
    try:
        conn = pyodbc.connect(dados_conexao)
        query = "SELECT DataCotacao, ValorCompra, ValorVenda FROM CotacaoDolar ORDER BY DataCotacao ASC"
        df = pd.read_sql(query, conn)
        conn.close()
        df['DataCotacao'] = pd.to_datetime(df['DataCotacao'])
        return df
    except Exception as e:
        st.error(f"Erro: {e}")
        return pd.DataFrame()


df_raw = carregar_dados()
if df_raw.empty:
    st.stop()

# --- LIMPEZA (SÁBADOS, DOMINGOS E FERIADOS) ---
df_clean = df_raw[df_raw['DataCotacao'].dt.dayofweek < 5].copy()
feriados_br = holidays.BR()
mask_feriados = ~df_clean['DataCotacao'].apply(lambda x: x in feriados_br)
df_clean = df_clean[mask_feriados]

# --- LÓGICA DINÂMICA D-1 ---
hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
df = df_clean[df_clean['DataCotacao'] < hoje].copy()

reg_ultimo = df.iloc[-1]     # D-1 útil
reg_penultimo = df.iloc[-2]   # D-2 útil
data_ref = reg_ultimo['DataCotacao']

# --- CÁLCULOS KPI (FECHAMENTO D-1) ---
# Venda
venda_atual = reg_ultimo['ValorVenda']
venda_anterior = reg_penultimo['ValorVenda']
delta_venda = ((venda_atual - venda_anterior) / venda_anterior) * 100

# Compra
compra_atual = reg_ultimo['ValorCompra']
compra_anterior = reg_penultimo['ValorCompra']
delta_compra = ((compra_atual - compra_anterior) / compra_anterior) * 100

# --- CÁLCULOS KPI (MÉDIAS DO ANO 2026) ---
df_ano = df[df['DataCotacao'].dt.year == data_ref.year].copy()

media_ano_compra = df_ano['ValorCompra'].mean()
media_ano_venda = df_ano['ValorVenda'].mean()
max_ano = df_ano['ValorVenda'].max()
min_ano = df_ano['ValorVenda'].min()

# --- PREPARAÇÃO DADOS VISUAIS (RECORTES 10 DIAS) ---
df_recorte = df.iloc[-11:].copy()
df_recorte['DataStr'] = df_recorte['DataCotacao'].dt.strftime('%d/%m')

# Cálculo da média diária para o gráfico
df_recorte['MediaDia'] = (df_recorte['ValorCompra'] +
                          df_recorte['ValorVenda']) / 2

df_tabela = df_recorte.sort_values(by='DataCotacao', ascending=False).copy()
df_tabela['Variação (%)'] = df_tabela['ValorVenda'].pct_change(-1) * 100
df_tabela_final = df_tabela.head(10)

df_view = df_tabela_final[['DataCotacao',
                           'ValorCompra', 'ValorVenda', 'Variação (%)']].copy()
df_view['DataCotacao'] = df_view['DataCotacao'].dt.strftime('%d/%m/%Y')


def estilo_variacao(val):
    if pd.isna(val):
        return 'color: white'
    color = '#4CAF50' if val > 0 else '#FF4B4B' if val < 0 else 'white'
    return f'color: {color}; font-weight: bold'


styler_tabela = df_view.style.applymap(estilo_variacao, subset=['Variação (%)'])\
    .format({'ValorCompra': 'R$ {:.4f}', 'ValorVenda': 'R$ {:.4f}', 'Variação (%)': '{:+.2f}%'})

df_grafico = df_recorte.iloc[1:].copy()

# Média constante do período (para a linha tracejada no gráfico)
media_periodo_constante = df_grafico['MediaDia'].mean()

# --- LAYOUT DASHBOARD ---
st.title(f"💵 Fechamento Dólar (PTAX) - {data_ref.strftime('%d/%m/%Y')}")

# 1. CARDS
col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Fechamento (Compra)",
            f"R$ {compra_atual:.4f}", f"{delta_compra:.2f}%")
col2.metric("Fechamento (Venda)",
            f"R$ {venda_atual:.4f}", f"{delta_venda:.2f}%")
col3.metric("Média Compra (Ano)", f"R$ {media_ano_compra:.4f}")
col4.metric("Média Venda (Ano)", f"R$ {media_ano_venda:.4f}")
col5.metric("Máxima Ano", f"R$ {max_ano:.4f}")
col6.metric("Mínima Ano", f"R$ {min_ano:.4f}")

st.markdown("---")

# 2. ÁREA PRINCIPAL
col_esq, col_dir, col_vazia = st.columns([0.45, 0.45, 0.1])

with col_esq:
    st.subheader("📋 Últimos 10 Dias Úteis")
    st.dataframe(styler_tabela, use_container_width=True,
                 height=380, hide_index=True)

with col_dir:
    st.subheader("📈 Tendência (Média Geral)")
    fig = go.Figure()

    # Linha principal: Média do Dia
    fig.add_trace(go.Scatter(
        x=df_grafico['DataStr'], y=df_grafico['MediaDia'],
        mode='lines+markers+text',
        text=df_grafico['MediaDia'].apply(lambda x: f"{x:.3f}"),
        textposition="top center", name='Média Dia',
        textfont=dict(size=15),  # AUMENTO DA FONTE DOS VALORES
        line=dict(color='#1f77b4', width=3)
    ))

    # Linha secundária: Média Constante do Período
    fig.add_trace(go.Scatter(
        x=df_grafico['DataStr'],
        y=[media_periodo_constante] * len(df_grafico),
        mode='lines', name='Média Período',
        line=dict(color='#ff7f0e', width=2, dash='dot')
    ))

    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=10), height=380,
        template="plotly_white", showlegend=False,
        xaxis=dict(
            type='category',
            tickmode='linear',
            tickfont=dict(size=14)  # AUMENTO DA FONTE DAS DATAS
        ),
        yaxis=dict(
            tickfont=dict(size=12)  # Aumento sutil do eixo Y caso apareça
        )
    )
    st.plotly_chart(fig, use_container_width=True)
