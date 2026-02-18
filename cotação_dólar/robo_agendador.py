import os
import sys
import time
import subprocess
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime

# Bibliotecas de Automação Web (Selenium)
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURAÇÕES DE CAMINHOS ---
PASTA_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))
NOME_ARQUIVO_DASHBOARD = "enviar_relatorio_dolar.py"
CAMINHO_COMPLETO_DASHBOARD = os.path.join(
    PASTA_DO_SCRIPT, NOME_ARQUIVO_DASHBOARD)

# Configurações de Rede
PORTA_STREAMLIT = "8501"
URL_DASHBOARD = f"http://127.0.0.1:{PORTA_STREAMLIT}"

# Pasta onde os prints serão guardados
PASTA_HISTORICO = r"C:\Users\lsilva\OneDrive\Arquivos\Python\historico_print_ptax"

# --- CONFIGURAÇÕES DE E-MAIL ---
EMAIL_REMETENTE = "bi@mtcs.com.br"
EMAIL_DESTINATARIO = "bi@mtcs.com.br"

# ATENÇÃO: Se você renomeou no Windows para SENHA_EMAIL, use assim.
# Se deixou como bi@mtcs.com.br, altere dentro do getenv()
SENHA_EMAIL = os.getenv('bi@mtcs.com.br')


def iniciar_streamlit():
    """Inicia o dashboard garantindo o caminho correto."""
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
    time.sleep(12)
    return processo


def tirar_print():
    """Abre navegador e tira print."""
    print("📸 Preparando navegador...")

    if not os.path.exists(PASTA_HISTORICO):
        os.makedirs(PASTA_HISTORICO)

    data_hoje = datetime.now().strftime('%Y-%m-%d')
    nome_arquivo = f"fechamento_{data_hoje}.png"
    caminho_completo = os.path.join(PASTA_HISTORICO, nome_arquivo)

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--hide-scrollbars")
    chrome_options.add_argument("--log-level=3")

    driver = None
    try:
        driver = webdriver.Chrome(service=Service(
            ChromeDriverManager().install()), options=chrome_options)
        driver.get(URL_DASHBOARD)

        print("⏳ Aguardando renderização (50s)...")
        time.sleep(50)

        driver.save_screenshot(caminho_completo)
        print(f"✅ Print salvo em: {caminho_completo}")
        driver.quit()
        return caminho_completo

    except Exception as e:
        print(f"❌ Erro ao tirar print: {e}")
        if driver:
            driver.quit()
        return None


def enviar_email(caminho_imagem):
    """Envia o e-mail com a imagem EMBUTIDA NO CORPO (HTML)."""
    print("📧 Preparando envio (Imagem Inline)...")

    if not SENHA_EMAIL:
        print("❌ ERRO CRÍTICO: Variável de senha não encontrada.")
        return

    # 1. Cria o objeto da mensagem como 'related' (necessário para imagens inline)
    msg = MIMEMultipart('related')
    msg['Subject'] = f"Fechamento Dólar (PTAX) (D-1) - {datetime.now().strftime('%d/%m/%Y')}"
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINATARIO

    # 2. Cria o corpo do e-mail em HTML
    # Note a tag <img src="cid:imagem_dolar">. É ela que puxa a imagem.
    html_body = """
    <html>
      <body>
        <p style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
            Bom dia,<br><br>
            Segue abaixo o painel de fechamento atualizado (D-1):
        </p>
        <br>
        <img src="cid:imagem_dolar" alt="Relatório Dólar" style="max-width: 100%; height: auto; border: 1px solid #ddd;">
        <br><br>
        <p style="font-size: 12px; color: #888;">Luís Fellipe Vasconcelos
Data Analytics
Meridional Oleochemicals & Ingredients
Phone: +55 (43) 3315-1289
Mobile/Whatsapp: +55 (43) 99172-7932
Skype: Bi@mtcs.com
Av. Maringá, 1880, Londrina PR, Brasil, 86060-000
</p>
      </body>
    </html>
    """
    # Anexa o HTML na mensagem
    msg_html = MIMEText(html_body, 'html')
    msg.attach(msg_html)

    try:
        # 3. Carrega e Prepara a Imagem
        with open(caminho_imagem, 'rb') as f:
            img_data = f.read()

        image = MIMEImage(img_data)

        # O SEGREDINHO: Adiciona o cabeçalho Content-ID
        # Esse ID '<imagem_dolar>' tem que ser IGUAL ao usado no HTML src="cid:..."
        image.add_header('Content-ID', '<imagem_dolar>')
        image.add_header('Content-Disposition', 'inline',
                         filename=os.path.basename(caminho_imagem))

        msg.attach(image)

    except FileNotFoundError:
        print(f"❌ Imagem não encontrada.")
        return

    # 4. Envio
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
            caminho_da_foto = tirar_print()
            if caminho_da_foto:
                enviar_email(caminho_da_foto)
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
