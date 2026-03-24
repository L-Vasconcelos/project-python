robo_agendador

import os
import sys
import time
import subprocess
import smtplib
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime

# Bibliotecas de Automação Web (Selenium)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURAÇÕES DE CAMINHOS ---
PASTA_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))
NOME_ARQUIVO_DASHBOARD = "enviar_relatorio_dolar.py"
CAMINHO_COMPLETO_DASHBOARD = os.path.join(PASTA_DO_SCRIPT, NOME_ARQUIVO_DASHBOARD)

# Configurações de Rede
PORTA_STREAMLIT = "8501"
URL_DASHBOARD = f"http://127.0.0.1:{PORTA_STREAMLIT}"

# --- CONFIGURAÇÕES DE E-MAIL ---
EMAIL_REMETENTE = "bi@mtcs.com.br"
EMAIL_DESTINATARIO = "bi@mtcs.com.br"
SENHA_EMAIL = os.getenv('bi@mtcs.com.br')

def iniciar_streamlit():
    """Inicia o dashboard e aguarda ficar online."""
    print(f"🚀 Iniciando Streamlit ({NOME_ARQUIVO_DASHBOARD})...")

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

    try:
        if os.name == 'nt': # Windows
            subprocess.run(["taskkill", "/F", "/IM", "streamlit.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(["pkill", "-f", "streamlit"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass

    processo = subprocess.Popen(
        comando,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    print("⏳ Aguardando o servidor Streamlit ficar online...")
    tempo_maximo = 60
    inicio = time.time()
    servidor_online = False

    while time.time() - inicio < tempo_maximo:
        try:
            req = urllib.request.Request(URL_DASHBOARD)
            with urllib.request.urlopen(req) as response:
                if response.getcode() == 200:
                    servidor_online = True
                    print(f"✅ Streamlit online em {round(time.time() - inicio, 1)}s!")
                    break
        except:
            time.sleep(2)

    if not servidor_online:
        print("⚠️ Erro: Streamlit não iniciou a tempo.")
        return None

    return processo

def tirar_print_validado():
    """Abre navegador, valida o carregamento total e tira print."""
    print("📸 Preparando captura do dashboard...")

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,2400")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3") # Silenciar logs do Chrome

    driver = None
    try:
        # SIMPLIFICAÇÃO: Removido ChromeDriverManager para evitar travamento no Python 3.13
        # O Selenium moderno (v4.6+) já gerencia o driver automaticamente
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(URL_DASHBOARD)
        
        print("⏳ Aguardando validação dos dados no dashboard...")
        wait = WebDriverWait(driver, 60)
        
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.stApp')))
        
        try:
            wait.until(EC.presence_of_element_located((By.ID, 'dashboard-ready')))
            print("✅ Dashboard validado com sucesso (READY).")
        except:
            if driver.find_elements(By.ID, 'dashboard-error'):
                print("❌ ERRO: O dashboard reportou erro interno de processamento.")
            else:
                print("❌ ERRO: Timeout na renderização ou dados ausentes.")
            driver.quit()
            return None

        time.sleep(5)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        img_binaria = driver.get_screenshot_as_png()
        print("✅ Print capturado com sucesso!")
        driver.quit()
        return img_binaria

    except Exception as e:
        print(f"❌ Falha crítica no Selenium: {e}")
        if driver:
            driver.quit()
        return None

def enviar_email(img_data):
    """Envia o e-mail apenas se houver imagem válida."""
    if not img_data:
        print("🛑 Abortando envio: Não há imagem válida para enviar.")
        return False

    print("📧 Preparando envio de e-mail...")
    if not SENHA_EMAIL:
        print("❌ ERRO: Senha de e-mail (variável 'bi@mtcs.com.br') não encontrada.")
        return False

    msg = MIMEMultipart('related')
    data_hoje = datetime.now().strftime('%d/%m/%Y')
    msg['Subject'] = f"Fechamento Câmbio - {data_hoje}"
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINATARIO

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif;">
        <p>Bom dia,<br><br>Segue o relatório de fechamento de câmbio atualizado:</p>
        <div style="margin: 20px 0;">
            <img src="cid:imagem_dolar" style="border:1px solid #ddd; max-width:100%; height:auto;">
        </div>
        <p style="color:#888; font-size:12px; border-top: 1px solid #eee; padding-top: 10px;">
            Relatório automático gerado pelo Sistema BI em {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html_body, 'html'))

    try:
        image = MIMEImage(img_data)
        image.add_header('Content-ID', '<imagem_dolar>')
        msg.attach(image)

        server = smtplib.SMTP('smtp.office365.com', 587, timeout=30)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_EMAIL)
        server.send_message(msg)
        server.quit()
        print("✅ E-mail enviado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")
        return False

def main():
    print(f"--- INÍCIO DO PROCESSO: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} ---")
    processo = iniciar_streamlit()
    
    if processo:
        try:
            imagem = tirar_print_validado()
            if imagem:
                enviar_email(imagem)
            else:
                print("⚠️ Processo interrompido: O dashboard não estava pronto ou continha erros.")
        finally:
            print("🛑 Encerrando servidor Streamlit...")
            if os.name == 'nt':
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(processo.pid)], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                processo.terminate()
            print("🏁 Processo finalizado.")
    else:
        print("❌ Falha ao iniciar o servidor. O script não prosseguiu para o envio.")

if __name__ == "__main__":
    main()
