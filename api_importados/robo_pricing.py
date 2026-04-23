"""
robo_pricing.py
Robô de captura de screenshot e envio automático do relatório de Pricing Importados.
Versão: 1.0 — Baseado no modelo robo_agendador.py (câmbio)

Fluxo:
  1. Inicia o Streamlit (dashboard_pricing_st.py)
  2. Aguarda o servidor ficar online
  3. Abre o Chrome headless e valida o carregamento completo do dashboard
  4. Captura o screenshot
  5. Envia o e-mail apenas se o dashboard sinalizou READY
  6. Encerra o Streamlit e registra o resultado no log

VARIÁVEL DE AMBIENTE OBRIGATÓRIA (Windows):
  Nome: SENHA_BI_EMAIL
  Valor: <senha do e-mail bi@mtcs.com.br>
  Configurar em: Painel de Controle > Sistema > Variáveis de Ambiente > Nova
"""

import os
import sys
import time
import socket
import subprocess
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ---------------------------------------------------------------------------
# CONFIGURAÇÕES
# ---------------------------------------------------------------------------

PASTA_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))
NOME_ARQUIVO_DASHBOARD = "dashboard_pricing_st.py"
CAMINHO_COMPLETO_DASHBOARD = os.path.join(
    PASTA_DO_SCRIPT, NOME_ARQUIVO_DASHBOARD)

# porta diferente do dashboard de câmbio (8501)
PORTA_STREAMLIT = "8502"
URL_DASHBOARD = f"http://127.0.0.1:{PORTA_STREAMLIT}"

EMAIL_REMETENTE = "bi@mtcs.com.br"
EMAIL_DESTINATARIO = "bi@mtcs.com.br"
SENHA_EMAIL = os.getenv("SENHA_BI_EMAIL")


# ---------------------------------------------------------------------------
# LOG ESTRUTURADO EM ARQUIVO
# ---------------------------------------------------------------------------

CAMINHO_LOG = os.path.join(PASTA_DO_SCRIPT, "log_pricing.txt")

logging.basicConfig(
    filename=CAMINHO_LOG,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
    encoding="utf-8",
)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
logging.getLogger().addHandler(console_handler)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ETAPA 1 — INICIAR STREAMLIT
# ---------------------------------------------------------------------------

def _matar_processo_na_porta(porta: int):
    """Encerra qualquer processo que esteja ocupando a porta informada."""
    try:
        resultado = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True
        )
        for linha in resultado.stdout.splitlines():
            if f":{porta}" in linha and "LISTENING" in linha:
                partes = linha.split()
                pid = partes[-1]
                subprocess.run(
                    ["taskkill", "/F", "/PID", pid],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                log.info(
                    f"Processo PID {pid} encerrado (porta {porta} liberada)")
    except Exception:
        pass


def _aguardar_porta_livre(porta: int, timeout: int = 30):
    """Aguarda até a porta ficar disponível (não ocupada)."""
    inicio = time.time()
    while time.time() - inicio < timeout:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        resultado = sock.connect_ex(("127.0.0.1", porta))
        sock.close()
        if resultado != 0:
            return True
        time.sleep(2)
    log.warning(f"Porta {porta} ainda ocupada após {timeout}s")
    return False


def _tentar_iniciar_streamlit() -> "subprocess.Popen | None":
    """
    Tenta iniciar o Streamlit uma vez.
    Retorna o processo se ficar online em até 120s, ou None.
    """
    if not os.path.exists(CAMINHO_COMPLETO_DASHBOARD):
        log.error(f"Arquivo não encontrado: {CAMINHO_COMPLETO_DASHBOARD}")
        return None

    # Encerra instâncias anteriores e libera a porta
    _matar_processo_na_porta(int(PORTA_STREAMLIT))
    _aguardar_porta_livre(int(PORTA_STREAMLIT), timeout=30)

    comando = [
        sys.executable, "-m", "streamlit", "run",
        CAMINHO_COMPLETO_DASHBOARD,
        "--server.port",     PORTA_STREAMLIT,
        "--server.headless", "true",
        "--server.address",  "127.0.0.1",
    ]

    CAMINHO_LOG_STREAMLIT = os.path.join(
        PASTA_DO_SCRIPT, "log_streamlit_pricing.txt")
    arquivo_log_streamlit = open(CAMINHO_LOG_STREAMLIT, "w", encoding="utf-8")

    processo = subprocess.Popen(
        comando,
        stdout=arquivo_log_streamlit,
        stderr=arquivo_log_streamlit,
    )

    log.info("Aguardando servidor Streamlit ficar online (máx. 120s)...")
    inicio = time.time()
    time.sleep(8)

    while time.time() - inicio < 120:
        if processo.poll() is not None:
            log.error(
                f"Streamlit encerrou inesperadamente (código {processo.returncode}). "
                "Verifique log_streamlit_pricing.txt"
            )
            return None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            resultado = sock.connect_ex(("127.0.0.1", int(PORTA_STREAMLIT)))
            sock.close()
            if resultado == 0:
                log.info(
                    f"Streamlit online em {round(time.time() - inicio, 1)}s")
                return processo
        except OSError:
            pass
        time.sleep(2)

    log.error("Timeout: Streamlit não ficou online em 120 segundos")
    processo.terminate()
    return None


def iniciar_streamlit():
    """
    Inicia o servidor Streamlit com até 2 tentativas.
    Retorna o objeto Popen do processo, ou None em caso de falha.
    """
    log.info(f"Iniciando Streamlit: {NOME_ARQUIVO_DASHBOARD}")

    for tentativa in range(1, 3):
        if tentativa > 1:
            log.warning(
                f"Tentativa {tentativa}/2 — aguardando 20s antes de reiniciar...")
            time.sleep(20)

        processo = _tentar_iniciar_streamlit()
        if processo:
            return processo
        log.error(f"Tentativa {tentativa}/2 falhou")

    return None


# ---------------------------------------------------------------------------
# ETAPA 2 — CAPTURA DO SCREENSHOT COM VALIDAÇÃO COMPLETA
# ---------------------------------------------------------------------------

def tirar_print_validado() -> bytes | None:
    """
    Abre o Chrome headless, valida em três camadas e captura o screenshot.

    Validações (em ordem):
      1. stApp carregado (DOM do Streamlit presente)
      2. Tabelas renderizadas (stDataFrame visível)
      3. Marcador #dashboard-ready injetado pelo dashboard
    """
    log.info("Preparando captura do dashboard...")

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,2800")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3")

    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(URL_DASHBOARD)

        wait = WebDriverWait(driver, 90)

        # ---------------------------------------------------------------
        # VALIDAÇÃO 1 — Estrutura do Streamlit carregada
        # ---------------------------------------------------------------
        log.info("Validação 1/3: aguardando estrutura do Streamlit...")
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.stApp")))
        log.info("Validação 1/3: OK")

        # ---------------------------------------------------------------
        # VALIDAÇÃO 2 — Tabelas de dados renderizadas
        # ---------------------------------------------------------------
        log.info("Validação 2/3: aguardando tabelas de preços...")
        try:
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[data-testid='stDataFrame']")))
            log.info("Validação 2/3: OK")
        except Exception:
            log.error(
                "Validação 2/3 FALHOU: tabelas não renderizaram — abortando")
            driver.quit()
            return None

        # ---------------------------------------------------------------
        # VALIDAÇÃO 3 — Marcador de dados completos (#dashboard-ready)
        # ---------------------------------------------------------------
        log.info("Validação 3/3: aguardando marcador de conclusão do dashboard...")
        try:
            wait.until(EC.presence_of_element_located(
                (By.ID, "dashboard-ready")))
            log.info("Validação 3/3: OK — dashboard READY confirmado")
        except Exception:
            if driver.find_elements(By.ID, "dashboard-error"):
                log.error(
                    "Validação 3/3 FALHOU: dashboard reportou #dashboard-error "
                    "(falha de conexão com o banco ou tabela vazia)"
                )
            else:
                log.error(
                    "Validação 3/3 FALHOU: timeout — dashboard não ficou pronto")
            driver.quit()
            return None

        # ---------------------------------------------------------------
        # Screenshot — aguarda estabilização visual
        # ---------------------------------------------------------------
        time.sleep(4)

        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        img_binaria = driver.get_screenshot_as_png()
        log.info("Screenshot capturado com sucesso")
        driver.quit()
        return img_binaria

    except Exception as e:
        log.error(f"Falha crítica no Selenium: {e}")
        if driver:
            driver.quit()
        return None


# ---------------------------------------------------------------------------
# ETAPA 3 — ENVIO DO E-MAIL
# ---------------------------------------------------------------------------

def enviar_email(img_data: bytes | None) -> bool:
    """
    Envia o e-mail com a imagem do dashboard de pricing.
    Aborta sem enviar se img_data for None.
    """
    if not img_data:
        log.error("=" * 60)
        log.error("ENVIO ABORTADO: nenhuma imagem válida foi gerada.")
        log.error("Causa provável: falha no banco, tabela vazia ou timeout.")
        log.error("Nenhum e-mail foi enviado.")
        log.error("=" * 60)
        return False

    log.info("Preparando envio de e-mail...")

    if not SENHA_EMAIL:
        log.error(
            "ERRO: Variável de ambiente 'SENHA_BI_EMAIL' não encontrada. "
            "Configure em: Painel de Controle > Sistema > Variáveis de Ambiente > Nova"
        )
        return False

    data_hoje = datetime.now().strftime("%d/%m/%Y")

    msg = MIMEMultipart("related")
    msg["Subject"] = f"Pricing Importados — {data_hoje}"
    msg["From"] = EMAIL_REMETENTE
    msg["To"] = EMAIL_DESTINATARIO

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
        <p style="font-size: 15px;">Bom dia,<br><br>
           Segue o relatório de <strong>Pricing de Químicos Importados</strong>
           atualizado para {data_hoje}:
        </p>
        <div style="margin: 20px 0;">
          <img src="cid:imagem_pricing"
               style="border: 1px solid #ddd; border-radius: 4px; max-width: 100%; height: auto;">
        </div>
        <p style="color: #999; font-size: 11px; border-top: 1px solid #eee; padding-top: 10px;">
          Relatório automático — Sistema BI MTCS — {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html_body, "html"))

    try:
        image = MIMEImage(img_data)
        image.add_header("Content-ID", "<imagem_pricing>")
        image.add_header(
            "Content-Disposition", "inline",
            filename=f"pricing_{data_hoje.replace('/', '-')}.png"
        )
        msg.attach(image)

        log.info("Conectando ao servidor SMTP (Office365)...")
        server = smtplib.SMTP("smtp.office365.com", 587, timeout=30)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_EMAIL)
        server.send_message(msg)
        server.quit()

        log.info(f"E-mail enviado com sucesso para: {EMAIL_DESTINATARIO}")
        return True

    except smtplib.SMTPAuthenticationError:
        log.error(
            "Falha de autenticação SMTP — verifique a variável SENHA_BI_EMAIL")
        return False
    except smtplib.SMTPException as e:
        log.error(f"Erro SMTP ao enviar e-mail: {e}")
        return False
    except Exception as e:
        log.error(f"Erro inesperado ao enviar e-mail: {e}")
        return False


# ---------------------------------------------------------------------------
# ENCERRAMENTO DO STREAMLIT
# ---------------------------------------------------------------------------

def encerrar_streamlit(processo):
    log.info("Encerrando servidor Streamlit...")
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(processo.pid)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        else:
            processo.terminate()
            processo.wait(timeout=10)
        log.info("Streamlit encerrado")
    except Exception as e:
        log.warning(f"Aviso ao encerrar Streamlit: {e}")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    log.info("=" * 60)
    log.info(
        f"INÍCIO DO PROCESSO: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    log.info("=" * 60)

    processo = iniciar_streamlit()

    if not processo:
        log.error("Falha ao iniciar o servidor Streamlit — processo abortado")
        sys.exit(1)

    try:
        imagem = tirar_print_validado()
        sucesso = enviar_email(imagem)

        if sucesso:
            log.info("PROCESSO CONCLUÍDO COM SUCESSO")
        else:
            log.error("PROCESSO CONCLUÍDO COM FALHA — e-mail não foi enviado")
            sys.exit(1)

    finally:
        encerrar_streamlit(processo)
        log.info("=" * 60)


if __name__ == "__main__":
    main()
