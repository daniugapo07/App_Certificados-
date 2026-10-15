@echo off
REM Iniciar la App de Certificados de Academia Horizonte con doble clic.
REM Para detenerla: pulse Ctrl+C en esta ventana o simplemente cierrela.
cd /d "%~dp0"
uv run app.py
pause
