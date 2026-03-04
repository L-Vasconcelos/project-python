import requests
import pyodbc
from datetime import datetime

# --- CONFIGURAÇÕES ---
data_hoje = datetime.now().strftime('%m-%d-%Y')

# AJUSTE NA URL:
# Removemos o filtro de texto 'Fechamento' e usamos o $orderby desc com $top=1
# Isso garante que pegaremos o ÚLTIMO boletim do dia (que é o de fechamento).
url_api = (
    f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
    f"CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)?"
    f"@moeda='EUR'&@dataCotacao='{data_hoje}'"
    f"&$orderby=dataHoraCotacao desc&$top=1&$format=json"
)

dados_conexao = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=CORPORATIVOMTCS;"
    "Database=Financeiro;"
    "Trusted_Connection=yes;"
)


def importar_euro_diario():
    try:
        response = requests.get(url_api)
        dados = response.json()

        # Verifica se a lista 'value' contém dados
        if not dados.get('value'):
            print(
                f"Nenhuma cotação de Euro disponível para hoje ({data_hoje}) até o momento.")
            return

        item = dados['value'][0]

        valor_compra = item['cotacaoCompra']
        valor_venda = item['cotacaoVenda']
        # Limpeza da data para o formato SQL YYYY-MM-DD
        data_api = item['dataHoraCotacao'].split(' ')[0]

        conn = pyodbc.connect(dados_conexao)
        cursor = conn.cursor()

        query = """
        IF NOT EXISTS (SELECT 1 FROM CotacaoEuro WHERE DataCotacao = ?)
        BEGIN
            INSERT INTO CotacaoEuro (DataCotacao, ValorCompra, ValorVenda)
            VALUES (?, ?, ?)
        END
        """

        cursor.execute(query, data_api, data_api, valor_compra, valor_venda)
        conn.commit()
        print(
            f"Sucesso: PTAX Euro de {data_api} processada. Compra: {valor_compra}")

    except Exception as e:
        print(f"Erro ao processar Euro: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    importar_euro_diario()
