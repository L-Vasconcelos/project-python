"""
Dashboard Streamlit — Pricing Importados
Fonte: SQL Server (CORPORATIVOMTCS · historico_precos_quimicos)
Versão: 2.0 — Dark OLED · Fira Code · Layout Compacto
"""

import streamlit as st
import pandas as pd
import pyodbc
from datetime import datetime
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Pricing · Importados", layout="wide")

# --- CSS DARK OLED + FIRA CODE ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Fira Sans', sans-serif !important;
    background-color: #020617 !important;
    color: #F8FAFC !important;
}
.block-container {
    padding-top: 0.6rem !important;
    padding-bottom: 0.4rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    max-width: 100% !important;
}
/* Header */
.dash-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    border: 1px solid #1E293B;
    border-left: 4px solid #06b6d4;
    border-radius: 8px;
    padding: 10px 18px;
    margin-bottom: 10px;
}
.dash-header .titulo {
    font-family: 'Fira Code', monospace;
    font-size: 1.15rem;
    font-weight: 700;
    color: #F8FAFC;
    letter-spacing: 0.04em;
}
.dash-header .subtitulo {
    font-size: 0.78rem;
    color: #94A3B8;
    font-family: 'Fira Code', monospace;
}
.dash-header .data-ref {
    font-family: 'Fira Code', monospace;
    font-size: 0.82rem;
    color: #06b6d4;
    background: #06b6d415;
    border: 1px solid #06b6d430;
    border-radius: 5px;
    padding: 4px 10px;
}
/* Metric Cards */
.metric-row {
    display: flex;
    gap: 8px;
    margin-bottom: 10px;
}
.metric-card {
    flex: 1;
    background: #0F172A;
    border: 1px solid #1E293B;
    border-radius: 7px;
    padding: 8px 12px;
    text-align: center;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: #334155; }
.metric-card .m-label {
    font-size: 0.68rem;
    font-weight: 600;
    color: #64748B;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-family: 'Fira Sans', sans-serif;
    margin-bottom: 2px;
}
.metric-card .m-value {
    font-family: 'Fira Code', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    line-height: 1.1;
}
.metric-card.total  .m-value { color: #F8FAFC; }
.metric-card.alta   .m-value { color: #10b981; text-shadow: 0 0 10px #10b98140; }
.metric-card.baixa  .m-value { color: #f43f5e; text-shadow: 0 0 10px #f43f5e40; }
.metric-card.estavel .m-value { color: #94A3B8; }
.metric-card.semref .m-value { color: #f59e0b; }
.metric-card.grupos .m-value { color: #8b5cf6; text-shadow: 0 0 10px #8b5cf640; }
/* Section titles */
.section-title {
    font-family: 'Fira Code', monospace;
    font-size: 0.78rem;
    font-weight: 700;
    color: #475569;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 6px;
    padding-bottom: 4px;
    border-bottom: 1px solid #1E293B;
}
/* Grupo header */
.grupo-header {
    padding: 3px 10px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    font-family: 'Fira Code', monospace;
    margin-top: 6px;
    margin-bottom: 3px;
}
/* Dataframe override */
div[data-testid="stDataFrame"] td,
div[data-testid="stDataFrame"] th {
    font-size: 0.82rem !important;
    padding: 4px 8px !important;
    font-family: 'Fira Code', monospace !important;
}
div[data-testid="stDataFrame"] thead th {
    background-color: #0F172A !important;
    color: #64748B !important;
    font-size: 0.70rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}
/* Footer */
.dash-footer {
    font-family: 'Fira Code', monospace;
    font-size: 0.68rem;
    color: #334155;
    text-align: center;
    border-top: 1px solid #1E293B;
    padding-top: 6px;
    margin-top: 6px;
}
/* Hide Streamlit chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stToolbar"] {visibility: hidden;}
/* Remove default title padding */
h1, h2, h3 { margin: 0 !important; padding: 0 !important; }
/* Compact columns gap */
[data-testid="column"] { padding: 0 4px !important; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# CONFIGURAÇÃO
# ---------------------------------------------------------------------------

SQL_SERVER   = "CORPORATIVOMTCS"
SQL_DATABASE = "historico_precos_quimicos"
SQL_TABLE    = "historico_precos_quimicos"

GRUPO_COR = {
    "Ácidos":                   "#06b6d4",
    "Álcoois":                  "#8b5cf6",
    "Outros Químicos":          "#f59e0b",
    "Polímeros/PEGs":           "#10b981",
    "Tensoativos/Polisorbatos": "#f43f5e",
    "Edulcorantes/Outros":      "#fb923c",
}


# ---------------------------------------------------------------------------
# CONEXÃO COM BANCO DE DADOS
# ---------------------------------------------------------------------------

def carregar_dados() -> pd.DataFrame | None:
    dados_conexao = (
        "Driver={ODBC Driver 17 for SQL Server};"
        f"Server={SQL_SERVER};"
        f"Database={SQL_DATABASE};"
        "Trusted_Connection=yes;"
    )
    query = f"""
        SELECT Data, Item, Preco, Unidade, Moeda, Grupo, Fonte
        FROM [{SQL_TABLE}]
        ORDER BY Data, Grupo, Item
    """
    ultimo_erro = None
    for tentativa in range(1, 3):
        try:
            conn = pyodbc.connect(dados_conexao, timeout=15)
            df = pd.read_sql(query, conn)
            conn.close()
            if df.empty:
                st.error(f"TABELA VAZIA: {SQL_TABLE} não retornou registros.")
                return None
            df["Data"] = pd.to_datetime(df["Data"]).dt.normalize()  # remove hora, mantém só a data
            df = df.sort_values("Data")
            df = df.drop_duplicates(subset=["Data", "Item"], keep="last")  # 1 entrada por dia/item
            return df
        except Exception as e:
            ultimo_erro = e
            if tentativa < 2:
                time.sleep(5)
    st.error(f"ERRO DE CONEXÃO após 2 tentativas: {ultimo_erro}")
    return None


# ---------------------------------------------------------------------------
# LÓGICA DE NEGÓCIO
# ---------------------------------------------------------------------------

def preco_por_kg(preco, unidade):
    if str(unidade).upper() == "MT":
        return round(preco / 1000, 4), "kg"
    return round(preco, 4), unidade


def calcular_variacao(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    datas   = sorted(df["Data"].unique())
    d_atual = datas[-1]
    d_ant   = datas[-2] if len(datas) > 1 else None

    atual = df[df["Data"] == d_atual][
        ["Item", "Preco", "Unidade", "Grupo", "Fonte"]].copy()
    atual.columns = ["Item", "Preco_Atual", "Unidade", "Grupo", "Fonte"]

    if d_ant is not None:
        ant = df[df["Data"] == d_ant][["Item", "Preco"]].rename(
            columns={"Preco": "Preco_Ant"})
        result = atual.merge(ant, on="Item", how="left")
    else:
        result = atual.copy()
        result["Preco_Ant"] = None

    result["Var_Pct"] = (
        (result["Preco_Atual"] - result["Preco_Ant"]) /
        result["Preco_Ant"] * 100
    ).round(2)
    result["Var_Abs"] = (result["Preco_Atual"] - result["Preco_Ant"]).round(2)
    result["Data_Ref"] = d_atual
    result["Data_Ant"] = d_ant
    return result.sort_values(["Grupo", "Item"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# ESTILO
# ---------------------------------------------------------------------------

def estilo_variacao(val):
    if pd.isna(val):
        return "color: #475569"
    if val > 0:
        return "color: #10b981; font-weight: 600"
    if val < 0:
        return "color: #f43f5e; font-weight: 600"
    return "color: #475569"


def estilo_preco(val):
    return "color: #93c5fd; font-weight: 600"


# ---------------------------------------------------------------------------
# RENDERIZAÇÃO
# ---------------------------------------------------------------------------

def gerar_painel_pricing(df_raw: pd.DataFrame) -> None:
    var_df  = calcular_variacao(df_raw)
    d_ref   = pd.to_datetime(var_df["Data_Ref"].iloc[0])
    d_ant   = var_df["Data_Ant"].iloc[0]
    d_ant_str = pd.to_datetime(d_ant).strftime('%d/%m/%Y') if pd.notna(d_ant) else "sem ref."
    grupos  = list(var_df["Grupo"].unique())

    n_total  = len(var_df)
    n_alta   = int((var_df["Var_Pct"] > 0).sum())
    n_baixa  = int((var_df["Var_Pct"] < 0).sum())
    n_estavel = int((var_df["Var_Pct"] == 0).sum())
    n_sem_ref = int(var_df["Var_Pct"].isna().sum())
    n_grupos = len(grupos)

    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    # --- HEADER ---
    st.markdown(f"""
    <div class="dash-header">
        <div>
            <div class="titulo">PRICING · QUIMICOS IMPORTADOS</div>
            <div class="subtitulo">{SQL_SERVER} / {SQL_DATABASE}</div>
        </div>
        <div class="data-ref">var. {d_ant_str} → {d_ref.strftime('%d/%m/%Y')} &nbsp;|&nbsp; atualizado {agora}</div>
    </div>
    """, unsafe_allow_html=True)

    # --- MÉTRICAS ---
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card total">
            <div class="m-label">Total Produtos</div>
            <div class="m-value">{n_total}</div>
        </div>
        <div class="metric-card alta">
            <div class="m-label">Em Alta</div>
            <div class="m-value">{n_alta}</div>
        </div>
        <div class="metric-card baixa">
            <div class="m-label">Em Baixa</div>
            <div class="m-value">{n_baixa}</div>
        </div>
        <div class="metric-card estavel">
            <div class="m-label">Estáveis</div>
            <div class="m-value">{n_estavel}</div>
        </div>
        <div class="metric-card semref">
            <div class="m-label">Sem Ref.</div>
            <div class="m-value">{n_sem_ref}</div>
        </div>
        <div class="metric-card grupos">
            <div class="m-label">Grupos</div>
            <div class="m-value">{n_grupos}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- TABELAS LADO A LADO ---
    metade = (len(grupos) + 1) // 2
    grupos_esq = grupos[:metade]
    grupos_dir = grupos[metade:]

    col_esq, col_dir = st.columns(2)

    def renderizar_grupos(col, lista_grupos):
        with col:
            st.markdown('<div class="section-title">Tabela de Precos por Grupo</div>',
                        unsafe_allow_html=True)
            for grupo in lista_grupos:
                cor   = GRUPO_COR.get(grupo, "#06b6d4")
                itens = var_df[var_df["Grupo"] == grupo].copy()

                st.markdown(
                    f'<div class="grupo-header" style="background:{cor}15; color:{cor}; '
                    f'border-left: 3px solid {cor};">'
                    f'{grupo.upper()} &nbsp;·&nbsp; {len(itens)} itens</div>',
                    unsafe_allow_html=True
                )

                df_view = itens[["Item", "Preco_Atual", "Unidade",
                                 "Var_Pct", "Var_Abs", "Fonte"]].copy()

                df_view[["Preco_Atual", "Unidade"]] = df_view.apply(
                    lambda r: pd.Series(preco_por_kg(r["Preco_Atual"], r["Unidade"])),
                    axis=1
                )

                df_view.rename(columns={
                    "Item":        "Produto",
                    "Preco_Atual": "Preco USD",
                    "Unidade":     "Un.",
                    "Var_Pct":     "Var.%",
                    "Var_Abs":     "Var.Abs",
                    "Fonte":       "Fonte",
                }, inplace=True)

                styler = (
                    df_view.style
                    .map(estilo_variacao, subset=["Var.%"])
                    .map(estilo_variacao, subset=["Var.Abs"])
                    .map(estilo_preco,    subset=["Preco USD"])
                    .format({
                        "Preco USD": "$ {:.4f}",
                        "Var.%":     lambda v: f"{v:+.2f}%" if pd.notna(v) else "—",
                        "Var.Abs":   lambda v: f"{v:+.4f}"  if pd.notna(v) else "—",
                    })
                    .set_table_styles([{
                        "selector": "th",
                        "props": [("background-color", "#0F172A"),
                                  ("color", "#475569"),
                                  ("font-size", "0.70rem"),
                                  ("text-transform", "uppercase"),
                                  ("letter-spacing", "0.06em")],
                    }])
                )

                st.dataframe(styler, use_container_width=True, hide_index=True)

    renderizar_grupos(col_esq, grupos_esq)
    renderizar_grupos(col_dir, grupos_dir)

    # --- FOOTER ---
    st.markdown(
        f'<div class="dash-footer">'
        f'{SQL_SERVER} &nbsp;/&nbsp; {SQL_DATABASE} &nbsp;·&nbsp; '
        f'ref. {d_ref.strftime("%d/%m/%Y")} &nbsp;·&nbsp; '
        f'atualizado {agora} &nbsp;·&nbsp; refresh automatico a cada 60s'
        f'</div>',
        unsafe_allow_html=True
    )


# ---------------------------------------------------------------------------
# EXECUÇÃO PRINCIPAL
# ---------------------------------------------------------------------------

df = carregar_dados()
if df is not None:
    gerar_painel_pricing(df)
    # Marcador lido pelo robô para confirmar que o dashboard carregou com sucesso
    st.markdown('<div id="dashboard-ready"></div>', unsafe_allow_html=True)
else:
    # Marcador de falha — robô aborta o envio do e-mail
    st.markdown('<div id="dashboard-error"></div>', unsafe_allow_html=True)

# Auto-refresh a cada 60 segundos (via browser, sem bloquear a thread)
st.markdown('<meta http-equiv="refresh" content="60">', unsafe_allow_html=True)
