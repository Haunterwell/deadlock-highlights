@echo off
chcp 65001 >nul
title Deadlock Highlights - instalacao
cd /d "%~dp0"
echo.
echo  === Deadlock Highlights - instalacao ===
echo.

set "PYEXE="
for %%V in (3.13 3.12 3.14 3.11) do (
  if not defined PYEXE (
    py -%%V -c "import sys" >nul 2>&1 && set "PYEXE=py -%%V"
  )
)

if not defined PYEXE (
  echo  Nao encontrei o Python 3.11 a 3.14 neste PC.
  echo  Vou instalar o Python 3.13 pelo winget ^(o instalador oficial do Windows^).
  echo.
  winget install -e --id Python.Python.3.13 --accept-package-agreements --accept-source-agreements
  if errorlevel 1 (
    echo.
    echo  Nao consegui instalar automaticamente.
    echo  Baixe o Python 3.13 em https://www.python.org/downloads/ ^(marque "Add python.exe to PATH"^)
    echo  e rode este instalador de novo.
    pause
    exit /b 1
  )
  set "PYEXE=py -3.13"
)

echo  Usando: %PYEXE%
echo  Criando o ambiente do app ^(pasta .venv^)...
%PYEXE% -m venv .venv || goto :erro
echo  Instalando o leitor de replays ^(boon-deadlock^)... pode levar 1 a 2 minutos.
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q --only-binary=:all: -r requirements.txt || goto :erro

echo  Criando atalho na Area de Trabalho...
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\Deadlock Highlights.lnk'); $s.TargetPath='%~dp0.venv\Scripts\pythonw.exe'; $s.Arguments='\"%~dp0app.py\"'; $s.WorkingDirectory='%~dp0'; $s.IconLocation='%SystemRoot%\System32\shell32.dll,115'; $s.Save()"

echo.
echo  Pronto! Abra pelo atalho "Deadlock Highlights" na Area de Trabalho
echo  ou pelo arquivo "Abrir Deadlock Highlights.bat" nesta pasta.
echo.
pause
exit /b 0

:erro
echo.
echo  Deu erro na instalacao. Veja a mensagem acima.
pause
exit /b 1
