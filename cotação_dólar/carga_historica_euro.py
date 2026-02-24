import requests
import pyodbc
from datetime import datetime

# --- CONFIGURAÇÕES ---
# Formato Mês-Dia-Ano (MM-DD-AAAA)
data_inicio = '01-01-2025' 
data_fim = '02-23-2026'

# URL específica para PERÍODO de OUTRAS MOEDAS (Euro = EUR)
url_api = (
    f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
    f"CotacaoMoedaPeriodo(moeda=@moeda,dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)?"
    f"@moeda='EUR'&@dataInicial='{data_inicio}'&@dataFinalCotacao='{data_fim}'&$top=10000&$format=json"
)

# Conexão SQL Server (Seu Servidor Atual)
dados_conexao = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=CORPORATIVOMTCS;"
    "Database=Financeiro;"
    "Trusted_Connection=yes;"
)

def realizar_carga_historica_euro():
    print("--- Iniciando Carga Histórica do EURO ---")
    print("Baixando dados do Banco Central... aguarde.")

    try:
        response = requests.get(url_api)
        response.raise_for_status()
        dados = response.json()
        lista_cotacoes = dados['value']

        total = len(lista_cotacoes)
        print(f"Foram encontrados {total} registros para importar.")

    except Exception as e:
        print(f"Erro ao baixar dados: {e}")
        return

    # Conectar ao Banco
    try:
        conn = pyodbc.connect(dados_conexao)
        cursor = conn.cursor()

        contador_inseridos = 0

        # Query de inserção segura apontando para a tabela CotacaoEuro
        query = """
        IF NOT EXISTS (SELECT 1 FROM CotacaoEuro WHERE DataCotacao = ?)
        BEGIN
            INSERT INTO CotacaoEuro (DataCotacao, ValorCompra, ValorVenda)
            VALUES (?, ?, ?)
        END
        """

        print("Gravando no Banco de Dados...")

        for item in lista_cotacoes:
            # A API retorna data hora completa, vamos converter
            data_str = item['dataHoraCotacao']
            valor_compra = item['cotacaoCompra']
            valor_venda = item['cotacaoVenda']

            # Formata a data para o padrão do SQL
            data_formatada = data_str.split(' ')[0]

            cursor.execute(query, data_formatada, data_formatada, valor_compra, valor_venda)
            contador_inseridos += 1

        conn.commit()
        print(f"--- Sucesso! Processo finalizado. ---")
        print(f"Registros processados: {total}")

    except Exception as e:
        print(f"Erro no Banco de Dados: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    realizar_carga_historica_euro()