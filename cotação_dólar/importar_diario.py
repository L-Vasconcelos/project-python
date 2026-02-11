import requests
import pyodbc
from datetime import datetime
import sys

# --- CONFIGURAÇÕES ---
# Pega a data de HOJE do sistema
data_hoje = datetime.now().strftime('%m-%d-%Y')
url_api = f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarDia(dataCotacao=@dataCotacao)?@dataCotacao='{data_hoje}'&$top=1&$format=json"

dados_conexao = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=CORPORATIVOMTCS;"
    "Database=Financeiro;"
    "Trusted_Connection=yes;"
)


def importar_diario():
    try:
        # 1. Busca na API
        response = requests.get(url_api)
        dados = response.json()

        if not dados['value']:
            print(f"Nenhuma cotação disponível para hoje ({data_hoje}).")
            return

        item = dados['value'][0]
        valor_compra = item['cotacaoCompra']
        valor_venda = item['cotacaoVenda']
        data_api = item['dataHoraCotacao'].split(
            ' ')[0]  # Pega só a data YYYY-MM-DD

        # 2. Conecta e Grava
        conn = pyodbc.connect(dados_conexao)
        cursor = conn.cursor()

        # Query que previne duplicação
        query = """
        IF NOT EXISTS (SELECT 1 FROM CotacaoDolar WHERE DataCotacao = ?)
        BEGIN
            INSERT INTO CotacaoDolar (DataCotacao, ValorCompra, ValorVenda)
            VALUES (?, ?, ?)
        END
        """

        cursor.execute(query, data_api, data_api, valor_compra, valor_venda)
        conn.commit()
        print(f"Sucesso: Cotação de {data_api} inserida/verificada.")

    except Exception as e:
        # Em automação, é bom gravar erros em um arquivo de log, mas por enquanto vamos printar
        print(f"Erro: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    importar_diario()
