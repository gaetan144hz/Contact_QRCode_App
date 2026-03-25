@echo off
chcp 65001 >nul

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
IF ERRORLEVEL 1 (
    echo Echec installation des dependances. pip non installé ?
    pause
    exit /b 1
)

echo Installation terminee !
pause