import os
import pandas as pd
import requests
import time

# --- CONFIGURAÇÕES ---
# Agora o Python busca os valores nas Variáveis de Ambiente do Windows
CLIENT_ID = os.getenv('client_id')
CLIENT_SECRET = os.getenv('client_secret')

# Verifica se carregou corretamente (para te avisar se der erro)
if not CLIENT_ID or not CLIENT_SECRET:
    print("ERRO CRÍTICO: As variáveis 'client_id' ou 'client_secret' não foram encontradas.")
    print("Dica: Reinicie o VS Code se acabou de criar as variáveis.")

# Caminho baseado na estrutura do seu SharePoint sincronizado no Windows
CAMINHO_PLANILHA = r"C:\Users\lsilva\Meridional TCS Ind e Com de Oleos S A\Banco de Dados - booking list\booking _list.xlsx"
ARQUIVO_SAIDA = r"C:\Users\lsilva\OneDrive\Arquivos\Python\API RESTful\resultado_rastreamento.xlsx"


def processar_rastreamento():
    # 1. Verificação de existência do arquivo
    if not os.path.exists(CAMINHO_PLANILHA):
        print(f"ERRO: Arquivo não encontrado!")
        print(f"Certifique-se de que a pasta 'Database' do SharePoint está sincronizada no seu computador.")
        print(f"Caminho tentado: {CAMINHO_PLANILHA}")
        return

    try:
        # 2. Leitura da Planilha
        df_base = pd.read_excel(CAMINHO_PLANILHA)

        # Limpa nomes de colunas (remove espaços extras)
        df_base.columns = df_base.columns.str.strip()

        # Busca automática pela coluna de booking
        colunas_booking = [
            c for c in df_base.columns if 'booking' in c.lower()]

        if not colunas_booking:
            print(f"Colunas encontradas: {list(df_base.columns)}")
            print("Erro: Não foi encontrada uma coluna com o nome 'Booking'.")
            return

        nome_coluna = colunas_booking[0]
        lista_bookings = df_base[nome_coluna].dropna().unique()

        print(
            f"Localizado {len(lista_bookings)} bookings na coluna '{nome_coluna}'.")

        # ... aqui continua a lógica de requests.get() que validamos anteriormente ...

    except Exception as e:
        print(f"Erro ao processar: {e}")


if __name__ == "__main__":
    processar_rastreamento()
