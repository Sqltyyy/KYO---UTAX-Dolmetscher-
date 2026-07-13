@echo off
setlocal

REM Projektpfad deines Kyocera/UTAX-Dolmetschers
set "PROJECT_DIR=C:\Users\tre\Documents\GitHub\KYO---UTAX-Dolmetscher-"

REM In den Projektordner wechseln
cd /d "%PROJECT_DIR%"

REM Wenn eine virtuelle Umgebung vorhanden ist, wird diese Python-Version genutzt.
REM Vorteil: Es ist keine PowerShell-ExecutionPolicy und kein activate-Befehl nötig.
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)


REM Streamlit-App starten
"%PYTHON_EXE%" -m streamlit run app.py --server.port 8501

pause
