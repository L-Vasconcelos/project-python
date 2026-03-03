import requests
import pyodbc
from datetime import datetime

# --- CONFIGURAÇÕES ---
# Formato Mês-Dia-Ano (MM-DD-AAAA)
data_inicio = '01-01-2024'
data_fim = '03-03-2026' # Data de hoje para cobrir tudo

# URL AJUSTADA: Removemos o filtro fixo de 'Fechamento' para evitar que dias 
# recém-fechados fiquem de fora por atraso na etiqueta do BC.
# Ordenamos por dataHoraCotacao para garantir a cronologia.
url_api = (
    f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
    f"CotacaoMoedaPeriodo(moeda=@moeda,dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)?"
    f"@moeda='EUR'&@dataInicial='{data_inicio}'&@dataFinalCotacao='{data_fim}'"
    f"&$orderby=dataHoraCotacao asc&$format=json"
)

# Conexão SQL Server
dados_conexao = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=CORPORATIVOMTCS;"
    "Database=Financeiro;"
    "Trusted_Connection=yes;"
)

def realizar_carga_historica_euro():
    print(f"--- Iniciando Carga Histórica do EURO ({data_inicio} até {data_fim}) ---")
    print("Baixando dados do Banco Central... aguarde.")

    try:
        response = requests.get(url_api)
        response.raise_for_status()
        dados = response.json()
        todos_boletins = dados['value']

        if not todos_boletins:
            print("Nenhum dado encontrado no período.")
            return

        # --- LÓGICA DE FILTRAGEM ---
        # Como o BC gera vários boletins por dia, vamos guardar apenas o ÚLTIMO de cada data.
        cotações_por_dia = {}
        for item in todos_boletins:
            data_curta = item['dataHoraCotacao'].split(' ')[0]
            # O dicionário será sobrescrito a cada novo boletim do mesmo dia,
            # restando apenas o último (o fechamento real) ao final do loop.
            cotações_por_dia[data_curta] = item

        lista_final = list(cotações_por_dia.values())
        print(f"Foram identificados {len(lista_final)} dias úteis para importar.")

    except Exception as e:
        print(f"Erro ao baixar dados: {e}")
        return

    # Conectar ao Banco
    try:
        conn = pyodbc.connect(dados_conexao)
        cursor = conn.cursor()

        query = """
        IF NOT EXISTS (SELECT 1 FROM CotacaoEuro WHERE DataCotacao = ?)
        BEGIN
            INSERT INTO CotacaoEuro (DataCotacao, ValorCompra, ValorVenda)
            VALUES (?, ?, ?)
        END
        """

        print("Gravando no Banco de Dados...")
        
        for item in lista_final:
            data_api = item['dataHoraCotacao'].split(' ')[0]
            v_compra = item['cotacaoCompra']
            v_venda = item['cotacaoVenda']

            cursor.execute(query, data_api, data_api, v_compra, v_venda)

        conn.commit()
        print(f"--- Sucesso! Processo finalizado. ---")
        print(f"Registros processados na tabela CotacaoEuro: {len(lista_final)}")

    except Exception as e:
        print(f"Erro no Banco de Dados: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    realizar_carga_historica_euro()