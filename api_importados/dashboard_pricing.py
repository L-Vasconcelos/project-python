"""
Dashboard de Pricing - Importados
Fonte: SQL Server (CORPORATIVOMTCS · historico_precos_quimicos)
Acesso: http://localhost:8051
Layout fixo 1920×1080 — sem scroll, otimizado para print/screenshot
"""

import urllib
import pandas as pd
from dash import Dash, dcc, html, Input, Output
from sqlalchemy import create_engine, text
from datetime import datetime

# ── Conexão SQL Server ─────────────────────────────────────────────────────────
SQL_SERVER   = r"CORPORATIVOMTCS"
SQL_DATABASE = "historico_precos_quimicos"
SQL_TABLE    = "historico_precos_quimicos"

REFRESH_MS = 60_000  # 60 segundos

# ── Paleta ─────────────────────────────────────────────────────────────────────
BG      = "#0a0e1a"
CARD    = "#111827"
CARD2   = "#0f172a"
BORDER  = "#1e2d45"
TEXT    = "#e2e8f0"
MUTED   = "#4b5a6e"
MUTED2  = "#64748b"
UP      = "#10b981"
DOWN    = "#f43f5e"
NEUTRAL = "#64748b"
ACCENT  = "#06b6d4"

GRUPO_COR = {
    "Ácidos":                   "#06b6d4",
    "Álcoois":                  "#8b5cf6",
    "Outros Químicos":          "#f59e0b",
    "Polímeros/PEGs":           "#10b981",
    "Tensoativos/Polisorbatos": "#f43f5e",
    "Edulcorantes/Outros":      "#fb923c",
}

FONT = "'Fira Code', 'JetBrains Mono', 'Cascadia Code', monospace"

# ── Helpers SQL ────────────────────────────────────────────────────────────────

def _engine():
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DATABASE};"
        f"Trusted_Connection=yes;"
    )
    params = urllib.parse.quote_plus(conn_str)
    return create_engine(f"mssql+pyodbc:///?odbc_connect={params}", fast_executemany=True)


def carregar_dados():
    """Retorna (df, status_str). Em caso de erro, df vazio e msg de erro."""
    try:
        engine = _engine()
        query = text(f"""
            SELECT Data, Item, Preco, Unidade, Moeda, Grupo, Fonte
            FROM [{SQL_TABLE}]
            ORDER BY Data, Grupo, Item
        """)
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        df["Data"] = pd.to_datetime(df["Data"])
        df = df.sort_values("Data")
        return df, "SQL Server · OK"
    except Exception as exc:
        return pd.DataFrame(), f"ERRO: {exc}"


# ── Lógica de negócio ──────────────────────────────────────────────────────────

def preco_por_kg(preco, unidade):
    """MT → USD/kg. Drum 300kg → mantém como está."""
    if str(unidade).upper() == "MT":
        return round(preco / 1000, 4), "kg"
    return round(preco, 4), unidade


def calcular_variacao(df):
    """Retorna df com Preco_Atual, Preco_Ant, Var_Pct, Var_Abs para a última data."""
    if df.empty:
        return df
    datas = sorted(df["Data"].unique())
    d_atual = datas[-1]
    d_ant   = datas[-2] if len(datas) > 1 else None

    atual = df[df["Data"] == d_atual][["Item", "Preco", "Unidade", "Grupo", "Fonte"]].copy()
    atual.columns = ["Item", "Preco_Atual", "Unidade", "Grupo", "Fonte"]

    if d_ant is not None:
        ant = df[df["Data"] == d_ant][["Item", "Preco"]].rename(columns={"Preco": "Preco_Ant"})
        result = atual.merge(ant, on="Item", how="left")
    else:
        result = atual.copy()
        result["Preco_Ant"] = None

    result["Var_Pct"] = (
        (result["Preco_Atual"] - result["Preco_Ant"]) / result["Preco_Ant"] * 100
    ).round(2)
    result["Var_Abs"] = (result["Preco_Atual"] - result["Preco_Ant"]).round(2)
    result["Data_Ref"] = d_atual
    return result.sort_values(["Grupo", "Item"])


# ── Componentes UI ─────────────────────────────────────────────────────────────

def _cell(content, width=None, align="left", bold=False, color=TEXT, size="11px", mono=False, extra=None):
    style = {
        "padding": "0 10px",
        "color": color,
        "fontSize": size,
        "fontWeight": "700" if bold else "400",
        "fontFamily": FONT if mono else FONT,
        "textAlign": align,
        "whiteSpace": "nowrap",
        "overflow": "hidden",
        "textOverflow": "ellipsis",
        "lineHeight": "30px",
        "height": "30px",
    }
    if width:
        style["width"] = width
        style["minWidth"] = width
        style["maxWidth"] = width
    if extra:
        style.update(extra)
    return html.Td(content, style=style)


def variacao_badge(var_pct):
    if var_pct is None or (isinstance(var_pct, float) and pd.isna(var_pct)):
        return html.Span("—", style={"color": NEUTRAL, "fontWeight": "600"})
    if var_pct > 0:
        return html.Span(f"▲ +{var_pct:.2f}%", style={"color": UP, "fontWeight": "700"})
    if var_pct < 0:
        return html.Span(f"▼ {var_pct:.2f}%", style={"color": DOWN, "fontWeight": "700"})
    return html.Span("— 0.00%", style={"color": NEUTRAL, "fontWeight": "600"})


def grupo_header_row(grupo, n_itens):
    cor = GRUPO_COR.get(grupo, ACCENT)
    return html.Tr(
        style={
            "background": CARD2,
            "borderLeft": f"3px solid {cor}",
            "borderBottom": f"1px solid {BORDER}",
        },
        children=[
            html.Td(
                colSpan=5,
                style={
                    "padding": "0 12px",
                    "height": "26px",
                    "lineHeight": "26px",
                    "fontSize": "10px",
                    "fontWeight": "700",
                    "letterSpacing": "0.12em",
                    "color": cor,
                    "fontFamily": FONT,
                },
                children=[
                    html.Span(grupo.upper()),
                    html.Span(
                        f"  ·  {n_itens} ITENS",
                        style={"color": MUTED2, "fontWeight": "400", "fontSize": "9px"},
                    ),
                ],
            )
        ],
    )


def produto_row(row, i):
    preco, unid  = preco_por_kg(row["Preco_Atual"], row["Unidade"])
    cor_grupo    = GRUPO_COR.get(row["Grupo"], ACCENT)
    var_badge    = variacao_badge(row.get("Var_Pct"))
    stripe       = CARD if i % 2 == 0 else "#0d1421"

    return html.Tr(
        style={
            "background": stripe,
            "borderBottom": f"1px solid {BORDER}",
            "transition": "background 150ms",
            "borderLeft": f"2px solid {cor_grupo}22",
        },
        children=[
            _cell(
                html.Span(
                    row["Grupo"],
                    style={
                        "background": f"{cor_grupo}18",
                        "color": cor_grupo,
                        "borderRadius": "3px",
                        "padding": "1px 6px",
                        "fontSize": "9px",
                        "fontWeight": "700",
                        "letterSpacing": "0.06em",
                    },
                ),
                width="180px",
            ),
            _cell(row["Item"], width="240px", bold=True, color=TEXT, size="11px"),
            _cell(
                f"${preco:,.4f} / {unid}",
                width="140px",
                align="right",
                bold=True,
                color="#93c5fd",
                mono=True,
            ),
            _cell(var_badge, width="120px", align="center"),
            _cell(
                row.get("Fonte", "—") or "—",
                color=MUTED2,
                size="9px",
                extra={"maxWidth": "220px"},
            ),
        ],
    )


def tabela_header():
    th_style = {
        "padding": "0 10px",
        "height": "28px",
        "lineHeight": "28px",
        "fontSize": "9px",
        "fontWeight": "700",
        "letterSpacing": "0.12em",
        "color": MUTED2,
        "textTransform": "uppercase",
        "fontFamily": FONT,
        "borderBottom": f"1px solid {BORDER}",
        "background": "#090d17",
        "position": "sticky",
        "top": "0",
        "zIndex": "10",
    }
    cols = [
        ("GRUPO",      "180px", "left"),
        ("ITEM",       "240px", "left"),
        ("PREÇO USD",  "140px", "right"),
        ("VARIAÇÃO",   "120px", "center"),
        ("FONTE",      None,    "left"),
    ]
    return html.Thead(
        html.Tr([
            html.Th(
                label,
                style={**th_style, "width": w or "auto", "textAlign": align},
            )
            for label, w, align in cols
        ])
    )


def kpi_pill(label, valor, cor):
    return html.Div(
        style={
            "display":       "flex",
            "flexDirection": "column",
            "alignItems":    "center",
            "justifyContent":"center",
            "background":    CARD,
            "border":        f"1px solid {BORDER}",
            "borderTop":     f"2px solid {cor}",
            "borderRadius":  "6px",
            "padding":       "6px 20px",
            "minWidth":      "90px",
            "gap":           "2px",
        },
        children=[
            html.Div(
                str(valor),
                style={
                    "fontSize":   "22px",
                    "fontWeight": "800",
                    "color":      cor,
                    "fontFamily": FONT,
                    "lineHeight": "1",
                },
            ),
            html.Div(
                label,
                style={
                    "fontSize":      "8px",
                    "color":         MUTED2,
                    "letterSpacing": "0.1em",
                    "textTransform": "uppercase",
                    "fontFamily":    FONT,
                },
            ),
        ],
    )


# ── App ────────────────────────────────────────────────────────────────────────

app = Dash(
    __name__,
    title="Pricing · Importados",
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&display=swap"
    ],
)

app.index_string = """<!DOCTYPE html>
<html>
<head>
{%metas%}
<title>{%title%}</title>
{%css%}
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html, body, #react-entry-point, #_dash-app-content {
    height: 100%; width: 100%; overflow: hidden;
  }
  body { background: """ + BG + """; }
  ::-webkit-scrollbar { display: none; }
  table { border-collapse: collapse; width: 100%; }
  tr:hover { background: #1a2235 !important; }
  @media print {
    body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  }
</style>
</head>
<body>
{%app_entry%}
<footer>{%config%}{%scripts%}{%renderer%}</footer>
</body>
</html>"""

app.layout = html.Div(
    style={
        "background":  BG,
        "height":      "100vh",
        "width":       "100vw",
        "overflow":    "hidden",
        "display":     "flex",
        "flexDirection":"column",
        "fontFamily":  FONT,
        "color":       TEXT,
    },
    children=[
        dcc.Interval(id="tick", interval=REFRESH_MS, n_intervals=0),

        # ── HEADER ──────────────────────────────────────────────────────────
        html.Div(
            style={
                "height":         "40px",
                "minHeight":      "40px",
                "background":     CARD,
                "borderBottom":   f"1px solid {BORDER}",
                "display":        "flex",
                "alignItems":     "center",
                "justifyContent": "space-between",
                "padding":        "0 20px",
                "flexShrink":     "0",
            },
            children=[
                html.Div(
                    style={"display": "flex", "alignItems": "center", "gap": "10px"},
                    children=[
                        html.Div(
                            style={
                                "width": "8px", "height": "8px",
                                "borderRadius": "50%",
                                "background": ACCENT,
                                "boxShadow": f"0 0 6px {ACCENT}",
                            }
                        ),
                        html.Span(
                            "PRICING",
                            style={"fontWeight": "800", "fontSize": "13px", "letterSpacing": "0.18em"},
                        ),
                        html.Span(
                            "· IMPORTADOS",
                            style={"color": MUTED2, "fontSize": "11px", "letterSpacing": "0.08em"},
                        ),
                    ],
                ),
                html.Div(
                    id="header-meta",
                    style={"fontSize": "10px", "color": MUTED2, "letterSpacing": "0.05em"},
                ),
            ],
        ),

        # ── KPI ROW ─────────────────────────────────────────────────────────
        html.Div(
            id="kpi-row",
            style={
                "display":    "flex",
                "alignItems": "center",
                "gap":        "10px",
                "padding":    "10px 20px",
                "flexShrink": "0",
                "height":     "72px",
                "minHeight":  "72px",
                "borderBottom": f"1px solid {BORDER}",
            },
        ),

        # ── TABLE AREA ──────────────────────────────────────────────────────
        html.Div(
            style={
                "flex":       "1",
                "overflow":   "hidden",
                "padding":    "0 20px",
                "display":    "flex",
                "flexDirection": "column",
            },
            children=[
                html.Div(
                    style={"flex": "1", "overflowY": "auto", "overflowX": "hidden"},
                    children=[
                        html.Table(
                            id="tabela-precos",
                            children=[tabela_header()],
                        )
                    ],
                )
            ],
        ),

        # ── FOOTER ──────────────────────────────────────────────────────────
        html.Div(
            id="footer-bar",
            style={
                "height":         "30px",
                "minHeight":      "30px",
                "background":     CARD,
                "borderTop":      f"1px solid {BORDER}",
                "display":        "flex",
                "alignItems":     "center",
                "justifyContent": "space-between",
                "padding":        "0 20px",
                "flexShrink":     "0",
                "fontSize":       "9px",
                "color":          MUTED,
                "letterSpacing":  "0.06em",
            },
        ),
    ],
)


# ── Callbacks ──────────────────────────────────────────────────────────────────

@app.callback(
    Output("header-meta",   "children"),
    Output("kpi-row",       "children"),
    Output("tabela-precos", "children"),
    Output("footer-bar",    "children"),
    Input("tick",           "n_intervals"),
)
def atualizar(n):
    agora = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
    df, status = carregar_dados()

    # ── sem dados ──────────────────────────────────────────────────────────
    if df.empty:
        meta    = html.Span(f"ERRO  ·  {agora}", style={"color": DOWN})
        kpis    = kpi_pill("STATUS", "OFFLINE", DOWN)
        tabela  = [tabela_header(), html.Tbody(html.Tr(html.Td(
            status, colSpan=5,
            style={"color": DOWN, "padding": "20px", "fontSize": "11px", "fontFamily": FONT},
        )))]
        footer  = [html.Span(status), html.Span(agora)]
        return meta, kpis, tabela, footer

    var_df = calcular_variacao(df)
    grupos = list(var_df["Grupo"].unique())

    # ── KPIs ───────────────────────────────────────────────────────────────
    n_alta   = int((var_df["Var_Pct"] > 0).sum())
    n_baixa  = int((var_df["Var_Pct"] < 0).sum())
    n_estavel= int((var_df["Var_Pct"] == 0).sum())
    n_sem_ref= int(var_df["Var_Pct"].isna().sum())
    d_ref    = pd.to_datetime(var_df["Data_Ref"].iloc[0]).strftime("%d/%m/%Y")

    kpis = [
        kpi_pill("PRODUTOS",    len(var_df),  TEXT),
        kpi_pill("EM ALTA",     n_alta,       UP),
        kpi_pill("EM BAIXA",    n_baixa,      DOWN),
        kpi_pill("ESTÁVEIS",    n_estavel,    NEUTRAL),
        kpi_pill("SEM REF.",    n_sem_ref,    MUTED2),
        html.Div(style={"flex": "1"}),
        html.Div(
            style={
                "display":        "flex",
                "flexDirection":  "column",
                "alignItems":     "flex-end",
                "gap":            "3px",
            },
            children=[
                html.Span(
                    f"Referência  {d_ref}",
                    style={"fontSize": "11px", "fontWeight": "700", "color": ACCENT},
                ),
                html.Span(
                    f"{len(grupos)} grupos  ·  {len(df['Data'].unique())} coletas",
                    style={"fontSize": "9px", "color": MUTED2},
                ),
            ],
        ),
    ]

    # ── Tabela ─────────────────────────────────────────────────────────────
    tbody_rows = []
    i = 0
    for grupo in grupos:
        itens_grupo = var_df[var_df["Grupo"] == grupo]
        tbody_rows.append(grupo_header_row(grupo, len(itens_grupo)))
        for _, row in itens_grupo.iterrows():
            tbody_rows.append(produto_row(row, i))
            i += 1

    tabela = [tabela_header(), html.Tbody(tbody_rows)]

    # ── Footer ─────────────────────────────────────────────────────────────
    footer = [
        html.Span(f"FONTE  ·  {SQL_SERVER} / {SQL_DATABASE} · {status}"),
        html.Span(f"ATUALIZADO  {agora}"),
    ]

    # ── Header meta ────────────────────────────────────────────────────────
    meta = html.Span(
        f"REF {d_ref}  ·  SQL SERVER  ·  {agora}",
        style={"color": MUTED2},
    )

    return meta, kpis, tabela, footer


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8051)
