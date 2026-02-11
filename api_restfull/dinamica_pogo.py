#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
POGO Spread – coleta diária, histórico em Excel e gráfico.
- Palma (MPOC, MYR/ton) -> converte para USD/ton via USDMYR (Yahoo Finance)
- Brent (Yahoo Finance, USD/bbl) -> USD/ton via 7.33 bbl/ton
- POGO = Palma(USD/ton) - Brent(USD/ton)
Saídas:
  - Excel: pogo_spread_history.xlsx (aba 'history')
  - Gráfico: pogo_spread.png
Opcionais (comente/descomente no topo):
  - Publicar em Google Sheets
  - Enviar e-mail com gráfico
Agendamento:
  - Windows Task Scheduler ou crona
"""

import cloudscraper
import os
import re
import sys
import json
import smtplib
import logging
import requests
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
# Imports para o Selenium (adicione no topo do arquivo)
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from curl_cffi import requests as c_requests
from pathlib import Path
from datetime import datetime
from dateutil.tz import gettz
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

# ===== NOVOS IMPORTS (MPOC robusto + debug) =====
from io import StringIO
from collections import Counter
from bs4 import BeautifulSoup

# ============== CONFIGURAÇÃO (edite aqui) ============== #
TZ = gettz("America/Sao_Paulo")


def _one_drive_base() -> Path:
    """Detecta a pasta base do OneDrive no Windows (corporativo/consumer)."""
    for var in ("OneDriveCommercial", "OneDriveConsumer", "OneDrive"):
        p = os.environ.get(var)
        if p and Path(p).exists():
            return Path(p)
    home = Path.home()
    if (home / "OneDrive").exists():
        return home / "OneDrive"
    # Fallback local caso não haja OneDrive
    return home / "Documents"


# Pasta base do projeto
BASE_DIR = _one_drive_base() / "Arquivos" / "Python" / "excel-api_restful"
BASE_DIR.mkdir(parents=True, exist_ok=True)  # garante existência

# Arquivos de saída
HISTORY_XLSX = str(BASE_DIR / "pogo_spread_history.xlsx")
HISTORY_SHEET = "history"
PLOT_PNG = str(BASE_DIR / "pogo_spread.png")

# Fontes de dados
BRENT_SYMBOL = "BZ=F"            # Brent no Yahoo Finance (USD/bbl)
BARRELS_PER_TON = 7.33           # ~ barris por tonelada
MPOC_URL = "https://www.mpoc.org.my/market-insight/daily-palm-oil-prices/"

# (OPCIONAL) Publicar no Google Sheets
GDRIVE_ENABLE = False
GDRIVE_SHEET_NAME = "POGO Spread"
GDRIVE_WORKSHEET = "history"
GDRIVE_CREDENTIALS_JSON = "service_account.json"

# (OPCIONAL) Enviar por e-mail o gráfico
EMAIL_ENABLE = False
SMTP_HOST = "smtp.office365.com"
SMTP_PORT = 587
SMTP_USER = "seu.email@empresa.com"
SMTP_PASS = "SUA_SENHA_OU_APP_PASSWORD"
EMAIL_TO = ["destinatario@empresa.com"]
EMAIL_SUBJECT = "POGO Spread atualizado"
EMAIL_BODY = "Segue anexo o gráfico diário do POGO Spread."
# ======================================================= #

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")


def _today_local_date():
    return datetime.now(TZ).date()


def _ensure_parent_dir(path: str):
    d = os.path.dirname(os.path.abspath(path))
    try:
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
    except PermissionError as e:
        raise PermissionError(
            f"Sem permissão para criar/gravar em '{d}'. "
            "Verifique se o caminho pertence ao usuário atual, se o OneDrive está conectado, "
            "e se o 'Controlled Folder Access' do Windows Defender não está bloqueando o Python/VS Code."
        ) from e

# ------------------- Persistência ------------------- #


def read_history() -> pd.DataFrame:
    if not os.path.exists(HISTORY_XLSX):
        return pd.DataFrame(columns=["date", "palm_usd_ton", "brent_usd_ton", "pogo"])
    try:
        df = pd.read_excel(
            HISTORY_XLSX, sheet_name=HISTORY_SHEET, engine="openpyxl")
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df
    except Exception:
        # arquivo existe mas sem a aba; cria DF vazio
        return pd.DataFrame(columns=["date", "palm_usd_ton", "brent_usd_ton", "pogo"])


def write_history(df: pd.DataFrame):
    """
    Salva o histórico na aba 'history' SEM apagar as demais abas
    do arquivo pogo_spread_history.xlsx.
    """
    _ensure_parent_dir(HISTORY_XLSX)

    if os.path.exists(HISTORY_XLSX):
        # Arquivo já existe: anexa e substitui apenas a aba 'history'
        with pd.ExcelWriter(
            HISTORY_XLSX,
            engine="openpyxl",
            mode="a",
            if_sheet_exists="replace"
        ) as writer:
            df.to_excel(writer, sheet_name=HISTORY_SHEET, index=False)
    else:
        # Cria o arquivo do zero com a aba 'history'
        with pd.ExcelWriter(
            HISTORY_XLSX,
            engine="openpyxl",
            mode="w"
        ) as writer:
            df.to_excel(writer, sheet_name=HISTORY_SHEET, index=False)

# ------------------- Coleta de dados ------------------- #


# Adicione este import lá no topo junto com os outros

# Adicione este import no topo do seu arquivo, junto com os outros


def get_palm_price_myr_per_ton() -> int:
    """
    Extrai o preço do óleo de palma (MYR/ton) no MPOC.
    Usa Selenium para renderizar o JavaScript e passar pelo Cloudflare.
    """
    logging.info("Iniciando navegador Chrome via Selenium...")

    chrome_options = Options()
    # O modo '--headless=new' é mais moderno e menos detectável que o antigo
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    # User-agent real para parecer navegação legítima
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    try:
        # Instala/atualiza o driver automaticamente e inicia o browser
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        logging.info(f"Acessando {MPOC_URL}...")
        driver.get(MPOC_URL)

        # ESPERA IMPORTANTE: Dá 8 segundos para o Cloudflare validar e o JS carregar a tabela
        time.sleep(8)

        # Pega o HTML final, já com os dados renderizados
        html = driver.page_source
        driver.quit()

    except Exception as e:
        # Tenta fechar o driver se der erro
        try:
            driver.quit()
        except:
            pass
        raise RuntimeError(f"Erro no Selenium: {e}")

    # --- Daqui para baixo é a lógica de extração que você já tinha ---

    # Validação se ainda estamos bloqueados
    lower = html.lower()
    if ("just a moment" in lower and "cloudflare" in lower) or ("challenge-platform" in lower):
        debug_path = Path(
            BASE_DIR) / f"mpoc_selenium_blocked_{datetime.now(TZ).strftime('%Y%m%d_%H%M%S')}.html"
        debug_path.write_text(html, encoding="utf-8", errors="ignore")
        raise RuntimeError(
            f"MPOC_BLOCKED: Selenium foi detectado. HTML salvo em {debug_path}")

    num_pat = re.compile(r"(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)")

    # 1) Tenta via tabelas HTML (agora que o JS rodou, a tabela deve existir)
    try:
        tables = pd.read_html(StringIO(html))
        candidates = []
        for t in tables:
            for v in t.values.ravel():
                if pd.isna(v):
                    continue
                s = str(v)
                m = num_pat.search(s)
                if not m:
                    continue
                n = float(m.group(1).replace(",", ""))
                if 2000 <= n <= 10000:
                    candidates.append(int(round(n)))

        if candidates:
            val = Counter(candidates).most_common(1)[0][0]
            logging.info(f"Preço encontrado via tabela: {val}")
            return val
    except Exception as e:
        logging.info(f"[MPOC] read_html falhou mesmo com Selenium: {e}")

    # 2) Fallback por texto (BeautifulSoup)
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)
    found = []
    for m in num_pat.finditer(text):
        n = float(m.group(1).replace(",", ""))
        if 2000 <= n <= 10000:
            found.append(int(round(n)))

    if found:
        val = Counter(found).most_common(1)[0][0]
        logging.info(f"Preço encontrado via texto: {val}")
        return val

    # 3) Falha total
    debug_path = Path(
        BASE_DIR) / f"mpoc_debug_{datetime.now(TZ).strftime('%Y%m%d_%H%M%S')}.html"
    debug_path.write_text(html, encoding="utf-8", errors="ignore")
    raise RuntimeError(
        f"Não consegui extrair o preço nem com Selenium. Verifique o HTML em: {debug_path}"
    )
    num_pat = re.compile(r"(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)")

    # 1) Tenta via tabelas HTML
    try:
        tables = pd.read_html(StringIO(html))
        candidates = []
        for t in tables:
            for v in t.values.ravel():
                if pd.isna(v):
                    continue
                s = str(v)
                m = num_pat.search(s)
                if not m:
                    continue
                n = float(m.group(1).replace(",", ""))
                # Faixa plausível para MYR/ton (2000 a 10000)
                if 2000 <= n <= 10000:
                    candidates.append(int(round(n)))

        if candidates:
            # Pega o valor mais comum encontrado nas tabelas
            return Counter(candidates).most_common(1)[0][0]

    except Exception as e:
        logging.info(f"[MPOC] read_html falhou (pode ser layout/JS): {e}")

    # 2) Fallback por texto completo (BeautifulSoup)
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)

    found = []
    # Procura números soltos no texto que façam sentido
    for m in num_pat.finditer(text):
        n = float(m.group(1).replace(",", ""))
        if 2000 <= n <= 10000:
            found.append(int(round(n)))

    if found:
        return Counter(found).most_common(1)[0][0]

    # 3) Se chegou aqui, não achou nada
    debug_path = Path(
        BASE_DIR) / f"mpoc_debug_{datetime.now(TZ).strftime('%Y%m%d_%H%M%S')}.html"
    debug_path.write_text(html, encoding="utf-8", errors="ignore")
    raise RuntimeError(
        f"Não consegui extrair o preço. O site pode ter mudado o layout. HTML salvo em: {debug_path}"
    )

    # Padrão numérico flexível
    num_pat = re.compile(r"(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)")

    # 1) Tenta via tabelas HTML
    try:
        tables = pd.read_html(StringIO(html))
        candidates = []
        for t in tables:
            for v in t.values.ravel():
                if pd.isna(v):
                    continue
                s = str(v)
                m = num_pat.search(s)
                if not m:
                    continue
                n = float(m.group(1).replace(",", ""))
                # faixa plausível para MYR/ton
                if 2000 <= n <= 10000:
                    candidates.append(int(round(n)))

        if candidates:
            return Counter(candidates).most_common(1)[0][0]

    except Exception as e:
        logging.info(f"[MPOC] read_html falhou (pode ser layout/JS): {e}")

    # 2) Fallback por texto completo
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)

    found = []
    for m in num_pat.finditer(text):
        n = float(m.group(1).replace(",", ""))
        if 2000 <= n <= 10000:
            found.append(int(round(n)))

    if found:
        return Counter(found).most_common(1)[0][0]

    # 3) Debug final
    debug_path = Path(
        BASE_DIR) / f"mpoc_debug_{datetime.now(TZ).strftime('%Y%m%d_%H%M%S')}.html"
    debug_path.write_text(html, encoding="utf-8", errors="ignore")
    raise RuntimeError(
        f"Não consegui extrair o preço do óleo de palma (MYR/ton) no MPOC. HTML salvo em: {debug_path}"
    )

    # Padrão numérico flexível
    num_pat = re.compile(r"(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)")

    # 1) Tenta via tabelas HTML
    try:
        tables = pd.read_html(StringIO(html))
        candidates = []
        for t in tables:
            for v in t.values.ravel():
                if pd.isna(v):
                    continue
                s = str(v)
                m = num_pat.search(s)
                if not m:
                    continue
                n = float(m.group(1).replace(",", ""))
                # faixa plausível para MYR/ton
                if 2000 <= n <= 10000:
                    candidates.append(int(round(n)))

        if candidates:
            return Counter(candidates).most_common(1)[0][0]

    except Exception as e:
        logging.info(f"[MPOC] read_html falhou (pode ser layout/JS): {e}")

    # 2) Fallback por texto completo
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)

    found = []
    for m in num_pat.finditer(text):
        n = float(m.group(1).replace(",", ""))
        if 2000 <= n <= 10000:
            found.append(int(round(n)))

    if found:
        return Counter(found).most_common(1)[0][0]

    # 3) Debug final
    debug_path = Path(
        BASE_DIR) / f"mpoc_debug_{datetime.now(TZ).strftime('%Y%m%d_%H%M%S')}.html"
    debug_path.write_text(html, encoding="utf-8", errors="ignore")
    raise RuntimeError(
        f"Não consegui extrair o preço do óleo de palma (MYR/ton) no MPOC. HTML salvo em: {debug_path}"
    )


def get_usd_per_myr() -> float:
    """
    USD por 1 MYR via Yahoo Finance.
    """
    df = yf.download("USDMYR=X", period="5d",
                     auto_adjust=False, progress=False)
    if df.empty:
        raise RuntimeError("Sem dados de câmbio USDMYR no Yahoo Finance.")

    # Ajuste para compatibilidade com versões novas do yfinance
    if "Close" in df.columns:
        vals = df["Close"]
    else:
        vals = df.iloc[:, 0]

    if isinstance(vals, pd.DataFrame):
        vals = vals.iloc[:, 0]

    myr_per_usd = vals.dropna().iloc[-1].item()
    return 1.0 / myr_per_usd


def get_brent_usd_per_ton() -> float:
    """
    Converte Brent de USD/bbl para USD/ton.
    """
    df = yf.download(BRENT_SYMBOL, period="5d",
                     auto_adjust=False, progress=False)
    if df.empty:
        raise RuntimeError("Sem dados recentes do Brent.")

    # Ajuste para compatibilidade com versões novas do yfinance
    if "Close" in df.columns:
        vals = df["Close"]
    else:
        vals = df.iloc[:, 0]

    if isinstance(vals, pd.DataFrame):
        vals = vals.iloc[:, 0]

    usd_per_bbl = vals.dropna().iloc[-1].item()
    return usd_per_bbl * BARRELS_PER_TON

# ------------------- Gráfico ------------------- #


def plot_series(df: pd.DataFrame, path_png: str):
    if df.empty:
        logging.warning("Sem dados para plotar.")
        return
    _ensure_parent_dir(path_png)

    plt.figure(figsize=(10, 5))
    x = pd.to_datetime(df["date"])
    plt.plot(x, df["palm_usd_ton"], label="Palm (USD/ton)")
    plt.plot(x, df["brent_usd_ton"], label="Brent (USD/ton)")
    plt.plot(x, df["pogo"], label="POGO (Palm - Brent)")
    plt.title("POGO Spread (USD/ton)")
    plt.xlabel("Data")
    plt.ylabel("USD/ton")
    plt.grid(True, alpha=0.25)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path_png, dpi=150)
    plt.close()

# --------------- Integrações opcionais --------------- #


def publish_to_google_sheets(df: pd.DataFrame):
    import gspread
    from google.oauth2.service_account import Credentials

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(
        GDRIVE_CREDENTIALS_JSON, scopes=scopes)
    gc = gspread.authorize(creds)

    try:
        sh = gc.open(GDRIVE_SHEET_NAME)
    except gspread.SpreadsheetNotFound:
        sh = gc.create(GDRIVE_SHEET_NAME)

    try:
        ws = sh.worksheet(GDRIVE_WORKSHEET)
        sh.del_worksheet(ws)
    except Exception:
        pass

    ws = sh.add_worksheet(title=GDRIVE_WORKSHEET, rows="1000", cols="10")
    ws.update([df.columns.tolist()] + df.values.tolist())


def send_email_with_attachment(path_png: str):
    """Envia o PNG por e-mail usando SMTP."""
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = ", ".join(EMAIL_TO)
    msg["Subject"] = EMAIL_SUBJECT
    msg.attach(MIMEText(EMAIL_BODY, "plain", "utf-8"))

    part = MIMEBase('application', 'octet-stream')
    with open(path_png, "rb") as f:
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition',
                    f'attachment; filename="{os.path.basename(path_png)}"')
    msg.attach(part)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, EMAIL_TO, msg.as_string())

# ------------------- Fluxo principal ------------------- #


def run_once() -> dict:
    # Palma (MPOC) com fallback REMOVIDO
    palm_source = "MPOC"
    try:
        palm_myr_t = get_palm_price_myr_per_ton()  # MYR/ton (MPOC)
        usd_per_myr = get_usd_per_myr()            # USD por 1 MYR (Yahoo)
        palm_usd_t = palm_myr_t * usd_per_myr      # USD/ton
    except RuntimeError as e:
        # AJUSTE FEITO: Se houver bloqueio ou erro, o script para e não repete dados antigos.
        logging.error(
            f"FALHA CRÍTICA NA COLETA (MPOC Bloqueado ou erro de leitura): {e}")
        raise e

    brent_usd_t = get_brent_usd_per_ton()      # USD/ton
    pogo = palm_usd_t - brent_usd_t

    logging.info(
        f"Palm USD/ton: {palm_usd_t:,.2f} ({palm_source}) | Brent USD/ton: {brent_usd_t:,.2f} | POGO: {pogo:,.2f}"
    )

    df_hist = read_history()
    d_today = _today_local_date()

    new_row = {
        "date": d_today,
        "palm_usd_ton": round(palm_usd_t, 2),
        "brent_usd_ton": round(brent_usd_t, 2),
        "pogo": round(pogo, 2),
    }

    # evita duplicata do dia (atualiza se já existe)
    if not df_hist.empty and d_today in set(df_hist["date"]):
        df_hist.loc[df_hist["date"] == d_today,
                    ["palm_usd_ton", "brent_usd_ton", "pogo"]] = \
            [new_row["palm_usd_ton"], new_row["brent_usd_ton"], new_row["pogo"]]
    else:
        if df_hist.empty:
            df_hist = pd.DataFrame([new_row])
        else:
            df_hist = pd.concat(
                [df_hist, pd.DataFrame([new_row])], ignore_index=True)

    df_hist = df_hist.sort_values("date")
    write_history(df_hist)
    plot_series(df_hist, PLOT_PNG)

    if GDRIVE_ENABLE:
        logging.info("Publicando no Google Sheets…")
        publish_to_google_sheets(df_hist)

    if EMAIL_ENABLE:
        logging.info("Enviando e-mail com gráfico…")
        send_email_with_attachment(PLOT_PNG)

    return {
        "date": str(d_today),
        "palm_usd_ton": palm_usd_t,
        "brent_usd_ton": brent_usd_t,
        "pogo": pogo,
        "palm_source": palm_source,
    }


if __name__ == "__main__":
    try:
        result = run_once()
        logging.info("Concluído: " + json.dumps(result, ensure_ascii=False))
    except Exception:
        logging.exception("Falha na execução")
        sys.exit(1)
