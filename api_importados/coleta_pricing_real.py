import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import re
import time
import random # Importar o módulo random

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

def clean_price(price_str):
    """Limpa a string de preço e converte para float."""
    if not price_str:
        return None
    # Remove R$, espaços e converte formato brasileiro (1.234,56) para americano (1234.56)
    clean_str = re.sub(r'[^\d,]', '', price_str).replace(',', '.')
    try:
        return float(clean_str)
    except ValueError:
        return None

def extract_unit(product_title):
    """Tenta extrair a unidade de medida do título do produto."""
    units = {"kg": ["kg", "quilo", "kilo"], 
             "g": ["g", "grama"], 
             "mg": ["mg", "miligrama"],
             "L": ["L", "litro"], 
             "ml": ["ml", "mililitro"],
             "un": ["unidade", "un", "pc", "peça"],
             "ton": ["ton", "tonelada"],
             "galão": ["galão", "galoes"],
             "saco": ["saco"],
             "caixa": ["caixa"]}
    
    for unit_key, unit_aliases in units.items():
        for alias in unit_aliases:
            if re.search(r'\b' + re.escape(alias) + r'\b', product_title, re.IGNORECASE):
                return unit_key
    return None

def fetch_ml_price(item_name):
    """Busca o preço no Mercado Livre de forma simplificada e tenta extrair a unidade e moeda."""
    query = item_name.replace(" ", "-")
    url = f"https://lista.mercadolivre.com.br/{query}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Busca o primeiro item da lista de resultados
            first_item = soup.find('li', class_='ui-search-layout__item')
            if first_item:
                # Extrai o título do produto
                title_elem = first_item.find('h2', class_='ui-search-item__title')
                product_title = title_elem.get_text() if title_elem else ""
                
                # Extrai o preço
                price_whole = first_item.find('span', class_='andes-money-amount__fraction')
                price_cents = first_item.find('span', class_='andes-money-amount__cents')
                
                full_price_str = ""
                if price_whole:
                    full_price_str += price_whole.get_text()
                if price_cents:
                    full_price_str += "," + price_cents.get_text()

                price = clean_price(full_price_str)
                unit = extract_unit(product_title) or DEFAULT_UNITS.get(item_name, "unidade")
                currency = "BRL" # Mercado Livre Brasil, então a moeda é BRL
                
                if price:
                    return price, "Mercado Livre", unit, currency
    except Exception as e:
        print(f"Erro ao buscar {item_name} no Mercado Livre: {e}")
    return None, None, DEFAULT_UNITS.get(item_name, "unidade"), "BRL"

def collect_chemical_prices(items):
    """Coleta os preços dos itens usando Web Scraping real e inclui a unidade e moeda."""
    prices_data = []
    current_date = datetime.now().strftime("%Y-%m-%d")

    for item in items:
        print(f"Buscando: {item}...")
        price, source, unit, currency = fetch_ml_price(item)
        prices_data.append({
            "Data": current_date,
            "Item": item,
            "Preco": price,
            "Unidade": unit,
            "Moeda": currency,
            "Fonte": source if price else "Nao encontrado"
        })
        time.sleep(random.uniform(1, 3)) # Pequeno delay para evitar bloqueio
    return pd.DataFrame(prices_data)

if __name__ == "__main__":
    print("Iniciando a coleta de preços REAIS com unidades e moeda...")
    df_new_prices = collect_chemical_prices(CHEMICAL_ITEMS)
    
    # Caminho completo para o arquivo Excel no OneDrive do usuário
    output_dir = r"C:\Users\luisf\OneDrive - Meridional TCS Ind e Com de Oleos S A\Arquivos\Python\importado"
    output_excel_filename = os.path.join(output_dir, "historico_precos_quimicos.xlsx")

    # No ambiente sandbox, vamos salvar localmente para teste, pois o diretório do usuário não existe aqui
    if not os.path.exists(output_dir):
        print(f"Aviso: Diretorio {output_dir} nao encontrado. Salvando localmente para teste.")
        output_excel_filename = "historico_precos_quimicos.xlsx"

    if os.path.exists(output_excel_filename):
        try:
            df_historical = pd.read_excel(output_excel_filename)
            df_combined = pd.concat([df_historical, df_new_prices], ignore_index=True)
        except Exception as e:
            print(f"Erro ao ler historico: {e}. Criando novo arquivo.")
            df_combined = df_new_prices
    else:
        df_combined = df_new_prices

    # Salva o DataFrame combinado no arquivo Excel
    df_combined.to_excel(output_excel_filename, index=False)
    print(f"\nColeta concluída. Dados atualizados e salvos em {output_excel_filename}")
    print(df_combined.tail(len(CHEMICAL_ITEMS)))