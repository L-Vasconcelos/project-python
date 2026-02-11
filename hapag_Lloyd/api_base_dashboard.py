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

# --- CONFIGURAÇÕES ---
# SEGURANÇA: Busca as senhas nas Variáveis de Ambiente do Windows
CLIENT_ID = os.getenv('client_id')
CLIENT_SECRET = os.getenv('client_secret')

# Verifica se as chaves foram carregadas
if not CLIENT_ID or not CLIENT_SECRET:
    st.error(
        "ERRO: Credenciais da API (client_id/secret) não encontradas nas variáveis de ambiente.")
    st.stop()  # Para a execução se não tiver senha

URL_API = "https://api.hlag.com/hlag/external/v2/events"

# OBSERVAÇÃO IMPORTANTE PARA O FUTURO (STREAMLIT CLOUD):
# Caminhos 'C:\Users...' só funcionam no seu PC. Na nuvem, precisaremos mudar isso.
# Por enquanto, mantive para funcionar no seu computador.
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
def buscar_coordenadas(nome, locode):
    try:
        geolocator = Nominatim(user_agent="meridional_tcs_final_map_v16")
        location = geolocator.geocode(nome.split('(')[0].strip(), timeout=10)
        return [location.latitude, location.longitude] if location else [None, None]
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


# --- UI ---
st.set_page_config(page_title="Monitoramento Meridional TCS", layout="wide")
st.title("🚢 Painel de Monitoramento Logístico")

# Linha de Status e Ações
c1, c2, c3, c4 = st.columns([1, 1, 1, 0.5])
sharepoint_ok = os.path.exists(CAMINHO_PLANILHA)

with c1:
    if sharepoint_ok:
        st.success("🟢 SHAREPOINT: Online")
    else:
        st.error("🔴 SHAREPOINT: Offline")
with c2:
    if CLIENT_ID:
        st.success("🟢 API HLAG: Credenciais Carregadas")
with c3:
    if st.button("🔄 Atualizar Relatório"):
        st.cache_data.clear()
        st.rerun()

# --- PROCESSAMENTO ---
if sharepoint_ok:
    try:
        df_base = pd.read_excel(CAMINHO_PLANILHA)
        df_base.columns = df_base.columns.str.strip()
        col_booking = [c for c in df_base.columns if 'booking' in c.lower()][0]
        lista_bookings = df_base[col_booking].dropna().unique()

        dados_tabela = []
        cache_local = carregar_cache()

        for b in lista_bookings:
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

                # BUSCA PROFUNDA: Varre todo o histórico para preencher campos técnicos
                for ev in eventos:
                    tc = ev.get('transportCall', {})
                    # Fix Viagem: busca em todos os campos possíveis da API
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
                        if item["Localização Atual"] == "Desconhecido":
                            item["Localização Atual"] = "Navio em Viagem"
                    else:
                        item["Localização Atual"] = "Pré-Embarque"

                    item["lat_o"], item["lon_o"] = buscar_coordenadas(
                        item["Origem"], un_o)
                    item["lat_d"], item["lon_d"] = buscar_coordenadas(
                        item["Destino"], un_d)

            dados_tabela.append(item)
            if "Ativo" in msg:
                time.sleep(15)

        df_final = pd.DataFrame(dados_tabela)

        # Botão Excel Opcional
        with c4:
            if st.button("📊 Salvar Excel"):
                try:
                    os.makedirs(os.path.dirname(
                        CAMINHO_SAVE_SHAREPOINT), exist_ok=True)
                    df_final.drop(columns=['lat_o', 'lon_o', 'lat_d', 'lon_d']).to_excel(
                        CAMINHO_SAVE_SHAREPOINT, index=False)
                    st.toast("✅ Relatório salvo no SharePoint!", icon="📁")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        # --- MAPA (TEMA ESCURO PRESERVADO) ---
        st.subheader("🗺️ Localização das Cargas")
        m = folium.Map(location=[10, 0], zoom_start=2,
                       tiles='CartoDB dark_matter')
        # Proteção contra NaN no mapa
        df_mapa = df_final.dropna(subset=['lat_o', 'lon_o', 'lat_d', 'lon_d'])
        for _, r in df_mapa.iterrows():
            AntPath(locations=[[r['lat_o'], r['lon_o']], [r['lat_d'], r['lon_d']]],
                    color="#39FF14", weight=3, tooltip=f"Booking: {r['Booking']}").add_to(m)
        st_folium(m, width="100%", height=450, key="mapa_v_final_exec")

        # --- TABELA EXECUTIVA ---
        st.subheader("📋 Relatório Completo de Embarques")

        def colorir_transporte(row):
            t = str(row['Transporte']).upper()
            if any(x in t for x in ["EXPRESS", "VESSEL", "SHIP"]):
                color = 'background-color: #004d00'
            elif "TRUCK" in t or "ROAD" in t:
                color = 'background-color: #002b80'
            else:
                color = ''
            return [color] * len(row)

        cols_viz = ["Booking", "Container", "Status", "Origem", "Transporte", "Viagem",
                    "IMO", "Localização Atual", "Último Evento", "Destino", "Saída", "Chegada"]
        st.dataframe(df_final[cols_viz].style.apply(
            colorir_transporte, axis=1), use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Erro no processamento: {e}")
