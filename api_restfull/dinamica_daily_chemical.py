#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Daily Chemical Price Script -> Histórico (SunSirs + FX real)
AJUSTE REALIZADO: 
- Nome da aba corrigido para "daily_chem_prices".
- Proteção contra erro 'price_date' (KeyError).
- Data automática (hoje).
"""

import os
import datetime as dt
from pathlib import Path
from io import StringIO

import requests
import pandas as pd
import openpyxl  # Garante que a engine está disponível

# =========================
# CAMINHO: ONEDRIVE / PROJETO
# =========================


def _one_drive_base() -> Path:
    """Detecta a pasta base do OneDrive no Windows."""
    for var in ("OneDriveCommercial", "OneDriveConsumer", "OneDrive"):
        p = os.environ.get(var)
        if p and Path(p).exists():
            return Path(p)
    home = Path.home()
    if (home / "OneDrive").exists():
        return home / "OneDrive"
    return home / "Documents"


BASE_DIR = _one_drive_base() / "Arquivos" / "Python" / "excel-api_restful"
BASE_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_XLSX = str(BASE_DIR / "pogo_spread_history.xlsx")
# --- CORREÇÃO AQUI: Nome da aba igual ao do seu arquivo ---
HISTORY_SHEET = "daily_chem_prices"

print(f"Diretório base: {BASE_DIR}")
print(f"Arquivo alvo: {HISTORY_XLSX}")

# =========================
# CONFIGURAÇÕES
# =========================

USE_DUMMY_DATA = False
FX_API_BASE_URL = "https://api.exchangerate.host"

PRODUCT_CONFIGS = [
    {"product_code": "PG",  "region": "ASIA",
        "incoterm": "CFR", "api_symbol": "PG_ASIA_CFR"},
    {"product_code": "MEG", "region": "ASIA",
        "incoterm": "CFR", "api_symbol": "MEG_ASIA_CFR"},
    {"product_code": "DEG", "region": "ASIA",
        "incoterm": "CFR", "api_symbol": "DEG_ASIA_CFR"},
]

_fx_cache: dict[tuple[str, str, dt.date], float] = {}

# =========================
# FX + CONVERSÃO
# =========================


def fetch_fx_rate(from_currency: str, to_currency: str, date: dt.date) -> float:
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    if from_currency == to_currency:
        return 1.0

    if USE_DUMMY_DATA:
        return 0.14

    key = (from_currency, to_currency, date)
    if key in _fx_cache:
        return _fx_cache[key]

    rate = None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        url_hist = f"{FX_API_BASE_URL}/{date.isoformat()}"
        params_hist = {"base": from_currency, "symbols": to_currency}
        resp_hist = requests.get(
            url_hist, params=params_hist, headers=headers, timeout=30)
        if resp_hist.status_code == 200:
            data_hist = resp_hist.json()
            rates = data_hist.get("rates")
            if isinstance(rates, dict) and to_currency in rates:
                rate = float(rates[to_currency])
    except Exception as e:
        print(
            f"[FX] Falha histórica {from_currency}->{to_currency} {date}: {e}")

    if rate is None:
        try:
            url_conv = f"{FX_API_BASE_URL}/convert"
            params_conv = {"from": from_currency,
                           "to": to_currency, "date": date.isoformat()}
            resp_conv = requests.get(
                url_conv, params=params_conv, headers=headers, timeout=30)
            if resp_conv.status_code == 200:
                data_conv = resp_conv.json()
                if "result" in data_conv and data_conv["result"] is not None:
                    rate = float(data_conv["result"])
        except Exception as e:
            print(f"[FX] Falha convert: {e}")

    if rate is None:
        print(f"[FX] Fallback usado para {date}")
        if from_currency == "CNY" and to_currency == "USD":
            rate = 0.138
        else:
            rate = 1.0

    _fx_cache[key] = rate
    return rate


def convert_to_usd_per_mt(price: float, currency: str, unit: str, date: dt.date) -> float:
    currency = currency.upper()
    unit = unit.upper().strip()

    if unit in {"MT", "T", "TON", "TONNE"}:
        unit_factor = 1.0
    elif unit == "KG":
        unit_factor = 1000.0
    elif unit in {"LB", "LBS"}:
        unit_factor = 2204.62262
    else:
        raise ValueError(f"Unidade não suportada: {unit}")

    price_per_mt_original = price * unit_factor
    fx_rate = fetch_fx_rate(currency, "USD", date)
    return price_per_mt_original * fx_rate

# =========================
# SUNSIRS SCRAPING
# =========================


def _sunsirs_url_for_symbol(api_symbol: str) -> str:
    symbol = api_symbol.upper()
    if symbol.startswith("MEG"):
        commodity_id = 222
    elif symbol.startswith("DEG"):
        commodity_id = 1332
    elif symbol.startswith("PG"):
        commodity_id = 1316
    else:
        raise ValueError(f"Símbolo desconhecido: {api_symbol}")
    return f"https://www.sunsirs.com/uk/prodetail-{commodity_id}.html"


def fetch_price_for_date(api_symbol: str, region: str, incoterm: str, date: dt.date) -> float:
    if USE_DUMMY_DATA:
        return 1000.0

    url = _sunsirs_url_for_symbol(api_symbol)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.google.com/"
    }

    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    try:
        tables = pd.read_html(StringIO(resp.text))
    except ValueError:
        raise RuntimeError(f"Nenhuma tabela encontrada: {url}")

    if not tables:
        raise RuntimeError(f"Tabela vazia: {url}")
    df = tables[0].copy()

    def _detect_cols(df_local):
        cols_lower = [str(c).strip().lower() for c in df_local.columns]
        df_local.columns = cols_lower
        p_c = next(
            (c for c in cols_lower if "price" in c or "preço" in c or "preco" in c), None)
        d_c = next((c for c in cols_lower if "date" in c or "data" in c), None)
        return df_local, p_c, d_c

    df, price_col, date_col = _detect_cols(df)

    if price_col is None or date_col is None:
        if df.shape[0] > 1:
            header_row = df.iloc[0].tolist()
            if any(isinstance(x, str) for x in header_row):
                df = df.iloc[1:].copy()
                df.columns = [str(c).strip().lower() for c in header_row]
                df, price_col, date_col = _detect_cols(df)

    if price_col is None or date_col is None:
        if df.shape[1] >= 2:
            date_col, price_col = df.columns[0], df.columns[1]
        else:
            raise RuntimeError("Colunas não identificadas.")

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.date
    df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
    df = df.dropna(subset=[date_col, price_col]).sort_values(
        date_col, ascending=False)

    mask_exact = df[date_col] == date
    if mask_exact.any():
        row = df.loc[mask_exact].iloc[0]
    else:
        mask_le = df[date_col] <= date
        if mask_le.any():
            row = df.loc[mask_le].iloc[0]
        else:
            row = df.iloc[-1]

    price_rmb = float(row[price_col])
    return convert_to_usd_per_mt(price_rmb, "CNY", "MT", date)

# =========================
# GRAVAÇÃO SEGURA DO HISTÓRICO
# =========================


def write_history_to_excel(rows):
    if not rows:
        print("Nenhuma linha nova para processar.")
        return

    cols = ["price_date", "product_code", "region",
            "incoterm", "price_usd_per_mt", "source"]
    new_df = pd.DataFrame(rows, columns=cols)
    new_df["price_date"] = pd.to_datetime(new_df["price_date"])

    if os.path.exists(HISTORY_XLSX):
        print("Arquivo existente encontrado. Carregando...")
        try:
            try:
                # Tenta ler a aba com o nome correto
                old_df = pd.read_excel(HISTORY_XLSX, sheet_name=HISTORY_SHEET)

                # --- PROTEÇÃO CONTRA KEYERROR ---
                if "price_date" not in old_df.columns:
                    print(
                        f"AVISO: A aba '{HISTORY_SHEET}' existe mas o cabeçalho está diferente. Recriando aba para corrigir.")
                    final_df = new_df
                else:
                    old_df["price_date"] = pd.to_datetime(old_df["price_date"])
                    final_df = pd.concat([old_df, new_df], ignore_index=True)

            except ValueError:
                # Se a aba não existir, cria uma nova
                print(f"Aba '{HISTORY_SHEET}' não encontrada. Criando nova.")
                final_df = new_df

            # Remove duplicatas
            final_df = final_df.sort_values(
                by=["price_date", "product_code", "region", "incoterm"])
            final_df = final_df.drop_duplicates(
                subset=["price_date", "product_code", "region", "incoterm"],
                keep="last"
            )

            # Salva
            with pd.ExcelWriter(HISTORY_XLSX, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
                final_df.to_excel(writer, index=False,
                                  sheet_name=HISTORY_SHEET)

            print(
                f"Sucesso! Aba '{HISTORY_SHEET}' atualizada. Total de linhas: {len(final_df)}")

        except Exception as e:
            print(f"[ERRO CRÍTICO] Detalhe: {e}")
            print("Verifique se o arquivo está aberto e feche-o.")
    else:
        print("Arquivo não encontrado. Criando novo arquivo.")
        new_df = new_df.sort_values(by=["price_date", "product_code"])
        new_df.to_excel(HISTORY_XLSX, index=False, sheet_name=HISTORY_SHEET)
        print(f"Arquivo criado: {HISTORY_XLSX}")

# =========================
# EXECUÇÃO
# =========================


def run_range_job(start_date: dt.date, end_date: dt.date):
    current = start_date
    rows = []
    print(f"--- Iniciando coleta para data única: {start_date} ---")

    while current <= end_date:
        for cfg in PRODUCT_CONFIGS:
            try:
                price = fetch_price_for_date(
                    cfg["api_symbol"], cfg["region"], cfg["incoterm"], current)
                print(
                    f"[OK] {current} | {cfg['product_code']}: {price:.2f} USD/mt")
                rows.append((current.isoformat(
                ), cfg["product_code"], cfg["region"], cfg["incoterm"], price, "SunSirs+FX"))
            except Exception as e:
                print(f"[FALHA] {current} | {cfg['product_code']}: {e}")
        current += dt.timedelta(days=1)

    write_history_to_excel(rows)


if __name__ == "__main__":
    # Pega data de hoje automaticamente
    hoje = dt.date.today()
    run_range_job(hoje, hoje)
