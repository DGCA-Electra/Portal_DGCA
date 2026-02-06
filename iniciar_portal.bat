@echo off
cd /d C:\DGCA

:: O segredo esta aqui: apontar para .venv\Scripts\python.exe
"C:\DGCA\.venv\Scripts\python.exe" -m streamlit run home.py --server.port 443 --server.address 0.0.0.0 --server.sslCertFile "C:\DGCA\cert.pem" --server.sslKeyFile "C:\DGCA\key.pem"

pause