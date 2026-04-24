"""
utils.py — Funções e constantes compartilhadas entre os dashboards de pricing.
"""

import pandas as pd


# ─── CORES POR GRUPO ─────────────────────────────────────────────────────────

GRUPO_COR: dict[str, str] = {
    "Ácidos":                   "#06b6d4",
    "Álcoois":                  "#8b5cf6",
    "Outros Químicos":          "#f59e0b",
    "Polímeros/PEGs":           "#10b981",
    "Tensoativos/Polisorbatos": "#f43f5e",
    "Edulcorantes/Outros":      "#fb923c",
}


# ─── FUNÇÕES COMPARTILHADAS ───────────────────────────────────────────────────

def preco_por_kg(preco: float, unidade: str) -> tuple[float, str]:
    """Converte MT → kg (÷ 1000). Demais unidades permanecem como estão."""
    if str(unidade).upper() == "MT":
        return round(float(preco) / 1000, 4), "kg"
    return round(float(preco), 4), str(unidade)


def calcular_variacao(df: pd.DataFrame) -> pd.DataFrame:
    """
    Para cada item, retorna preço atual, anterior, variação % e variação absoluta.

    Colunas do resultado:
        Item, Preco_Atual, Unidade, Grupo, Fonte,
        Preco_Ant, Var_Pct, Var_Abs, Data_Ref, Data_Ant
    """
    if df.empty:
        return df

    datas   = sorted(df["Data"].unique())
    d_atual = datas[-1]
    d_ant   = datas[-2] if len(datas) > 1 else None

    atual = df[df["Data"] == d_atual][
        ["Item", "Preco", "Unidade", "Grupo", "Fonte"]
    ].copy()
    atual.columns = ["Item", "Preco_Atual", "Unidade", "Grupo", "Fonte"]

    if d_ant is not None:
        ant = df[df["Data"] == d_ant][["Item", "Preco"]].rename(
            columns={"Preco": "Preco_Ant"}
        )
        result = atual.merge(ant, on="Item", how="left")
    else:
        result = atual.copy()
        result["Preco_Ant"] = None

    result["Var_Pct"] = (
        (result["Preco_Atual"] - result["Preco_Ant"]) /
        result["Preco_Ant"] * 100
    ).round(2)
    result["Var_Abs"]  = (result["Preco_Atual"] - result["Preco_Ant"]).round(2)
    result["Data_Ref"] = d_atual
    result["Data_Ant"] = d_ant
    return result.sort_values(["Grupo", "Item"]).reset_index(drop=True)
