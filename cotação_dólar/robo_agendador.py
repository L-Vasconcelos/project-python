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
EMAIL_DESTINATARIO = "bi@mtcs.com.br"

# ATENÇÃO: Se você renomeou no Windows para SENHA_EMAIL, use assim.
# Se deixou como bi@mtcs.com.br, altere dentro do getenv()
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
    
    # --- SISTEMA DE ESPERA DINÂMICA ---
    print("⏳ Aguardando o servidor Streamlit ficar online...")
    time.sleep(3) # Dá um fôlego inicial para o processo do Streamlit abrir a porta
    
    tempo_maximo = 45 # Dá até 45 segundos para o Streamlit iniciar
    inicio = time.time()
    servidor_online = False

    while time.time() - inicio < tempo_maximo:
        try:
            # Tenta acessar a URL do dashboard
            codigo_resposta = urllib.request.urlopen(URL_DASHBOARD).getcode()
            if codigo_resposta == 200:
                servidor_online = True
                tempo_decorrido = round(time.time() - inicio, 1)
                print(f"✅ Streamlit online em {tempo_decorrido} segundos!")
                break
        except (urllib.error.URLError, ConnectionError, Exception):
            # O servidor ainda não está pronto ou a conexão foi recusada, espera 1 segundo e tenta de novo
            time.sleep(1)

    if not servidor_online:
        print("⚠️ Aviso: O Streamlit demorou muito para responder. O Selenium pode falhar.")

    return processo


def tirar_print_memoria():
    """Abre navegador, força a rolagem para carregar gráficos e tira print."""
    print("📸 Preparando navegador...")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,2200")
    chrome_options.add_argument("--hide-scrollbars")
    chrome_options.add_argument("--log-level=3")

    driver = None
    try:
        # INICIALIZAÇÃO SIMPLIFICADA USANDO O SELENIUM MANAGER NATIVO
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(URL_DASHBOARD)

        print("⏳ Aguardando montagem inicial (30s)...")
        time.sleep(30)

        # Rolar a tela para baixo e para cima para forçar o JavaScript a desenhar os gráficos
        print("🔄 Simulando rolagem de tela para forçar carregamento dos gráficos...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(10) # Dá tempo para os gráficos desenharem
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(5)  # Volta pro topo para estabilizar a foto

        # CAPTURA A IMAGEM DIRETO PARA A MEMÓRIA (FORMATO BINÁRIO)
        img_binaria = driver.get_screenshot_as_png()
        print("✅ Print capturado com sucesso na memória!")

        driver.quit()
        return img_binaria

    except Exception as e:
        print(f"❌ Erro ao tirar print: {e}")
        if driver:
            driver.quit()
        return None


def enviar_email(img_data):
    """Envia o e-mail recebendo a imagem direto da memória."""
    print("📧 Preparando envio (Imagem Inline)...")

    if not SENHA_EMAIL:
        print("❌ ERRO CRÍTICO: Variável de senha não encontrada.")
        return

    msg = MIMEMultipart('related')
    msg['Subject'] = f"Fechamento Câmbio (Dólar/Euro) (D-1) - {datetime.now().strftime('%d/%m/%Y')}"
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINATARIO

    html_body = """
    <html>
      <body>
        <p style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
            Bom dia,<br><br>
            Segue abaixo o painel de fechamento atualizado (D-1):
        </p>
        <br>
        <img src="cid:imagem_dolar" alt="Relatório Câmbio" style="max-width: 100%; height: auto; border: 1px solid #ddd;">
        <br><br>
        <p style="font-size: 12px; color: #888;">Luís Fellipe Vasconcelos<br>
Data Analytics<br>
Meridional Oleochemicals & Ingredients<br>
Phone: +55 (43) 3315-1289<br>
Mobile/Whatsapp: +55 (43) 99172-7932<br>
Skype: Bi@mtcs.com<br>
Av. Maringá, 1880, Londrina PR, Brasil, 86060-000
</p>
      </body>
    </html>
    """
    msg_html = MIMEText(html_body, 'html')
    msg.attach(msg_html)

    try:
        # Usa a variável img_data (que já está na memória) em vez de ler de um arquivo
        image = MIMEImage(img_data)
        image.add_header('Content-ID', '<imagem_dolar>')
        image.add_header('Content-Disposition', 'inline',
                         filename="relatorio_cambio.png")
        msg.attach(image)

    except Exception as e:
        print(f"❌ Erro ao processar imagem para e-mail: {e}")
        return

    # Envio
    try:
        server = smtplib.SMTP('smtp.office365.com', 587)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_EMAIL)
        server.send_message(msg)
        server.quit()
        print("✅ E-mail enviado com sucesso!")
    except Exception as e:
        print(f"❌ Falha no envio: {e}")


def main():
    processo = None
    try:
        processo = iniciar_streamlit()
        if processo:
            # Pega a imagem direto na memória
            dados_da_imagem = tirar_print_memoria()
            if dados_da_imagem:
                # Envia a imagem passando os dados binários
                enviar_email(dados_da_imagem)
        else:
            print("⚠️ Erro ao iniciar Streamlit.")

    finally:
        if processo:
            print("🛑 Encerrando processo Streamlit...")
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(processo.pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except:
                pass
            print("🏁 Finalizado.")


if __name__ == "__main__":
    main()