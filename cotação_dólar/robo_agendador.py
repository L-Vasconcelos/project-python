import os
import sys
import time
import subprocess
import smtplib
import urllib.request
import urllib.error
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime

# Bibliotecas de Automação Web (Selenium)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service  # ADICIONADO
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# ADICIONADO PARA AUTO-UPDATE
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURAÇÕES DE CAMINHOS ---
PASTA_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))
NOME_ARQUIVO_DASHBOARD = "enviar_relatorio_dolar.py"
CAMINHO_COMPLETO_DASHBOARD = os.path.join(
    PASTA_DO_SCRIPT, NOME_ARQUIVO_DASHBOARD)

# Configurações de Rede
PORTA_STREAMLIT = "8501"
URL_DASHBOARD = f"http://127.0.0.1:{PORTA_STREAMLIT}"

# --- CONFIGURAÇÕES DE E-MAIL ---
EMAIL_REMETENTE = "bi@mtcs.com.br"
EMAIL_DESTINATARIO = "bi@mtcs.com.br, leonardo@mtcs.com.br, comercial2@mtcs.com.br, comercial5@mtcs.com.br"
# DICA: Se a senha estiver no ambiente, use o nome da VARIÁVEL, não o e-mail.
# Ex: SENHA_EMAIL = os.getenv('SENHA_SISTEMA_BI')
SENHA_EMAIL = os.getenv('bi@mtcs.com.br')


def iniciar_streamlit():
    """Inicia o dashboard garantindo o caminho correto e aguarda ficar online."""
    print(f"🚀 Iniciando Streamlit...")

    if not os.path.exists(CAMINHO_COMPLETO_DASHBOARD):
        print(f"❌ ERRO: Arquivo não encontrado: {CAMINHO_COMPLETO_DASHBOARD}")
        return None

    comando = [
        sys.executable, "-m", "streamlit", "run",
        CAMINHO_COMPLETO_DASHBOARD,
        "--server.port", PORTA_STREAMLIT,
        "--server.headless", "true",
        "--server.address", "127.0.0.1"
    ]

    processo = subprocess.Popen(
        comando,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    print("⏳ Aguardando o servidor Streamlit ficar online...")

    tempo_maximo = 45
    inicio = time.time()
    servidor_online = False

    while time.time() - inicio < tempo_maximo:
        try:
            # Tenta conectar na URL
            req = urllib.request.Request(URL_DASHBOARD)
            with urllib.request.urlopen(req) as response:
                if response.getcode() == 200:
                    servidor_online = True
                    print(
                        f"✅ Streamlit online em {round(time.time() - inicio, 1)} segundos!")
                    break
        except:
            time.sleep(2)  # Espera um pouco mais entre tentativas

    if not servidor_online:
        print("⚠️ Erro: Streamlit não iniciou a tempo.")

    return processo


def tirar_print_memoria():
    """Abre navegador, verifica erros e tira print."""
    print("📸 Preparando navegador...")

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # Headless moderno
    chrome_options.add_argument("--window-size=1920,2200")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--hide-scrollbars")

    driver = None
    try:
        # CORREÇÃO: Usando Service e WebDriver Manager para evitar erros de versão do ChromeDriver
        servico = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=servico, options=chrome_options)

        driver.get(URL_DASHBOARD)
        print("⏳ Aguardando renderização (máx 60s)...")

        wait = WebDriverWait(driver, 60)
        # Espera até que o corpo do Streamlit apareça
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'div.stApp')))

        # Tempo extra para os gráficos carregarem
        time.sleep(8)

        # Forçar carregamento (scroll)
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

        # Verificar se há erros na tela
        alertas = driver.find_elements(By.CSS_SELECTOR, 'div[role="alert"]')
        if alertas:
            print("❌ Erro detectado na tela do Streamlit. Abortando print.")
            driver.quit()
            return None

        img_binaria = driver.get_screenshot_as_png()
        print("✅ Print capturado com sucesso!")
        driver.quit()
        return img_binaria

    except Exception as e:
        print(f"❌ Falha no Selenium: {e}")
        if driver:
            driver.quit()
        return None


def enviar_email(img_data):
    """Envia o e-mail com a imagem."""
    print("📧 Enviando e-mail...")

    if not SENHA_EMAIL:
        print("❌ ERRO: Senha de e-mail não configurada no ambiente.")
        return

    msg = MIMEMultipart('related')
    msg['Subject'] = f"Fechamento Câmbio - {datetime.now().strftime('%d/%m/%Y')}"
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINATARIO

    html_body = f"""
    <html>
      <body>
        <p>Bom dia,<br><br>Segue o relatório de fechamento:</p>
        <img src="cid:imagem_dolar" style="border:1px solid #ddd; width:1000px;">
        <p style="color:#888; font-size:12px;">Relatório automático gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html_body, 'html'))

    try:
        image = MIMEImage(img_data)
        image.add_header('Content-ID', '<imagem_dolar>')
        msg.attach(image)

        server = smtplib.SMTP('smtp.office365.com', 587)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_EMAIL)
        server.send_message(msg)
        server.quit()
        print("✅ E-mail enviado!")
    except Exception as e:
        print(f"❌ Erro no envio de e-mail: {e}")


def main():
    processo = iniciar_streamlit()
    if processo:
        try:
            imagem = tirar_print_memoria()
            if imagem:
                enviar_email(imagem)
        finally:
            print("🛑 Encerrando Streamlit...")
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(processo.pid)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("🏁 Finalizado.")


if __name__ == "__main__":
    main()
