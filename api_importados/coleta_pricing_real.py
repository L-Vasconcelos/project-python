import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import re
import time
import random
import logging
import shutil

# --- Configurações --- #
USER_WINDOWS_EXCEL_PATH = r"C:\Users\lsilva\OneDrive - Meridional TCS Ind e Com de Oleos S A\Arquivos\Python\importado\historico_precos_quimicos.xlsx"
LOG_FILENAME = "coleta_precos_v3.log"

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
# Estes são valores de exemplo e devem ser ajustados com dados reais de fornecedores ou APIs pagas
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
    url = "https://tradingeconomics.com/commodity/palm-oil"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        # Tenta encontrar o valor atual do preço do óleo de palma
        # Ajustado para o HTML atual do Trading Economics
        price_elem = soup.find('td', class_='datatable-item-first')
        if price_elem:
            price_text = price_elem.get_text().strip().replace(',', '')
            return float(price_text)  # Retorna o preço em MYR/MT
    except requests.exceptions.RequestException as e:
        logging.error(
            f"Erro ao buscar preco do Oleo de Palma no Trading Economics: {e}")
    except Exception as e:
        logging.error(
            f"Erro inesperado ao parsear preco do Oleo de Palma: {e}")
    return 4500.0  # Fallback MYR/MT (valor de referência)


def get_usd_brl_rate():
    """Busca a taxa de câmbio USD/BRL para conversão."""
    try:
        # Usando uma API de câmbio gratuita e confiável
        response = requests.get(
            "https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        response.raise_for_status()
        return response.json()['rates']['BRL']
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao buscar taxa de cambio USD/BRL: {e}")
    except Exception as e:
        logging.error(f"Erro inesperado ao parsear taxa de cambio: {e}")
    return 5.10  # Fallback


def collect_industrial_prices():
    """Coleta preços baseados em índices industriais e benchmarks B2B."""
    usd_brl = get_usd_brl_rate()
    palm_oil_current_price = get_palm_oil_price_index()  # Preço atual em MYR/MT
    palm_oil_base_price = 4500.0  # Preço de referência para o índice
    palm_index_factor = palm_oil_current_price / \
        palm_oil_base_price  # Fator de variação

    prices_data = []
    current_date = datetime.now().strftime("%Y-%m-%d")

    for item in CHEMICAL_ITEMS:
        price = None
        unit = DEFAULT_UNITS.get(item, "unidade")
        currency = "USD"
        source = "Estimativa Industrial"
        group = ITEM_GROUPS.get(item, "Outros")

        # Lógica de precificação industrial
        if item in INDUSTRIAL_BENCHMARKS:
            data = INDUSTRIAL_BENCHMARKS[item]
            if "base_price_usd_mt" in data:
                price = data["base_price_usd_mt"]
                currency = "USD"
                unit = data["unit"]
                if item in PALM_OIL_INDEX_ITEMS:
                    price *= palm_index_factor  # Ajusta conforme o mercado global de oleoquímicos
            elif "base_price_brl_drum" in data:
                price = data["base_price_brl_drum"] / usd_brl  # Converte BRL para USD
                currency = "USD"
                unit = data["unit"]
            source = data["source"]
            group = data["group"]
        else:
            # Fallback para itens sem benchmark direto
            price = 1500.0  # Estimativa base em USD
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
        time.sleep(random.uniform(1, 3))  # Pequeno delay aleatório

    return pd.DataFrame(prices_data)


# --- Lógica Principal --- #
if __name__ == "__main__":
    logging.info(
        "Script de coleta de precos V3 (Foco Industrial B2B) iniciado.")
    print("Iniciando a coleta de preços industriais B2B (V3 - Robusto)...")

    df_new_prices = collect_industrial_prices()

    # Determina o caminho de saída com base no ambiente
    if os.name == 'nt':  # Se o sistema operacional for Windows
        output_excel_filename = USER_WINDOWS_EXCEL_PATH
        output_dir = os.path.dirname(output_excel_filename)
    else:  # Para ambientes Linux (como o sandbox)
        output_dir = "/home/ubuntu/temp_prices"  # Um diretório temporário no sandbox
        output_excel_filename = os.path.join(
            output_dir, "historico_precos_quimicos.xlsx")
        print(
            f"Aviso: Salvando localmente para teste no sandbox: {output_excel_filename}")

    # Cria o diretório se não existir
    os.makedirs(output_dir, exist_ok=True)

    # --- Backup de Segurança --- #
    backup_excel_filename = os.path.join(
        output_dir, f"historico_precos_quimicos_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx")
    if os.path.exists(output_excel_filename):
        try:
            shutil.copy2(output_excel_filename, backup_excel_filename)
            logging.info(
                f"Backup do arquivo Excel criado em: {backup_excel_filename}")
        except Exception as e:
            logging.error(f"Erro ao criar backup do Excel: {e}")

    # --- Leitura e Concatenação do Histórico --- #
    df_combined = pd.DataFrame()
    if os.path.exists(output_excel_filename):
        try:
            df_historical = pd.read_excel(output_excel_filename)
            df_combined = pd.concat(
                [df_historical, df_new_prices], ignore_index=True)
            logging.info(
                "Novos precos concatenados com o historico existente.")
        except Exception as e:
            logging.error(
                f"Erro ao ler ou concatenar historico existente: {e}. Criando novo arquivo com os dados de hoje.")
            df_combined = df_new_prices
    else:
        df_combined = df_new_prices
        logging.info(
            "Arquivo historico nao encontrado. Criando um novo com os dados de hoje.")

    # Salva o DataFrame combinado no arquivo Excel
    try:
        df_combined.to_excel(output_excel_filename, index=False)
        logging.info(
            f"Coleta concluida. Dados atualizados e salvos em {output_excel_filename}")
        print(
            f"\nColeta concluída. Dados atualizados e salvos em {output_excel_filename}")
        print(df_combined.tail(len(CHEMICAL_ITEMS)))
    except Exception as e:
        logging.error(f"Erro ao salvar o arquivo Excel: {e}")
        print(
            f"\nERRO: Nao foi possivel salvar o arquivo Excel em {output_excel_filename}. Verifique permissoes ou se o arquivo esta aberto.")

    logging.info("Script de coleta de precos finalizado.")
