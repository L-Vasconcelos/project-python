import streamlit as st
import pandas as pd
import pyodbc
import plotly.graph_objects as go
import holidays
from datetime import datetime, timedelta

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

def carregar_dados(nome_tabela):
    """Carrega dados do SQL Server com tratamento de erro robusto."""
    dados_conexao = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=CORPORATIVOMTCS;"
        "Database=Financeiro;"
        "Trusted_Connection=yes;"
    )
    try:
        conn = pyodbc.connect(dados_conexao, timeout=10)
        # Otimização: Pegar apenas os últimos 60 registros para performance
        query = f"SELECT TOP 60 DataCotacao, ValorCompra, ValorVenda FROM {nome_tabela} ORDER BY DataCotacao DESC"
        df = pd.read_sql(query, conn)
        conn.close()
        
        if df.empty:
            return None
            
        df['DataCotacao'] = pd.to_datetime(df['DataCotacao'])
        # Reordenar para cronológico após pegar os últimos
        df = df.sort_values(by='DataCotacao', ascending=True)
        return df
    except Exception as e:
        # Erro crítico: O dashboard não deve renderizar se não houver dados
        st.error(f"ERRO CRÍTICO DE CONEXÃO ({nome_tabela}): {e}")
        return None

def estilo_variacao(val):
    if pd.isna(val):
        return 'color: white'
    color = '#4CAF50' if val > 0 else '#FF4B4B' if val < 0 else 'white'
    return f'color: {color}; font-weight: bold'

def gerar_painel_moeda(df_raw, nome_moeda, icone):
    """Gera o painel visual para a moeda especificada."""
    if df_raw is None or df_raw.empty:
        st.error(f"❌ DADOS NÃO LOCALIZADOS: {nome_moeda}")
        return False

    # Filtrar dias úteis e feriados
    df_clean = df_raw[df_raw['DataCotacao'].dt.dayofweek < 5].copy()
    feriados_br = holidays.BR()
    mask_feriados = ~df_clean['DataCotacao'].apply(lambda x: x in feriados_br)
    df_clean = df_clean[mask_feriados]

    # Garantir que temos dados suficientes para comparação
    if len(df_clean) < 2:
        st.warning(f"Dados insuficientes para {nome_moeda} (mínimo 2 dias úteis).")
        return False

    reg_ultimo = df_clean.iloc[-1]
    reg_penultimo = df_clean.iloc[-2]
    data_ref = reg_ultimo['DataCotacao']

    # Validação de Recência: Se o último dado for mais antigo que 3 dias úteis, alertar
    hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if (hoje - data_ref).days > 5: # Tolerância para fins de semana prolongados
        st.warning(f"Atenção: Os dados de {nome_moeda} estão desatualizados (Último: {data_ref.strftime('%d/%m/%Y')})")

    venda_atual = reg_ultimo['ValorVenda']
    venda_anterior = reg_penultimo['ValorVenda']
    delta_venda = ((venda_atual - venda_anterior) / venda_anterior) * 100

    compra_atual = reg_ultimo['ValorCompra']
    compra_anterior = reg_penultimo['ValorCompra']
    delta_compra = ((compra_atual - compra_anterior) / compra_anterior) * 100

    # Estatísticas Anuais (baseadas no que foi carregado)
    df_ano = df_clean[df_clean['DataCotacao'].dt.year == data_ref.year].copy()
    media_ano_compra = df_ano['ValorCompra'].mean()
    media_ano_venda = df_ano['ValorVenda'].mean()
    max_ano = df_ano['ValorVenda'].max()
    min_ano = df_ano['ValorVenda'].min()

    # Preparação da Tabela (Últimos 10 dias úteis)
    df_recorte = df_clean.iloc[-11:].copy()
    df_recorte['DataStr'] = df_recorte['DataCotacao'].dt.strftime('%d/%m')
    df_recorte['MediaDia'] = (df_recorte['ValorCompra'] + df_recorte['ValorVenda']) / 2

    df_tabela = df_recorte.sort_values(by='DataCotacao', ascending=False).copy()
    df_tabela['Variação (%)'] = df_tabela['ValorVenda'].pct_change(-1) * 100
    df_tabela_final = df_tabela.head(10)

    df_view = df_tabela_final[['DataCotacao', 'MediaDia', 'ValorCompra', 'ValorVenda', 'Variação (%)']].copy()
    df_view.rename(columns={'MediaDia': 'Média (C/V)'}, inplace=True)
    df_view['DataCotacao'] = df_view['DataCotacao'].dt.strftime('%d/%m/%Y')

    styler_tabela = df_view.style\
        .map(estilo_variacao, subset=['Variação (%)'])\
        .map(lambda _: 'color: #FFD700; font-weight: bold', subset=['Média (C/V)'])\
        .format({'ValorCompra': 'R$ {:.4f}', 'ValorVenda': 'R$ {:.4f}', 'Média (C/V)': 'R$ {:.4f}', 'Variação (%)': '{:+.2f}%'})

    # Gráfico de Tendência
    df_grafico = df_recorte.iloc[1:].copy()
    media_periodo_constante = df_grafico['MediaDia'].mean()

    st.markdown(f"<h2>{icone} Fechamento {nome_moeda} (PTAX) - {data_ref.strftime('%d/%m/%Y')}</h2>", unsafe_allow_html=True)
    st.markdown("---")

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Fechamento (Compra)", f"R$ {compra_atual:.4f}", f"{delta_compra:.2f}%")
    col2.metric("Fechamento (Venda)", f"R$ {venda_atual:.4f}", f"{delta_venda:.2f}%")
    col3.metric("Média Compra (Ano)", f"R$ {media_ano_compra:.4f}")
    col4.metric("Média Venda (Ano)", f"R$ {media_ano_venda:.4f}")
    col5.metric("Máxima Ano", f"R$ {max_ano:.4f}")
    col6.metric("Mínima Ano", f"R$ {min_ano:.4f}")

    col_esq, col_dir = st.columns([0.45, 0.55])
    with col_esq:
        st.subheader("📋 Últimos 10 Dias Úteis")
        st.dataframe(styler_tabela, use_container_width=True, height=400, hide_index=True)

    with col_dir:
        st.subheader("📈 Tendência (Média Geral)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_grafico['DataStr'], y=df_grafico['MediaDia'],
            mode='lines+markers+text',
            text=df_grafico['MediaDia'].apply(lambda x: f"{x:.3f}"),
            textposition="top center", name='Média Dia',
            textfont=dict(size=14), line=dict(color='#1f77b4', width=3)
        ))
        fig.add_trace(go.Scatter(
            x=df_grafico['DataStr'], y=[media_periodo_constante] * len(df_grafico),
            mode='lines', name='Média Período',
            line=dict(color='#ff7f0e', width=2, dash='dot')
        ))
        fig.update_layout(
            margin=dict(l=10, r=10, t=30, b=10), height=400,
            template="plotly_white", showlegend=False,
            xaxis=dict(type='category', tickmode='linear', tickfont=dict(size=12)),
            yaxis=dict(tickfont=dict(size=12))
        )
        st.plotly_chart(fig, use_container_width=True)
    
    return True

# --- INÍCIO DA EXECUÇÃO ---
st.title("📊 Relatório Executivo de Câmbio")

# Flag de sucesso para controle do Selenium
sucesso_dolar = False
sucesso_euro = False

df_dolar = carregar_dados('CotacaoDolar')
if df_dolar is not None:
    sucesso_dolar = gerar_painel_moeda(df_dolar, "Dólar", "💵")

st.markdown("<br><br>", unsafe_allow_html=True) 

df_euro = carregar_dados('CotacaoEuro')
if df_euro is not None:
    sucesso_euro = gerar_painel_moeda(df_euro, "Euro", "💶")

# Marcador invisível para o Selenium validar se tudo carregou OK
if sucesso_dolar and sucesso_euro:
    st.markdown('<div id="dashboard-ready" style="display:none">READY</div>', unsafe_allow_html=True)
else:
    st.markdown('<div id="dashboard-error" style="display:none">ERROR</div>', unsafe_allow_html=True)