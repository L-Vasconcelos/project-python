import streamlit as st
import pandas as pd
import pyodbc
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Monitor do Dólar (PTAX)", layout="wide")

# --- FUNÇÃO DE CONEXÃO E CARGA ---
# Usamos um decorador de cache para o dashboard não ficar lento recarregando o banco a cada clique


@st.cache_data(ttl=3600)  # Cache dura 1 hora ou atualiza manual
def carregar_dados():
    dados_conexao = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=CORPORATIVOMTCS;"
        "Database=Financeiro;"
        "Trusted_Connection=yes;"
    )
    conn = pyodbc.connect(dados_conexao)

    # Trazemos tudo ordenado
    query = "SELECT DataCotacao, ValorCompra, ValorVenda FROM CotacaoDolar ORDER BY DataCotacao ASC"
    df = pd.read_sql(query, conn)
    conn.close()

    # Garantir que é data
    df['DataCotacao'] = pd.to_datetime(df['DataCotacao'])
    return df


# --- CARREGANDO DADOS ---
try:
    df = carregar_dados()
except Exception as e:
    st.error(f"Erro ao conectar no banco: {e}")
    st.stop()

# --- CÁLCULOS DE INDICADORES ---
# 1. Dados Mais Recentes
ultimo_reg = df.iloc[-1]
data_atual = ultimo_reg['DataCotacao']
valor_atual = ultimo_reg['ValorVenda']

# 2. Dados do Dia Anterior (para variação diária)
penultimo_reg = df.iloc[-2]
valor_ontem = penultimo_reg['ValorVenda']
variacao_dia = ((valor_atual - valor_ontem) / valor_ontem) * 100

# 3. Comparativo Ano Anterior (Mesma data 1 ano atrás)
data_ano_passado = data_atual - timedelta(days=365)
# Busca a data mais próxima no passado (caso tenha caído em fim de semana)
df_ano_passado = df[df['DataCotacao'] <= data_ano_passado].iloc[-1]
valor_ano_passado = df_ano_passado['ValorVenda']
variacao_anual = ((valor_atual - valor_ano_passado) / valor_ano_passado) * 100

# 4. Tendências (Médias Móveis)
df['MediaMovel_30d'] = df['ValorVenda'].rolling(window=30).mean()

# --- INTERFACE VISUAL (DASHBOARD) ---

# Título
st.title("💵 Monitor de Cotação do Dólar (PTAX)")
st.markdown(f"**Última atualização:** {data_atual.strftime('%d/%m/%Y')}")
st.markdown("---")

# BLOCO 1: INDICADORES ESSENCIAIS (KPIs)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Cotação Atual (Venda)",
        value=f"R$ {valor_atual:.4f}",
        delta=f"{variacao_dia:.2f}% (vs. Ontem)"
    )

with col2:
    st.metric(
        label="Comparativo Ano Anterior",
        value=f"R$ {valor_ano_passado:.4f}",
        delta=f"{variacao_anual:.2f}% (12 meses)",
        # Vermelho se subiu (ruim para importador, bom para exportador)
        delta_color="inverse"
    )

with col3:
    max_ano = df[df['DataCotacao'].dt.year ==
                 data_atual.year]['ValorVenda'].max()
    st.metric(label="Máxima do Ano", value=f"R$ {max_ano:.4f}")

with col4:
    min_ano = df[df['DataCotacao'].dt.year ==
                 data_atual.year]['ValorVenda'].min()
    st.metric(label="Mínima do Ano", value=f"R$ {min_ano:.4f}")

# BLOCO 2: GRÁFICOS
st.markdown("---")

# Filtro de Data na Barra Lateral
st.sidebar.header("Filtros")
anos_disponiveis = df['DataCotacao'].dt.year.unique()
anos_selecionados = st.sidebar.multiselect(
    # Padrão: 2 últimos anos
    "Selecione os Anos", anos_disponiveis, default=anos_disponiveis[-2:])

# Filtra o DataFrame para o gráfico
df_filtrado = df[df['DataCotacao'].dt.year.isin(anos_selecionados)]

# Gráfico 1: Evolução com Tendência
st.subheader("📈 Evolução da Cotação e Tendência")
fig_evolucao = go.Figure()

# Linha principal
fig_evolucao.add_trace(go.Scatter(
    x=df_filtrado['DataCotacao'],
    y=df_filtrado['ValorVenda'],
    mode='lines',
    name='Dólar Venda',
    line=dict(color='#1f77b4', width=2)
))

# Linha de tendência
fig_evolucao.add_trace(go.Scatter(
    x=df_filtrado['DataCotacao'],
    y=df_filtrado['MediaMovel_30d'],
    mode='lines',
    name='Tendência (Média 30 dias)',
    line=dict(color='#ff7f0e', width=2, dash='dot')
))

fig_evolucao.update_layout(
    xaxis_title="Data", yaxis_title="Valor (R$)", height=500, template="plotly_white")
st.plotly_chart(fig_evolucao, use_container_width=True)

# Gráfico 2: Análise Mensal (Boxplot - mostra a variação dentro de cada mês)
st.subheader("📊 Volatilidade Mensal (Máxima, Mínima e Fechamento)")
df_filtrado['Mes_Ano'] = df_filtrado['DataCotacao'].dt.strftime('%Y-%m')
fig_volatilidade = px.box(df_filtrado, x="Mes_Ano",
                          y="ValorVenda", title="Variação de Preço por Mês")
st.plotly_chart(fig_volatilidade, use_container_width=True)
