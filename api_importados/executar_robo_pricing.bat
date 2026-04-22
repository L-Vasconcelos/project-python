@echo off
cd /d "C:\Users\lsilva\OneDrive\Arquivos\Python\api_importados"
"C:\Users\lsilva\OneDrive\Arquivos\Python\.venv\Scripts\python.exe" "C:\Users\lsilva\OneDrive\Arquivos\Python\api_importados\robo_pricing.py" >> "C:\Users\lsilva\OneDrive\Arquivos\Python\api_importados\log_bat.txt" 2>&1
echo Codigo de saida: %ERRORLEVEL% >> "C:\Users\lsilva\OneDrive\Arquivos\Python\api_importados\log_bat.txt"
