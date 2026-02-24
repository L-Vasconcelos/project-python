import requests
import pyodbc
from datetime import datetime

# --- CONFIGURAÇÕES ---
data_hoje = datetime.now().strftime('%m-%d-%Y')

# URL BLINDADA: Traz apenas o boletim onde o tipo é exatamente 'Fechamento'
url_api = (
    f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
    f"CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)?"
    f"@moeda='EUR'&@dataCotacao='{data_hoje}'"
    f"&$filter=tipoBoletim eq 'Fechamento'&$format=json"
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

        # Se o BCB ainda não publicou o Fechamento de hoje, ele para aqui e não grava nada errado
        if not dados['value']:
            print(
                f"Boletim de FECHAMENTO do Euro ainda não disponível para hoje ({data_hoje}).")
            return

        # Como filtramos, só vem 1 resultado: o PTAX final
        item = dados['value'][0]

        valor_compra = item['cotacaoCompra']
        valor_venda = item['cotacaoVenda']
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
            f"Sucesso: PTAX Final do Euro de {data_api} inserida/verificada. Compra: {valor_compra}")

    except Exception as e:
        print(f"Erro: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    importar_euro_diario()
