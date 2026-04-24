import glob
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import time
import logging
import shutil
import pyodbc
from sqlalchemy import create_engine, text
import urllib

# --- Configurações --- #
USER_WINDOWS_EXCEL_PATH = os.path.join(
    os.path.expanduser("~"),
    "OneDrive - Meridional TCS Ind e Com de Oleos S A",
    "Arquivos", "Python", "importado",
    "historico_precos_quimicos.xlsx",
)
LOG_FILENAME = "coleta_precos_v3.log"

# Número máximo de backups do Excel a manter no diretório
MAX_BACKUPS = 5

# --- Configurações SQL Server --- #
SQL_SERVER   = r"CORPORATIVOMTCS"
SQL_DATABASE = "historico_precos_quimicos"
SQL_TABLE    = "historico_precos_quimicos"
# Autenticação Windows (Trusted Connection = True) — sem usuário/senha
SQL_USE_WINDOWS_AUTH = True
# Autenticação SQL Server — preencha somente se SQL_USE_WINDOWS_AUTH = False
SQL_USER     = ""
SQL_PASSWORD = ""

# Lista de itens fornecida pelo usuário
CHEMICAL_ITEMS = [
    "ACIDO BORICO", "ACIDO CAPRICO C10", "ACIDO CAPRILICO C18", "ACIDO OLEICO",
    "ACIDO PALMITICO (MI - EVONIK)", "ALCOOL CETILICO", "ALCOOL CETOESTEARILICO",
    "ALCOOL CETOESTEARILICO 20 EO", "CLORETO DE BENZILA", "DMAPA",
    "MIRISTATO DE ISOPROPILA", "MOLECULAR SIEVE 3A POWDER", "PALMITATO DE ISOPROPILA",
    "PEG 3350 - POLIETILENOGLICOL", "PEG 4000 - POLIETILENOGLICOL", "POLISORBATO 20",
    "POLISORBATO 60", "POLISORBATO 80", "SMCA", "SORBITOL 70"
]

# Dicionário de unidades padrão para fallback, se não for encontrada no scraping
DEFAULT_UNITS = {
    "ACIDO BORICO": "kg",
    "ACIDO CAPRICO C10": "kg",
    "ACIDO CAPRILICO C18": "kg",
    "ACIDO OLEICO": "L",
    "ACIDO PALMITICO (MI - EVONIK)": "kg",
    "ALCOOL CETILICO": "kg",
    "ALCOOL CETOESTEARILICO": "kg",
    "ALCOOL CETOESTEARILICO 20 EO": "kg",
    "CLORETO DE BENZILA": "L",
    "DMAPA": "L",
    "MIRISTATO DE ISOPROPILA": "L",
    "MOLECULAR SIEVE 3A POWDER": "kg",
    "PALMITATO DE ISOPROPILA": "L",
    "PEG 3350 - POLIETILENOGLICOL": "kg",
    "PEG 4000 - POLIETILENOGLICOL": "kg",
    "POLISORBATO 20": "L",
    "POLISORBATO 60": "L",
    "POLISORBATO 80": "L",
    "SMCA": "kg",
    "SORBITOL 70": "L"
}

# Mapeamento de itens para grupos
ITEM_GROUPS = {
    "ACIDO BORICO": "Ácidos",
    "ACIDO CAPRICO C10": "Ácidos",
    "ACIDO CAPRILICO C18": "Ácidos",
    "ACIDO OLEICO": "Ácidos",
    "ACIDO PALMITICO (MI - EVONIK)": "Ácidos",
    "ALCOOL CETILICO": "Álcoois",
    "ALCOOL CETOESTEARILICO": "Álcoois",
    "ALCOOL CETOESTEARILICO 20 EO": "Álcoois",
    "CLORETO DE BENZILA": "Outros Químicos",
    "DMAPA": "Outros Químicos",
    "MIRISTATO DE ISOPROPILA": "Outros Químicos",
    "MOLECULAR SIEVE 3A POWDER": "Outros Químicos",
    "PALMITATO DE ISOPROPILA": "Outros Químicos",
    "PEG 3350 - POLIETILENOGLICOL": "Polímeros/PEGs",
    "PEG 4000 - POLIETILENOGLICOL": "Polímeros/PEGs",
    "POLISORBATO 20": "Tensoativos/Polisorbatos",
    "POLISORBATO 60": "Tensoativos/Polisorbatos",
    "POLISORBATO 80": "Tensoativos/Polisorbatos",
    "SMCA": "Outros Químicos",
    "SORBITOL 70": "Edulcorantes/Outros"
}

# Mapeamento Industrial B2B (Foco em Tonelada ou Tambor)
# Preços de referência (Benchmarks) baseados em pesquisa de mercado mar/2026
INDUSTRIAL_BENCHMARKS = {
    "ACIDO BORICO": {"base_price_usd_mt": 950.0, "source": "IMARC/BusinessAnalytiq", "unit": "MT", "group": "Ácidos"},
    "ACIDO CAPRICO C10": {"base_price_usd_mt": 1800.0, "source": "Estimativa (Oleoquímico)", "unit": "MT", "group": "Ácidos"},
    "ACIDO CAPRILICO C18": {"base_price_usd_mt": 2200.0, "source": "Estimativa (Oleoquímico)", "unit": "MT", "group": "Ácidos"},
    "ACIDO OLEICO": {"base_price_usd_mt": 1350.0, "source": "Trading Economics (Palm Oil Index)", "unit": "MT", "group": "Ácidos"},
    "ACIDO PALMITICO (MI - EVONIK)": {"base_price_usd_mt": 1500.0, "source": "Estimativa (Oleoquímico)", "unit": "MT", "group": "Ácidos"},
    "ALCOOL CETILICO": {"base_price_usd_mt": 1600.0, "source": "Estimativa (Oleoquímico)", "unit": "MT", "group": "Álcoois"},
    "ALCOOL CETOESTEARILICO": {"base_price_usd_mt": 1700.0, "source": "Estimativa (Oleoquímico)", "unit": "MT", "group": "Álcoois"},
    "ALCOOL CETOESTEARILICO 20 EO": {"base_price_usd_mt": 2000.0, "source": "Estimativa (Oleoquímico)", "unit": "MT", "group": "Álcoois"},
    "CLORETO DE BENZILA": {"base_price_usd_mt": 1100.0, "source": "Estimativa", "unit": "MT", "group": "Outros Químicos"},
    "DMAPA": {"base_price_usd_mt": 1850.0, "source": "ChemAnalyst (Trend)", "unit": "MT", "group": "Outros Químicos"},
    "MIRISTATO DE ISOPROPILA": {"base_price_usd_mt": 2500.0, "source": "Estimativa", "unit": "MT", "group": "Outros Químicos"},
    "MOLECULAR SIEVE 3A POWDER": {"base_price_usd_mt": 3000.0, "source": "Estimativa", "unit": "MT", "group": "Outros Químicos"},
    "PALMITATO DE ISOPROPILA": {"base_price_usd_mt": 2400.0, "source": "Estimativa", "unit": "MT", "group": "Outros Químicos"},
    "PEG 3350 - POLIETILENOGLICOL": {"base_price_usd_mt": 1300.0, "source": "ChemAnalyst", "unit": "MT", "group": "Polímeros/PEGs"},
    "PEG 4000 - POLIETILENOGLICOL": {"base_price_usd_mt": 1360.0, "source": "ChemAnalyst", "unit": "MT", "group": "Polímeros/PEGs"},
    "POLISORBATO 20": {"base_price_usd_mt": 2100.0, "source": "Estimativa (Tensoativo)", "unit": "MT", "group": "Tensoativos/Polisorbatos"},
    "POLISORBATO 60": {"base_price_usd_mt": 2300.0, "source": "Estimativa (Tensoativo)", "unit": "MT", "group": "Tensoativos/Polisorbatos"},
    "POLISORBATO 80": {"base_price_usd_mt": 2500.0, "source": "Estimativa (Tensoativo)", "unit": "MT", "group": "Tensoativos/Polisorbatos"},
    "SMCA": {"base_price_usd_mt": 1900.0, "source": "Estimativa", "unit": "MT", "group": "Outros Químicos"},
    "SORBITOL 70": {"base_price_brl_drum": 3990.0, "source": "Quimisul/B2B", "unit": "Drum 300kg", "group": "Edulcorantes/Outros"},
}

# Itens que seguem o índice de Óleo de Palma (Oleoquímicos)
PALM_OIL_INDEX_ITEMS = [
    "ACIDO CAPRICO C10", "ACIDO CAPRILICO C18", "ACIDO OLEICO",
    "ACIDO PALMITICO (MI - EVONIK)", "ALCOOL CETILICO", "ALCOOL CETOESTEARILICO",
    "ALCOOL CETOESTEARILICO 20 EO", "MIRISTATO DE ISOPROPILA", "PALMITATO DE ISOPROPILA"
]

# --- Configuração de Logging --- #
logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")


# --- Funções de Auxílio --- #

def get_palm_oil_price_index():
    """Busca o preço do Óleo de Palma no Trading Economics como indexador para oleoquímicos."""
    FALLBACK = 4500.0
    url = "https://tradingeconomics.com/commodity/palm-oil"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        price_elem = soup.find('td', class_='datatable-item-first')
        if price_elem:
            price_text = price_elem.get_text().strip().replace(',', '')
            return float(price_text)
        logging.warning("Seletor 'datatable-item-first' não encontrado na página. Usando fallback.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao buscar preco do Oleo de Palma no Trading Economics: {e}")
    except Exception as e:
        logging.error(f"Erro inesperado ao parsear preco do Oleo de Palma: {e}")

    logging.warning(f"Usando valor fallback para Óleo de Palma: {FALLBACK} MYR/MT")
    return FALLBACK


def get_usd_brl_rate():
    """Busca a taxa de câmbio USD/BRL para conversão."""
    FALLBACK = 5.10
    try:
        response = requests.get(
            "https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        response.raise_for_status()
        return response.json()['rates']['BRL']
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao buscar taxa de cambio USD/BRL: {e}")
    except Exception as e:
        logging.error(f"Erro inesperado ao parsear taxa de cambio: {e}")

    logging.warning(f"Usando valor fallback para USD/BRL: {FALLBACK}")
    return FALLBACK


def collect_industrial_prices():
    """Coleta preços baseados em índices industriais e benchmarks B2B."""
    usd_brl = get_usd_brl_rate()
    palm_oil_current_price = get_palm_oil_price_index()
    palm_oil_base_price = 4500.0
    palm_index_factor = palm_oil_current_price / palm_oil_base_price

    prices_data = []
    current_date = datetime.now().strftime("%Y-%m-%d")

    for item in CHEMICAL_ITEMS:
        price = None
        unit = DEFAULT_UNITS.get(item, "unidade")
        currency = "USD"
        source = "Estimativa Industrial"
        group = ITEM_GROUPS.get(item, "Outros")

        if item in INDUSTRIAL_BENCHMARKS:
            data = INDUSTRIAL_BENCHMARKS[item]
            if "base_price_usd_mt" in data:
                price = data["base_price_usd_mt"]
                currency = "USD"
                unit = data["unit"]
                if item in PALM_OIL_INDEX_ITEMS:
                    price *= palm_index_factor
            elif "base_price_brl_drum" in data:
                price = data["base_price_brl_drum"] / usd_brl
                currency = "USD"
                unit = data["unit"]
            source = data["source"]
            group = data["group"]
        else:
            price = 1500.0
            currency = "USD"
            unit = DEFAULT_UNITS.get(item, "unidade")
            source = "Estimativa Generica"
            group = ITEM_GROUPS.get(item, "Outros")

        prices_data.append({
            "Data": current_date,
            "Item": item,
            "Preco": round(price, 2) if price else None,
            "Unidade": unit,
            "Moeda": currency,
            "Grupo": group,
            "Fonte": source
        })
        # Sem sleep: cálculo local, nenhuma requisição de rede neste loop

    return pd.DataFrame(prices_data)


# --- SQL Server --- #

def get_sqlserver_engine():
    """Cria e retorna um engine SQLAlchemy para o SQL Server."""
    if SQL_USE_WINDOWS_AUTH:
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={SQL_SERVER};"
            f"DATABASE={SQL_DATABASE};"
            f"Trusted_Connection=yes;"
        )
    else:
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={SQL_SERVER};"
            f"DATABASE={SQL_DATABASE};"
            f"UID={SQL_USER};"
            f"PWD={SQL_PASSWORD};"
        )
    params = urllib.parse.quote_plus(conn_str)
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}", fast_executemany=True)
    return engine


def ensure_table_exists(engine):
    """Cria a tabela no SQL Server se ela ainda não existir."""
    ddl = f"""
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME = '{SQL_TABLE}'
    )
    BEGIN
        CREATE TABLE [{SQL_TABLE}] (
            Id          INT IDENTITY(1,1) PRIMARY KEY,
            Data        DATE            NOT NULL,
            Item        NVARCHAR(150)   NOT NULL,
            Preco       FLOAT           NULL,
            Unidade     NVARCHAR(50)    NULL,
            Moeda       NVARCHAR(10)    NULL,
            Grupo       NVARCHAR(100)   NULL,
            Fonte       NVARCHAR(255)   NULL,
            DataInsercao DATETIME       NOT NULL DEFAULT GETDATE(),
            CONSTRAINT UQ_{SQL_TABLE}_Data_Item UNIQUE (Data, Item)
        )
    END
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))
    logging.info(f"Tabela [{SQL_TABLE}] verificada/criada com sucesso.")


def upsert_to_sqlserver(df: pd.DataFrame, engine):
    """
    Insere novos registros no SQL Server.
    Ignora linhas que já existam para o mesmo par (Data, Item) — sem duplicatas.
    """
    if df.empty:
        logging.warning("DataFrame vazio, nada a inserir no SQL Server.")
        return

    rows_inserted = 0
    rows_skipped  = 0

    insert_sql = text(f"""
        IF NOT EXISTS (
            SELECT 1 FROM [{SQL_TABLE}]
            WHERE Data = :Data AND Item = :Item
        )
        INSERT INTO [{SQL_TABLE}] (Data, Item, Preco, Unidade, Moeda, Grupo, Fonte)
        VALUES (:Data, :Item, :Preco, :Unidade, :Moeda, :Grupo, :Fonte)
    """)

    with engine.begin() as conn:
        for _, row in df.iterrows():
            result = conn.execute(insert_sql, {
                "Data":    row["Data"],
                "Item":    row["Item"],
                "Preco":   row["Preco"],
                "Unidade": row["Unidade"],
                "Moeda":   row["Moeda"],
                "Grupo":   row["Grupo"],
                "Fonte":   row["Fonte"],
            })
            if result.rowcount > 0:
                rows_inserted += 1
            else:
                rows_skipped += 1

    logging.info(f"SQL Server: {rows_inserted} registros inseridos, {rows_skipped} já existiam (ignorados).")
    print(f"SQL Server: {rows_inserted} registros inseridos, {rows_skipped} já existiam.")


def _limpar_backups_antigos(output_dir: str):
    """Mantém apenas os últimos MAX_BACKUPS arquivos de backup no diretório."""
    padrao = os.path.join(output_dir, "historico_precos_quimicos_backup_*.xlsx")
    backups = sorted(glob.glob(padrao))
    while len(backups) > MAX_BACKUPS:
        antigo = backups.pop(0)
        try:
            os.remove(antigo)
            logging.info(f"Backup antigo removido: {antigo}")
        except Exception as e:
            logging.warning(f"Não foi possível remover backup antigo {antigo}: {e}")


# --- Lógica Principal --- #
if __name__ == "__main__":
    logging.info("Script de coleta de precos V3 (Foco Industrial B2B) iniciado.")
    print("Iniciando a coleta de preços industriais B2B (V3 - Robusto)...")

    df_new_prices = collect_industrial_prices()

    # Determina o caminho de saída com base no ambiente
    if os.name == 'nt':
        output_excel_filename = USER_WINDOWS_EXCEL_PATH
        output_dir = os.path.dirname(output_excel_filename)
    else:
        output_dir = "/home/ubuntu/temp_prices"
        output_excel_filename = os.path.join(output_dir, "historico_precos_quimicos.xlsx")
        print(f"Aviso: Salvando localmente para teste no sandbox: {output_excel_filename}")

    os.makedirs(output_dir, exist_ok=True)

    # --- Backup de Segurança --- #
    if os.path.exists(output_excel_filename):
        backup_excel_filename = os.path.join(
            output_dir,
            f"historico_precos_quimicos_backup_{datetime.now().strftime('%Y%m%d')}.xlsx"
        )
        try:
            shutil.copy2(output_excel_filename, backup_excel_filename)
            logging.info(f"Backup criado em: {backup_excel_filename}")
        except Exception as e:
            logging.error(f"Erro ao criar backup do Excel: {e}")

        _limpar_backups_antigos(output_dir)

    # --- Leitura e Concatenação do Histórico --- #
    df_combined = pd.DataFrame()
    if os.path.exists(output_excel_filename):
        try:
            df_historical = pd.read_excel(output_excel_filename)
            df_combined = pd.concat([df_historical, df_new_prices], ignore_index=True)
            logging.info("Novos precos concatenados com o historico existente.")
        except Exception as e:
            logging.error(
                f"Erro ao ler ou concatenar historico existente: {e}. "
                "Criando novo arquivo com os dados de hoje."
            )
            df_combined = df_new_prices
    else:
        df_combined = df_new_prices
        logging.info("Arquivo historico nao encontrado. Criando um novo com os dados de hoje.")

    # Remove duplicatas mantendo o último registro de cada (Data, Item)
    df_combined = df_combined.drop_duplicates(subset=["Data", "Item"], keep="last")

    # Salva o DataFrame combinado no arquivo Excel
    try:
        df_combined.to_excel(output_excel_filename, index=False)
        logging.info(f"Coleta concluida. Dados salvos em {output_excel_filename}")
        print(f"\nColeta concluída. Dados salvos em {output_excel_filename}")
        print(df_combined.tail(len(CHEMICAL_ITEMS)))
    except Exception as e:
        logging.error(f"Erro ao salvar o arquivo Excel: {e}")
        print(
            f"\nERRO: Nao foi possivel salvar o arquivo Excel em {output_excel_filename}. "
            "Verifique permissoes ou se o arquivo esta aberto."
        )

    # --- Gravação no SQL Server --- #
    try:
        engine = get_sqlserver_engine()
        ensure_table_exists(engine)
        upsert_to_sqlserver(df_new_prices, engine)
    except Exception as e:
        logging.error(f"Erro ao gravar no SQL Server: {e}")
        print(f"\nAVISO: Nao foi possivel gravar no SQL Server: {e}")

    logging.info("Script de coleta de precos finalizado.")
