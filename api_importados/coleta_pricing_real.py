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
# Caminho completo para o arquivo Excel no OneDrive do usuário (para uso no Windows)
USER_WINDOWS_EXCEL_PATH = r"C:\Users\lsilva\OneDrive - Meridional TCS Ind e Com de Oleos S A\Arquivos\Python\importado\historico_precos_quimicos.xlsx"
LOG_FILENAME = "coleta_precos.log"

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

# Lista de User-Agents para rotação
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
]

# --- Configuração de Logging --- #
logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# --- Funções de Auxílio --- #
def clean_price(price_str):
    """Limpa a string de preço e converte para float."""
    if not price_str:
        return None
    clean_str = re.sub(r'[^\d,]', '', price_str).replace(',', '.')
    try:
        return float(clean_str)
    except ValueError:
        logging.warning(f"Nao foi possivel converter o preco '{price_str}' para float.")
        return None

def extract_unit(product_title, item_name):
    """Tenta extrair a unidade de medida do título do produto ou usa a padrao."""
    units_map = {"kg": ["kg", "quilo", "kilo"], 
                 "g": ["g", "grama"], 
                 "mg": ["mg", "miligrama"],
                 "L": ["L", "litro"], 
                 "ml": ["ml", "mililitro"],
                 "un": ["unidade", "un", "pc", "peça"],
                 "ton": ["ton", "tonelada"],
                 "galão": ["galão", "galoes"],
                 "saco": ["saco"],
                 "caixa": ["caixa"]}
    
    for unit_key, unit_aliases in units_map.items():
        for alias in unit_aliases:
            if re.search(r'\b' + re.escape(alias) + r'\b', product_title, re.IGNORECASE):
                return unit_key
    return DEFAULT_UNITS.get(item_name, "unidade")

def get_item_group(item_name):
    """Retorna o grupo do item com base no mapeamento predefinido."""
    return ITEM_GROUPS.get(item_name, "Outros")

# --- Funções de Coleta de Dados --- #
def fetch_ml_price(item_name):
    """Busca o preço no Mercado Livre e tenta extrair a unidade e moeda."""
    query = item_name.replace(" ", "-")
    url = f"https://lista.mercadolivre.com.br/{query}"
    headers = {"User-Agent": random.choice(USER_AGENTS)} # Rotação de User-Agent
    
    try:
        response = requests.get(url, headers=headers, timeout=20) # Aumentar timeout
        response.raise_for_status() # Levanta HTTPError para códigos de status ruins (4xx ou 5xx)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        first_item = soup.find('li', class_='ui-search-layout__item')
        if first_item:
            title_elem = first_item.find('h2', class_='ui-search-item__title')
            product_title = title_elem.get_text() if title_elem else ""
            
            price_whole = first_item.find('span', class_='andes-money-amount__fraction')
            price_cents = first_item.find('span', class_='andes-money-amount__cents')
            
            full_price_str = ""
            if price_whole:
                full_price_str += price_whole.get_text()
            if price_cents:
                full_price_str += "," + price_cents.get_text()

            price = clean_price(full_price_str)
            unit = extract_unit(product_title, item_name)
            currency = "BRL" # Mercado Livre Brasil, então a moeda é BRL
            
            if price:
                logging.info(f"Preco encontrado para {item_name}: {price} {currency}/{unit} na Mercado Livre.")
                return price, "Mercado Livre", unit, currency
        else:
            logging.info(f"Nenhum item encontrado para '{item_name}' no Mercado Livre.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro de requisicao ao buscar '{item_name}' no Mercado Livre: {e}")
    except Exception as e:
        logging.error(f"Erro inesperado ao buscar '{item_name}' no Mercado Livre: {e}")
        
    return None, None, DEFAULT_UNITS.get(item_name, "unidade"), "BRL"

def collect_chemical_prices(items):
    """Coleta os preços dos itens usando Web Scraping real e inclui a unidade e moeda."""
    prices_data = []
    current_date = datetime.now().strftime("%Y-%m-%d")

    for item in items:
        logging.info(f"Iniciando busca para: {item}...")
        price, source, unit, currency = fetch_ml_price(item)
        group = get_item_group(item) # Adiciona o grupo aqui
        prices_data.append({
            "Data": current_date,
            "Item": item,
            "Preco": price,
            "Unidade": unit,
            "Moeda": currency,
            "Grupo": group, # Nova coluna de grupo
            "Fonte": source if price else "Nao encontrado"
        })
        time.sleep(random.uniform(2, 5)) # Pequeno delay aleatório para evitar bloqueio
    return pd.DataFrame(prices_data)

# --- Lógica Principal --- #
if __name__ == "__main__":
    logging.info("Script de coleta de precos iniciado.")
    print("Iniciando a coleta de preços REAIS com unidades, moeda e grupo (V2 - Robusto)...")
    
    df_new_prices = collect_chemical_prices(CHEMICAL_ITEMS)
    
    # Determina o caminho de saída com base no ambiente
    if os.name == 'nt': # Se o sistema operacional for Windows
        output_excel_filename = USER_WINDOWS_EXCEL_PATH
        output_dir = os.path.dirname(output_excel_filename)
    else: # Para ambientes Linux (como o sandbox)
        output_dir = "/home/ubuntu/temp_prices" # Um diretório temporário no sandbox
        output_excel_filename = os.path.join(output_dir, "historico_precos_quimicos.xlsx")
        print(f"Aviso: Salvando localmente para teste no sandbox: {output_excel_filename}")

    # Cria o diretório se não existir
    os.makedirs(output_dir, exist_ok=True)
    
    # --- Backup de Segurança --- #
    backup_excel_filename = os.path.join(output_dir, f"historico_precos_quimicos_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx")
    if os.path.exists(output_excel_filename):
        try:
            shutil.copy2(output_excel_filename, backup_excel_filename)
            logging.info(f"Backup do arquivo Excel criado em: {backup_excel_filename}")
        except Exception as e:
            logging.error(f"Erro ao criar backup do Excel: {e}")

    # --- Leitura e Concatenação do Histórico --- #
    df_combined = pd.DataFrame()
    if os.path.exists(output_excel_filename):
        try:
            df_historical = pd.read_excel(output_excel_filename)
            df_combined = pd.concat([df_historical, df_new_prices], ignore_index=True)
            logging.info("Novos precos concatenados com o historico existente.")
        except Exception as e:
            logging.error(f"Erro ao ler ou concatenar historico existente: {e}. Criando novo arquivo com os dados de hoje.")
            df_combined = df_new_prices
    else:
        df_combined = df_new_prices
        logging.info("Arquivo historico nao encontrado. Criando um novo com os dados de hoje.")

    # Salva o DataFrame combinado no arquivo Excel
    try:
        df_combined.to_excel(output_excel_filename, index=False)
        logging.info(f"Coleta concluida. Dados atualizados e salvos em {output_excel_filename}")
        print(f"\nColeta concluída. Dados atualizados e salvos em {output_excel_filename}")
        print(df_combined.tail(len(CHEMICAL_ITEMS)))
    except Exception as e:
        logging.error(f"Erro ao salvar o arquivo Excel: {e}")
        print(f"\nERRO: Nao foi possivel salvar o arquivo Excel em {output_excel_filename}. Verifique permissoes ou se o arquivo esta aberto.")
    
    logging.info("Script de coleta de precos finalizado.")