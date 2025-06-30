@echo off
rem Se placer dans le dossier du batch (où se trouve le script)
cd /d "%~dp0"
rem Lancer le script avec pythonw pour masquer la console
start "" pythonw "interface_generator_qr.pyw"
