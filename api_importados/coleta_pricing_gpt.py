import pandas as pd
from datetime import datetime
import os

# =========================
# CONFIGURAÇÃO
# =========================
CAMINHO_ARQUIVO = r"C:\Users\lsilva\OneDrive - Meridional TCS Ind e Com de Oleos S A\Arquivos\Python\importado\precos_quimicos.xlsx"

# =========================
# PRODUTOS E GRUPOS
# =========================
produtos = [
    "ACIDO BORICO",
    "ACIDO CAPRICO C10",
    "ACIDO CAPRILICO C18",
    "ACIDO OLEICO",
    "ACIDO PALMITICO (MI - EVONIK)",
    "ALCOOL CETILICO",
    "ALCOOL CETOESTEARILICO",
    "ALCOOL CETOESTEARILICO 20 EO",
    "CLORETO DE BENZILA",
    "DMAPA",
    "MIRISTATO DE ISOPROPILA",
    "MOLECULAR SIEVE 3A POWDER",
    "PALMITATO DE ISOPROPILA",
    "PEG 3350 - POLIETILENOGLICOL",
    "PEG 4000 - POLIETILENOGLICOL",
    "POLISORBATO 20",
    "POLISORBATO 60",
    "POLISORBATO 80",
    "SMCA",
    "SORBITOL 70"
]

grupos = [
    "Ácidos",
    "Ácidos",
    "Ácidos",
    "Ácidos",
    "Ácidos",
    "Álcoois",
    "Álcoois",
    "Álcoois",
    "Outros Químicos",
    "Outros Químicos",
    "Outros Químicos",
    "Outros Químicos",
    "Outros Químicos",
    "Polímeros/PEGs",
    "Polímeros/PEGs",
    "Tensoativos/Polisorbatos",
    "Tensoativos/Polisorbatos",
    "Tensoativos/Polisorbatos",
    "Outros Químicos",
    "Edulcorantes/Outros"
]

# Validação
if len(produtos) != len(grupos):
    raise ValueError("Quantidade de produtos e grupos não corresponde!")

# Mapeamento
produto_grupo = dict(zip(produtos, grupos))

# =========================
# FUNÇÃO DE PREÇO (BASE)
# =========================
def buscar_preco(produto):
    """
    Substituir futuramente por API / scraping real
    """
    base_precos = {
        "ACIDO OLEICO": 7100,
        "ACIDO PALMITICO (MI - EVONIK)": 7890,
        "ACIDO CAPRICO C10": 9468,
        "ACIDO CAPRILICO C18": 11572,
        "ACIDO BORICO": 4997,
        "ALCOOL CETILICO": 8416,
        "ALCOOL CETOESTEARILICO": 8942,
        "ALCOOL CETOESTEARILICO 20 EO": 10520,
        "CLORETO DE BENZILA": 5786,
        "DMAPA": 9731,
        "MIRISTATO DE ISOPROPILA": 13150,
        "MOLECULAR SIEVE 3A POWDER": 15780,
        "PALMITATO DE ISOPROPILA": 12624,
        "PEG 3350 - POLIETILENOGLICOL": 6838,
        "PEG 4000 - POLIETILENOGLICOL": 7153.6,
        "POLISORBATO 20": 11046,
        "POLISORBATO 60": 12098,
        "POLISORBATO 80": 13150,
        "SMCA": 9994,
        "SORBITOL 70": 3990
    }

    return base_precos.get(produto, None)

# =========================
# COLETA DE DADOS
# =========================
def coletar_dados():
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    registros = []

    for produto in produtos:
        preco = buscar_preco(produto)
        grupo = produto_grupo.get(produto, "Não definido")

        registro = {
            "Data": data_hoje,
            "Item": produto,
            "Preco": preco,
            "Unidade": "MT",
            "Moeda": "BRL",
            "Fonte": "Automatizado",
            "Grupo": grupo
        }

        registros.append(registro)

    return pd.DataFrame(registros)

# =========================
# SALVAR (APPEND + CONTROLE)
# =========================
def salvar_excel(df_novo):
    if os.path.exists(CAMINHO_ARQUIVO):
        df_existente = pd.read_excel(CAMINHO_ARQUIVO)

        # Remove duplicidade (Data + Item)
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
        df_final = df_final.drop_duplicates(subset=["Data", "Item"], keep="last")
    else:
        df_final = df_novo

    df_final.to_excel(CAMINHO_ARQUIVO, index=False)
    print(f"Arquivo atualizado com {len(df_novo)} registros novos.")

# =========================
# EXECUÇÃO
# =========================
if __name__ == "__main__":
    df = coletar_dados()
    salvar_excel(df)