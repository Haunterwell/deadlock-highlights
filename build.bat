@echo off
rem Gera dist\DeadlockHighlights-Setup-<versao>.exe
rem Precisa de: Python 3.11-3.14 (py launcher) e Inno Setup 6 (winget install JRSoftware.InnoSetup)
setlocal
cd /d "%~dp0"

set "PY="
for %%V in (3.13 3.12 3.14 3.11) do (
  if not defined PY ( py -%%V -c "import sys" >nul 2>&1 && set "PY=py -%%V" )
)
if not defined PY ( echo Python 3.11-3.14 nao encontrado. & exit /b 1 )

if not exist ".venv\Scripts\python.exe" ( %PY% -m venv .venv || exit /b 1 )
".venv\Scripts\python.exe" -m pip install --only-binary=:all: -q -r requirements.txt pyinstaller || exit /b 1

rem pasta curta: o Windows nao carrega a DLL do Python se o caminho for muito longo
set "OUT=%TEMP%\dlhb"
if exist "%OUT%\dist" rmdir /s /q "%OUT%\dist"
".venv\Scripts\pyinstaller.exe" --noconfirm --clean --windowed --onedir --name DeadlockHighlights ^
  --icon "%~dp0assets\icon.ico" --add-data "%~dp0assets\icon.ico;assets" ^
  --version-file "%~dp0build_tools\version_info.txt" ^
  --collect-all boon --collect-binaries polars --copy-metadata boon-deadlock ^
  --distpath "%OUT%\dist" --workpath "%OUT%\work" --specpath "%OUT%" app.py || exit /b 1

set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" ( echo Inno Setup 6 nao encontrado. & exit /b 1 )
"%ISCC%" /Q "/DDistDir=%OUT%\dist\DeadlockHighlights" installer\DeadlockHighlights.iss || exit /b 1
echo.
echo Pronto: & dir /b dist\*.exe
