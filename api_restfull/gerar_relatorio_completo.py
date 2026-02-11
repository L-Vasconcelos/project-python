import subprocess
import time
from datetime import datetime

# Lista com o nome exato dos seus 3 scripts
lista_scripts = [
    "C:\\Users\\lsilva\\OneDrive\\Arquivos\\Python\\api_restfull\\dinamica_daily_chemical.py",
    "C:\\Users\\lsilva\\OneDrive\\Arquivos\\Python\\api_restfull\\dinamica_pogo.py",
    "C:\\Users\\lsilva\\OneDrive\\Arquivos\\Python\\api_restfull\\dinamica_sunsirs.py"
]

print(f"--- Iniciando Geração do Excel: {datetime.now()} ---")

for script in lista_scripts:
    print(f"Executando: {script}...")
    try:
        # O comando abaixo roda o script e ESPERA ele terminar para ir pro próximo
        resultado = subprocess.run(["python", script], check=True)
        print(f"--> {script} finalizado com sucesso.")

        # Uma pequena pausa de 2 segundos para garantir que o Excel foi salvo e fechado pelo sistema
        time.sleep(2)

    except subprocess.CalledProcessError as e:
        print(f"ERRO ao rodar {script}: {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")

print("--- Processo Finalizado ---")
