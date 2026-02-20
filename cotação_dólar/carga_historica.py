import requests
import pyodbc
from datetime import datetime

# --- CONFIGURAÇÕES ---
data_inicio = '02-14-2026'
data_fim = '02-18-2026'  # (Mês 03, dia 02? Ou Dia 03, Mês 02?)

# URL específica para PERÍODO (Note o $top=10000 para garantir que traga tudo de uma vez)
url_api = (
    f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
    f"CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)?"
    f"@dataInicial='{data_inicio}'&@dataFinalCotacao='{data_fim}'&$top=10000&$format=json"
)

# 2. Conexão SQL Server (Seu Servidor Atual)
dados_conexao = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=CORPORATIVOMTCS;"
    "Database=Financeiro;"
    "Trusted_Connection=yes;"
)


def realizar_carga_historica():
    print("--- Iniciando Carga Histórica ---")
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

        # Query de inserção segura (evita duplicados)
        query = """
        IF NOT EXISTS (SELECT 1 FROM CotacaoDolar WHERE DataCotacao = ?)
        BEGIN
            INSERT INTO CotacaoDolar (DataCotacao, ValorCompra, ValorVenda)
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
            # Exemplo de entrada: "2020-01-02 13:11:10.123" -> Pegamos só a data
            data_formatada = data_str.split(' ')[0]

            cursor.execute(query, data_formatada, data_formatada,
                           valor_compra, valor_venda)
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
    realizar_carga_historica()
