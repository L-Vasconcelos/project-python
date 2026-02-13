import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
import requests
import os
import time
import json
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
# Requer instalação: pip install streamlit-autorefresh
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURAÇÕES GERAIS ---
st.set_page_config(page_title="Monitoramento Meridional TCS", layout="wide")

CLIENT_ID = os.getenv('client_id')
CLIENT_SECRET = os.getenv('client_secret')

if not CLIENT_ID or not CLIENT_SECRET:
    st.error("ERRO: Credenciais da API (client_id/secret) não encontradas.")
    st.stop()

URL_API = "https://api.hlag.com/hlag/external/v2/events"
CAMINHO_PLANILHA = r"C:\Users\lsilva\Meridional TCS Ind e Com de Oleos S A\Banco de Dados - booking list\booking _list.xlsx"
CAMINHO_SAVE_SHAREPOINT = r"C:\Users\lsilva\Meridional TCS Ind e Com de Oleos S A\Database\Comex\booking list\relatorio_executivo_bookings.xlsx"
ARQUIVO_CACHE = "cache_hlag_v_final_map_excel.json"

MAPA_STATUS = {
    "LOAD": "Carga Embarcada", "DISC": "Vessel Arrived", "GTIN": "Gate-in Terminal",
    "GTOUT": "Gate-out Terminal", "RECE": "Carga Recebida", "DEPA": "Navio Zarpou"
}

# --- FUNÇÕES ---


def formatar_data_br(data_iso):
    if not data_iso or data_iso == "---":
        return "---"
    try:
        dt = datetime.fromisoformat(data_iso.replace('Z', '+00:00'))
        return dt.strftime('%d/%m/%Y %H:%M')
    except:
        return data_iso


def carregar_cache():
    if os.path.exists(ARQUIVO_CACHE):
        with open(ARQUIVO_CACHE, 'r') as f:
            return json.load(f)
    return {}


def salvar_cache(dados):
    with open(ARQUIVO_CACHE, 'w') as f:
        json.dump(dados, f)


@st.cache_data(ttl=86400)
def buscar_coordenadas(nome):
    # User-Agent alterado para renovar a permissão de busca
    geolocator = Nominatim(user_agent="meridional_logistics_tracker_v3_fix")

    try:
        nome_limpo = nome.split('(')[0].strip()

        # TENTATIVA 1: Busca pelo nome exato (Ex: Paranagua)
        location = geolocator.geocode(nome_limpo, timeout=10)

        # TENTATIVA 2: Se falhar, tenta adicionar "Port of" (Ex: Port of Paranagua)
        if not location:
            time.sleep(1)  # Pausa respeitosa
            location = geolocator.geocode(f"Port of {nome_limpo}", timeout=10)

        if location:
            return [location.latitude, location.longitude]
        else:
            return [None, None]
    except:
        return [None, None]


def consultar_hlag(booking, cache):
    agora = datetime.now()
    if str(booking) in cache:
        info = cache[str(booking)]
        if agora - datetime.strptime(info['timestamp'], '%Y-%m-%d %H:%M:%S') < timedelta(hours=12):
            return info['dados'], True, "✅ (Cache)"

    headers = {"X-IBM-Client-ID": CLIENT_ID,
               "X-IBM-Client-Secret": CLIENT_SECRET, "Accept": "application/json"}
    try:
        response = requests.get(URL_API, headers=headers, params={
                                "carrierBookingReference": str(booking)}, timeout=25)
        if response.status_code == 200:
            dados = response.json()
            cache[str(booking)] = {
                'dados': dados, 'timestamp': agora.strftime('%Y-%m-%d %H:%M:%S')}
            salvar_cache(cache)
            return dados, True, "✅ Ativo"
        return None, False, f"Erro {response.status_code}"
    except:
        return None, False, "Erro Conexão"


# --- INTERFACE E LAYOUT ---
st.title("🚢 Painel de Monitoramento Logístico")

sharepoint_ok = os.path.exists(CAMINHO_PLANILHA)

# Layout idêntico ao print solicitado
c1, c2, c3, c4 = st.columns([3, 3, 2, 1.5])

with c1:
    if sharepoint_ok:
        st.success("🟢 SHAREPOINT: Online")
    else:
        st.error("🔴 SHAREPOINT: Offline")

with c2:
    if CLIENT_ID:
        st.success("🟢 API HLAG: Credenciais Carregadas")

with c3:
    refresh_ativo = st.toggle("Atualização Automática (60 min)", value=True)

with c4:
    if st.button("Atualização", use_container_width=True):
        st.cache_data.clear()  # Limpa cache de coordenadas
        st.rerun()

    # Placeholder para o botão salvar aparecer aqui depois
    container_botao_salvar = st.empty()

# Lógica do Refresh
if refresh_ativo:
    st_autorefresh(interval=3600000, key="refresh_global")

# --- PROCESSAMENTO ---
if sharepoint_ok:
    try:
        df_base = pd.read_excel(CAMINHO_PLANILHA)
        df_base.columns = df_base.columns.str.strip()
        col_booking = [c for c in df_base.columns if 'booking' in c.lower()][0]
        lista_bookings = df_base[col_booking].dropna().unique()

        dados_tabela = []
        cache_local = carregar_cache()

        progresso = st.progress(0)

        for i, b in enumerate(lista_bookings):
            json_api, sucesso, msg = consultar_hlag(b, cache_local)
            item = {
                "Booking": str(b), "Container": "---", "Status": msg,
                "Origem": "---", "Transporte": "---", "Viagem": "---", "IMO": "---",
                "Localização Atual": "---", "Último Evento": "---", "Destino": "---",
                "Saída": "---", "Chegada": "---", "lat_o": None, "lon_o": None, "lat_d": None, "lon_d": None
            }

            if sucesso and json_api:
                eventos = sorted(
                    json_api, key=lambda x: x.get('eventDateTime', ''))
                for ev in eventos:
                    tc = ev.get('transportCall', {})
                    v_viag = tc.get('carrierVoyageNumber') or tc.get(
                        'voyageNumber')
                    v_imo = tc.get('vessel', {}).get('vesselIMONumber')
                    v_navio = tc.get('vessel', {}).get('vesselName')
                    cont_id = ev.get('equipmentReference') or ev.get(
                        'containerReference')
                    if v_viag and item["Viagem"] == "---":
                        item["Viagem"] = v_viag
                    if v_imo and item["IMO"] == "---":
                        item["IMO"] = v_imo
                    if v_navio and item["Transporte"] == "---":
                        item["Transporte"] = v_navio
                    if cont_id and item["Container"] == "---":
                        item["Container"] = cont_id

                if eventos:
                    def extract(ev):
                        loc = ev.get('eventLocation') or ev.get(
                            'transportCall', {}).get('location') or {}
                        st_trad = MAPA_STATUS.get(
                            ev.get('shipmentEventTypeCode'), ev.get('eventType', '---'))
                        return loc.get('locationName', 'Em Trânsito'), st_trad, loc.get('UNLocationCode', '')

                    item["Origem"], _, un_o = extract(eventos[0])
                    item["Destino"], _, un_d = extract(eventos[-1])
                    item["Saída"] = formatar_data_br(
                        eventos[0].get('eventDateTime'))
                    item["Chegada"] = formatar_data_br(
                        eventos[-1].get('eventDateTime'))

                    reais = [e for e in eventos if e.get(
                        'eventClassifierCode') == 'ACT']
                    if reais:
                        item["Localização Atual"], item["Último Evento"], _ = extract(
                            reais[-1])
                    else:
                        item["Localização Atual"] = "Pré-Embarque"

                    # Busca de coordenadas com a nova lógica robusta
                    item["lat_o"], item["lon_o"] = buscar_coordenadas(
                        item["Origem"])
                    item["lat_d"], item["lon_d"] = buscar_coordenadas(
                        item["Destino"])

            dados_tabela.append(item)
            progresso.progress((i + 1) / len(lista_bookings))
            if "Ativo" in msg:
                time.sleep(1.5)

        progresso.empty()
        df_final = pd.DataFrame(dados_tabela)

        # Renderiza o botão Salvar no local reservado lá em cima
        with container_botao_salvar:
            if st.button("Salvar Excel", use_container_width=True):
                try:
                    os.makedirs(os.path.dirname(
                        CAMINHO_SAVE_SHAREPOINT), exist_ok=True)
                    df_final.drop(columns=['lat_o', 'lon_o', 'lat_d', 'lon_d']).to_excel(
                        CAMINHO_SAVE_SHAREPOINT, index=False)
                    st.toast("✅ Arquivo Salvo!", icon="💾")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        # --- MAPA ---
        st.subheader("🗺️ Localização das Cargas")

        m = folium.Map(location=[10, 0], zoom_start=2, tiles=None)
        folium.TileLayer('CartoDB dark_matter', name="Dark Mode",
                         no_wrap=True, control=False).add_to(m)

        # Filtra apenas dados válidos
        df_mapa = df_final.dropna(subset=['lat_o', 'lon_o', 'lat_d', 'lon_d'])

        # Contador de rotas para debug
        rotas_criadas = 0
        for _, r in df_mapa.iterrows():
            AntPath(
                locations=[[r['lat_o'], r['lon_o']], [r['lat_d'], r['lon_d']]],
                color="#39FF14", weight=3, opacity=0.8,
                tooltip=f"{r['Booking']}: {r['Origem']} -> {r['Destino']}"
            ).add_to(m)
            rotas_criadas += 1

        # Mensagem mais clara se falhar
        if rotas_criadas == 0:
            st.warning(
                "⚠️ Nenhuma rota plotada. As coordenadas não foram encontradas. Clique em 'Atualização' para tentar novamente.")

        st_folium(m, width="100%", height=450, key="mapa_final_v3")

        # --- TABELA ---
        st.subheader("📋 Relatório Completo de Embarques")

        def colorir_transporte(row):
            t = str(row['Transporte']).upper()
            if any(x in t for x in ["EXPRESS", "VESSEL", "SHIP"]):
                return ['background-color: #004d00'] * len(row)
            if "TRUCK" in t or "ROAD" in t:
                return ['background-color: #002b80'] * len(row)
            return [''] * len(row)

        cols_viz = ["Booking", "Container", "Status", "Origem", "Transporte", "Viagem",
                    "Localização Atual", "Último Evento", "Destino", "Saída", "Chegada"]
        st.dataframe(df_final[cols_viz].style.apply(
            colorir_transporte, axis=1), use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Erro no processamento: {e}")
