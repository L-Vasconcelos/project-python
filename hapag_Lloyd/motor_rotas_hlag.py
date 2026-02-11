import pandas as pd
import requests
import time
import os
import shutil
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

# --- CONFIGURAÇÕES ---
# ALTERADO: Agora busca as senhas nas Variáveis de Ambiente do Windows
CLIENT_ID = os.getenv('client_id')
CLIENT_SECRET = os.getenv('client_secret')

# Detecta automaticamente a pasta do usuário atual (seja luisf ou lsilva)
USER_HOME = os.path.expanduser("~")

# Lista inteligente de caminhos para encontrar sua planilha
POSSIVEIS_CAMINHOS = [
    # Caminho exato que você forneceu, mas com o usuário dinâmico
    os.path.join(USER_HOME, "Meridional TCS Ind e Com de Oleos S A",
                 "Banco de Dados - booking list", "booking _list.xlsx"),
    # Variações comuns de backup
    os.path.join(USER_HOME, "OneDrive", "Arquivos", "booking _list.xlsx"),
    os.path.join(USER_HOME, "OneDrive", "Arquivos", "booking list.xlsx")
]

# Onde salvar o arquivo final para o Power BI ler
CAMINHO_SAIDA = os.path.join(
    USER_HOME, "OneDrive", "Arquivos", "base_rotas_powerbi.xlsx")

# Inicializa o serviço de mapas (apenas para fallback)
geolocator = Nominatim(user_agent="app_rastreamento_meridional", timeout=10)


def encontrar_arquivo_entrada():
    """Tenta encontrar o arquivo de entrada em vários locais."""
    print(f"--- Procurando arquivo de entrada (Base: {USER_HOME}) ---")
    for caminho in POSSIVEIS_CAMINHOS:
        if os.path.exists(caminho):
            print(f"Arquivo ENCONTRADO em: {caminho}")
            return caminho
    return None


def consultar_api_inteligente(numero_ref):
    """
    Tenta buscar como Booking. Se falhar, tenta como Container.
    """
    url = "https://api.hlag.com/hlag/external/v2/events/"
    headers = {
        "X-IBM-Client-ID": CLIENT_ID,
        "X-IBM-Client-Secret": CLIENT_SECRET,
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"  # Evita bloqueios simples
    }

    # Limpa o número (tira decimais e espaços)
    numero_limpo = str(numero_ref).replace('.0', '').strip()

    # 1. TENTATIVA A: BOOKING
    try:
        resp = requests.get(url, headers=headers, params={
                            "carrierBookingReference": numero_limpo}, timeout=20)
        if resp.status_code == 200:
            dados = resp.json()
            eventos = dados if isinstance(
                dados, list) else dados.get('events', [])
            if eventos:
                print(f"   > [OK] Encontrado como Booking: {numero_limpo}")
                return eventos
            else:
                print(
                    f"   > [VAZIO] Booking {numero_limpo} existe mas sem eventos.")
        elif resp.status_code not in [404, 400]:
            print(f"   > [ERRO {resp.status_code}] ao buscar Booking.")
    except Exception as e:
        print(f"   > Erro de conexão (Booking): {e}")

    # 2. TENTATIVA B: CONTAINER (Fallback)
    try:
        resp = requests.get(url, headers=headers, params={
                            "equipmentReference": numero_limpo}, timeout=20)
        if resp.status_code == 200:
            dados = resp.json()
            eventos = dados if isinstance(
                dados, list) else dados.get('events', [])
            if eventos:
                print(f"   > [OK] Encontrado como Container: {numero_limpo}")
                return eventos
    except Exception:
        pass

    return None


def obter_coordenadas_fallback(local_nome):
    """
    Usa o Geopy se a API não trouxer Lat/Lon.
    """
    if not local_nome or local_nome == 'Desconhecido':
        return None, None
    try:
        location = geolocator.geocode(f"{local_nome}, Port")
        if not location:
            location = geolocator.geocode(local_nome)
        if location:
            return location.latitude, location.longitude
    except:
        return None, None
    return None, None


def ler_excel_seguro(caminho):
    """Lê o Excel mesmo se estiver aberto."""
    try:
        return pd.read_excel(caminho)
    except PermissionError:
        print("Aviso: Arquivo aberto. Criando cópia temporária para leitura...")
        temp_path = caminho + ".temp.xlsx"
        shutil.copy2(caminho, temp_path)
        try:
            df = pd.read_excel(temp_path)
            return df
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    except Exception as e:
        print(f"Erro crítico ao ler planilha: {e}")
        return None


def processar_dados():
    caminho_real = encontrar_arquivo_entrada()
    if not caminho_real:
        print("\nERRO CRÍTICO: Planilha não encontrada em nenhum dos caminhos esperados.")
        return

    print("\n--- INICIANDO MOTOR DE ROTAS INTELIGENTE ---")

    df_base = ler_excel_seguro(caminho_real)
    if df_base is None:
        return

    # Normaliza colunas e busca a coluna de Booking
    df_base.columns = df_base.columns.str.strip()
    col_booking = next(
        (c for c in df_base.columns if 'booking' in c.lower()), None)

    if not col_booking:
        print(
            f"Coluna 'Booking' não encontrada. Colunas disponíveis: {list(df_base.columns)}")
        return

    lista_bookings = df_base[col_booking].dropna().unique()
    todas_rotas = []
    cache_coords = {}  # Cache para não gastar tempo calculando porto repetido

    print(f"Processando {len(lista_bookings)} referências...")

    for i, item in enumerate(lista_bookings):
        print(f"[{i+1}/{len(lista_bookings)}] Consultando: {item}...")

        eventos = consultar_api_inteligente(item)

        if eventos:
            for evento in eventos:
                # Extração de Dados
                local_obj = evento.get('location', {})
                local_nome = local_obj.get('locationName', 'Desconhecido')
                data_evento = evento.get('eventDateTime', '')
                tipo_evento = evento.get('eventType', '')
                desc_evento = evento.get('eventDescription', '')
                navio = evento.get('vessel', {}).get('vesselName', 'N/A')

                # --- LÓGICA INTELIGENTE DE COORDENADAS ---
                lat = local_obj.get('latitude')
                lon = local_obj.get('longitude')
                origem = "API"

                # Se a API veio vazia, usamos o plano B (Geopy)
                if lat is None or lon is None:
                    origem = "Geopy"
                    if local_nome and local_nome != 'Desconhecido':
                        if local_nome in cache_coords:
                            lat, lon = cache_coords[local_nome]
                        else:
                            lat, lon = obter_coordenadas_fallback(local_nome)
                            if lat:
                                cache_coords[local_nome] = (lat, lon)
                            # Pequena pausa apenas se precisou usar o serviço externo
                            time.sleep(1)

                todas_rotas.append({
                    "Ref_Original": item,
                    "Navio": navio,
                    "Data_Evento": data_evento,
                    "Tipo_Evento": tipo_evento,
                    "Descricao": desc_evento,
                    "Local": local_nome,
                    "Latitude": lat,
                    "Longitude": lon,
                    "Origem_Coord": origem
                })

        # Pausa mínima para não sobrecarregar a API da Hapag-Lloyd
        time.sleep(0.5)

    # Salvamento final
    if todas_rotas:
        df_final = pd.DataFrame(todas_rotas)
        df_final.sort_values(by=['Ref_Original', 'Data_Evento'], inplace=True)

        try:
            # Cria a pasta de saída se não existir
            os.makedirs(os.path.dirname(CAMINHO_SAIDA), exist_ok=True)

            df_final.to_excel(CAMINHO_SAIDA, index=False)
            print(f"\nSUCESSO! Arquivo gerado em:\n{CAMINHO_SAIDA}")
            print(f"Total de eventos: {len(df_final)}")
        except PermissionError:
            print(f"\nERRO: O arquivo de saída '{CAMINHO_SAIDA}' está aberto.")
            print("Feche o Excel e rode o script novamente.")
    else:
        print("\nNenhum dado encontrado. Verifique se os números de Booking estão corretos e ativos.")


if __name__ == "__main__":
    processar_dados()
