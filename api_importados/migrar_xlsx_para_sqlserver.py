"""
Migração única: lê o histórico do Excel e grava no SQL Server.
Reutiliza as configurações e funções de coleta_pricing_real.py.
Execute uma única vez após criar o banco.
"""

import pandas as pd
import logging
from coleta_pricing_real import (
    SQL_SERVER, SQL_DATABASE, SQL_TABLE,
    USER_WINDOWS_EXCEL_PATH,
    get_sqlserver_engine,
    ensure_table_exists,
    upsert_to_sqlserver,
    LOG_FILENAME,
)

logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

EXCEL_PATH = USER_WINDOWS_EXCEL_PATH  # altere aqui se quiser outro arquivo

if __name__ == "__main__":
    print(f"Lendo Excel: {EXCEL_PATH}")
    try:
        df = pd.read_excel(EXCEL_PATH)
    except FileNotFoundError:
        print(f"ERRO: Arquivo não encontrado: {EXCEL_PATH}")
        raise

    # Garante que a coluna Data está como string no formato YYYY-MM-DD
    df["Data"] = pd.to_datetime(df["Data"]).dt.strftime("%Y-%m-%d")

    print(f"{len(df)} registros encontrados no Excel.")
    print(df.head())

    print(f"\nConectando ao SQL Server: {SQL_SERVER} / {SQL_DATABASE}")
    engine = get_sqlserver_engine()
    ensure_table_exists(engine)

    print("Iniciando migração...")
    upsert_to_sqlserver(df, engine)
    print("Migração concluída.")
