"""
Dashboard de Cotações Químicas
Requer: pip install dash plotly pandas openpyxl requests
Execução: python app.py
Acesso: http://localhost:8050
"""

import os
import io
import hashlib
import logging
import requests
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
from datetime import datetime

from utils import GRUPO_COR, preco_por_kg, calcular_variacao

# ─── CONFIGURAÇÃO ────────────────────────────────────────────────────────────

# Arquivo sincronizado pelo cliente OneDrive Desktop
LOCAL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "historico_precos_quimicos.xlsx"
)
# Fallback: tenta baixar diretamente do SharePoint se o arquivo local não existir
ONEDRIVE_URL = (
    "https://meridionaltcs-my.sharepoint.com/personal/bi_mtcs_com_br"
    "/Documents/Arquivos/Python/importado/historico_precos_quimicos.xlsx"
    "?download=1"
)

# Polling: verifica mudança no arquivo a cada N segundos
POLL_INTERVAL_MS = 30_000  # 30 segundos

log = logging.getLogger(__name__)

# ─── PALETA ──────────────────────────────────────────────────────────────────

CORES = {
    "bg":        "#0a0e1a",
    "card":      "#111827",
    "card2":     "#1a2235",
    "border":    "#1e2d45",
    "text":      "#e2e8f0",
    "muted":     "#64748b",
    "accent":    "#06b6d4",
    "up":        "#10b981",
    "down":      "#f43f5e",
    "neutral":   "#94a3b8",
    "grupos":    GRUPO_COR,  # compartilhado via utils.py
}

# ─── DADOS ───────────────────────────────────────────────────────────────────

# Nota: _cache_hash é estado global — funciona corretamente em processo único.
# Em deploys multi-worker (Gunicorn), substituir por cache externo (Redis/disco).
_cache_hash = None


def _hash_bytes(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def _baixar_onedrive() -> bytes | None:
    """Tenta baixar o arquivo direto do SharePoint (requer link público ou autenticação)."""
    try:
        r = requests.get(ONEDRIVE_URL, timeout=15)
        if r.status_code == 200:
            return r.content
        log.warning(f"Download OneDrive retornou status {r.status_code}")
    except Exception as e:
        log.warning(f"Falha ao baixar do OneDrive: {e}")
    return None


def _ler_local() -> bytes | None:
    if os.path.exists(LOCAL_PATH):
        with open(LOCAL_PATH, "rb") as f:
            return f.read()
    return None


def carregar_dados() -> tuple[pd.DataFrame, str, bool]:
    """
    Retorna (df, fonte_str, mudou).
    Tenta o arquivo local primeiro; se ausente, faz fallback para download do OneDrive.
    """
    global _cache_hash

    raw = _ler_local()
    fonte = "OneDrive (local sync)"

    if raw is None:
        log.warning(f"Arquivo local não encontrado ({LOCAL_PATH}), tentando download...")
        raw = _baixar_onedrive()
        fonte = "OneDrive (download direto)"

    if raw is None:
        return pd.DataFrame(), f"Arquivo não encontrado: {LOCAL_PATH}", False

    novo_hash = _hash_bytes(raw)
    mudou = novo_hash != _cache_hash
    _cache_hash = novo_hash

    df = pd.read_excel(io.BytesIO(raw))
    df["Data"] = pd.to_datetime(df["Data"])
    df = df.sort_values("Data")
    return df, fonte, mudou


# ─── COMPONENTES ─────────────────────────────────────────────────────────────

def card_produto(row: dict) -> html.Div:
    preco, unid = preco_por_kg(row["Preco_Atual"], row["Unidade"])
    cor_grupo = CORES["grupos"].get(row["Grupo"], CORES["accent"])
    var = row["Var_Pct"]

    if pd.isna(var):
        var_cor = CORES["neutral"]
        var_txt = "—"
        seta = ""
    elif var > 0:
        var_cor = CORES["up"]
        var_txt = f"+{var:.2f}%"
        seta = "▲"
    elif var < 0:
        var_cor = CORES["down"]
        var_txt = f"{var:.2f}%"
        seta = "▼"
    else:
        var_cor = CORES["neutral"]
        var_txt = "0,00%"
        seta = "—"

    return html.Div(
        style={
            "background": CORES["card"],
            "border": f"1px solid {CORES['border']}",
            "borderLeft": f"3px solid {cor_grupo}",
            "borderRadius": "8px",
            "padding": "12px 14px",
            "display": "flex",
            "flexDirection": "column",
            "gap": "6px",
            "minWidth": "0",
        },
        children=[
            html.Div(
                row["Item"],
                style={
                    "fontSize": "11px",
                    "fontWeight": "600",
                    "color": CORES["text"],
                    "letterSpacing": "0.04em",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                    "whiteSpace": "nowrap",
                },
            ),
            html.Div(
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "baseline"},
                children=[
                    html.Span(
                        f"${preco:,.4f}/{unid}",
                        style={"fontSize": "15px", "fontWeight": "700", "color": CORES["text"]},
                    ),
                    html.Span(
                        f"{seta} {var_txt}",
                        style={"fontSize": "13px", "fontWeight": "700", "color": var_cor},
                    ),
                ],
            ),
            html.Div(
                row["Fonte"] if not pd.isna(row.get("Fonte", "")) else "",
                style={"fontSize": "9px", "color": CORES["muted"], "overflow": "hidden", "textOverflow": "ellipsis", "whiteSpace": "nowrap"},
            ),
        ],
    )


def grafico_grupo(df: pd.DataFrame, grupo: str) -> dcc.Graph:
    itens = df[df["Grupo"] == grupo]["Item"].unique()

    fig = go.Figure()

    for item in sorted(itens):
        serie = df[df["Item"] == item].sort_values("Data")
        if serie.empty:
            continue
        precos_kg = [preco_por_kg(p, u)[0] for p, u in zip(serie["Preco"], serie["Unidade"])]
        fig.add_trace(
            go.Scatter(
                x=serie["Data"],
                y=precos_kg,
                mode="lines+markers",
                name=item,
                line=dict(width=2),
                marker=dict(size=5),
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "Data: %{x|%d/%m/%Y}<br>"
                    "$%{y:,.4f}<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="'JetBrains Mono', monospace", size=10, color=CORES["muted"]),
        margin=dict(l=8, r=8, t=8, b=8),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(size=9),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            gridcolor=CORES["border"],
            linecolor=CORES["border"],
            tickformat="%d/%m",
            tickfont=dict(size=9),
        ),
        yaxis=dict(
            gridcolor=CORES["border"],
            linecolor=CORES["border"],
            tickprefix="$",
            tickfont=dict(size=9),
        ),
        hovermode="x unified",
        height=220,
    )

    return dcc.Graph(
        figure=fig,
        config={"displayModeBar": False},
        style={"width": "100%"},
    )


# ─── LAYOUT ──────────────────────────────────────────────────────────────────

app = Dash(__name__, title="Citações Químicas")
app.layout = html.Div(
    id="root",
    style={
        "background": CORES["bg"],
        "minHeight": "100vh",
        "fontFamily": "'JetBrains Mono', 'Fira Code', monospace",
        "color": CORES["text"],
        "padding": "0",
        "margin": "0",
    },
    children=[
        dcc.Interval(id="intervalo", interval=POLL_INTERVAL_MS, n_intervals=0),
        dcc.Store(id="store-dados"),

        # HEADER
        html.Div(
            style={
                "background": CORES["card"],
                "borderBottom": f"1px solid {CORES['border']}",
                "padding": "14px 24px",
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "position": "sticky",
                "top": "0",
                "zIndex": "100",
            },
            children=[
                html.Div(
                    children=[
                        html.Span("⬡ ", style={"color": CORES["accent"], "fontSize": "18px"}),
                        html.Span(
                            "CITAÇÕES QUÍMICAS",
                            style={"fontWeight": "800", "fontSize": "15px", "letterSpacing": "0.12em"},
                        ),
                        html.Span(
                            " · Importados",
                            style={"color": CORES["muted"], "fontSize": "12px", "marginLeft": "6px"},
                        ),
                    ]
                ),
                html.Div(
                    id="header-status",
                    style={"fontSize": "11px", "color": CORES["muted"]},
                ),
            ],
        ),

        # CORPO PRINCIPAL
        html.Div(
            id="corpo",
            style={"padding": "20px 24px", "maxWidth": "1600px", "margin": "0 auto"},
        ),
    ],
)


# ─── CALLBACKS ───────────────────────────────────────────────────────────────

@app.callback(
    Output("store-dados", "data"),
    Output("header-status", "children"),
    Input("intervalo", "n_intervals"),
)
def atualizar_store(n):
    df, fonte, mudou = carregar_dados()
    if df.empty:
        return None, "❌ Sem dados"

    datas = sorted(df["Data"].unique())
    data_ref = pd.to_datetime(datas[-1]).strftime("%d/%m/%Y")
    agora = datetime.now().strftime("%H:%M:%S")
    status = f"Ref: {data_ref}  ·  Fonte: {fonte}  ·  Sync: {agora}"

    return df.to_json(date_format="iso", orient="records"), status


@app.callback(
    Output("corpo", "children"),
    Input("store-dados", "data"),
)
def renderizar(json_data):
    if json_data is None:
        return html.Div("Aguardando dados...", style={"color": CORES["muted"], "padding": "40px"})

    df = pd.read_json(json_data, orient="records")
    df["Data"] = pd.to_datetime(df["Data"])

    var_df = calcular_variacao(df)
    grupos = sorted(df["Grupo"].unique())

    # ── KPIs do topo ──────────────────────────────────────────────────────
    n_alta = int((var_df["Var_Pct"] > 0).sum())
    n_baixa = int((var_df["Var_Pct"] < 0).sum())
    n_estavel = int((var_df["Var_Pct"] == 0).sum())

    top_alta = var_df.nlargest(1, "Var_Pct").iloc[0] if n_alta else None
    top_baixa = var_df.nsmallest(1, "Var_Pct").iloc[0] if n_baixa else None

    def kpi(label, valor, cor):
        return html.Div(
            style={
                "background": CORES["card"],
                "border": f"1px solid {CORES['border']}",
                "borderRadius": "8px",
                "padding": "12px 18px",
                "display": "flex",
                "flexDirection": "column",
                "gap": "2px",
                "minWidth": "130px",
            },
            children=[
                html.Div(label, style={"fontSize": "9px", "color": CORES["muted"], "letterSpacing": "0.1em", "textTransform": "uppercase"}),
                html.Div(str(valor), style={"fontSize": "28px", "fontWeight": "800", "color": cor}),
            ],
        )

    def destaque(label, row, cor):
        if row is None:
            return html.Div()
        preco, unid = preco_por_kg(row["Preco_Atual"], row["Unidade"])
        return html.Div(
            style={
                "background": CORES["card"],
                "border": f"1px solid {CORES['border']}",
                "borderLeft": f"3px solid {cor}",
                "borderRadius": "8px",
                "padding": "12px 18px",
                "flex": "1",
            },
            children=[
                html.Div(label, style={"fontSize": "9px", "color": CORES["muted"], "letterSpacing": "0.1em", "textTransform": "uppercase"}),
                html.Div(row["Item"], style={"fontSize": "13px", "fontWeight": "700", "color": CORES["text"], "marginTop": "4px"}),
                html.Div(
                    f"${preco:,.4f}/{unid}  ·  {row['Var_Pct']:+.2f}%",
                    style={"fontSize": "12px", "color": cor, "marginTop": "2px"},
                ),
            ],
        )

    barra_kpi = html.Div(
        style={"display": "flex", "gap": "12px", "marginBottom": "20px", "flexWrap": "wrap", "alignItems": "stretch"},
        children=[
            kpi("PRODUTOS", len(var_df), CORES["text"]),
            kpi("EM ALTA", n_alta, CORES["up"]),
            kpi("EM BAIXA", n_baixa, CORES["down"]),
            kpi("ESTÁVEIS", n_estavel, CORES["neutral"]),
            destaque("▲ MAIOR ALTA", top_alta, CORES["up"]),
            destaque("▼ MAIOR BAIXA", top_baixa, CORES["down"]),
        ],
    )

    # ── Seções por grupo ───────────────────────────────────────────────────
    secoes = []
    for grupo in grupos:
        cor_grupo = CORES["grupos"].get(grupo, CORES["accent"])
        itens_grupo = var_df[var_df["Grupo"] == grupo]

        cards = html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fill, minmax(220px, 1fr))",
                "gap": "10px",
                "marginBottom": "16px",
            },
            children=[card_produto(row) for _, row in itens_grupo.iterrows()],
        )

        grafico = grafico_grupo(df, grupo)

        secao = html.Div(
            style={
                "background": CORES["card2"],
                "border": f"1px solid {CORES['border']}",
                "borderTop": f"2px solid {cor_grupo}",
                "borderRadius": "8px",
                "padding": "16px",
                "marginBottom": "16px",
            },
            children=[
                html.Div(
                    style={"display": "flex", "alignItems": "center", "marginBottom": "14px", "gap": "10px"},
                    children=[
                        html.Span("●", style={"color": cor_grupo, "fontSize": "16px"}),
                        html.Span(
                            grupo.upper(),
                            style={"fontWeight": "700", "fontSize": "12px", "letterSpacing": "0.1em", "color": CORES["text"]},
                        ),
                        html.Span(
                            f"{len(itens_grupo)} itens",
                            style={"fontSize": "10px", "color": CORES["muted"]},
                        ),
                    ],
                ),
                cards,
                html.Div(
                    html.Details(
                        children=[
                            html.Summary(
                                "📈 Histórico de evolução",
                                style={"cursor": "pointer", "fontSize": "11px", "color": CORES["muted"], "marginBottom": "8px"},
                            ),
                            grafico,
                        ],
                        style={"borderTop": f"1px solid {CORES['border']}", "paddingTop": "10px"},
                    )
                ),
            ],
        )
        secoes.append(secao)

    return html.Div([barra_kpi] + secoes)


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8050)
