@echo off
setlocal EnableExtensions

set "LAUNCHER_DIR=%~dp0"
if "%LAUNCHER_DIR%"=="" set "LAUNCHER_DIR=C:\OrcaScripts\"

call :resolve_home
if errorlevel 1 (
    echo [ERROR] Could not determine user home directory.
    pause
    exit /b 1
)

set "HOME_SCRIPTS=%USER_HOME%\OrcaScripts\"
if exist "%HOME_SCRIPTS%g2z_wrapper_orca.py" (
    set "SCRIPT_DIR=%HOME_SCRIPTS%"
    set "SCRIPT_SOURCE=home"
) else (
    set "SCRIPT_DIR=%LAUNCHER_DIR%"
    set "SCRIPT_SOURCE=launcher"
)

cd /d "%SCRIPT_DIR%"

set "WRAPPER=%SCRIPT_DIR%g2z_wrapper_orca.py"
set "LOGFILE=%SCRIPT_DIR%orca_postprocess_last.log"
set "INPUT=%~1"

title Zortrax Inventure - Orca post-process

cls
echo ==========================================
echo Zortrax Inventure - Orca post-process
echo Converter : v1.01
echo ==========================================
echo User home : %USER_HOME%
echo Launcher  : %LAUNCHER_DIR%
echo Script dir: %SCRIPT_DIR%
echo Source    : %SCRIPT_SOURCE%
echo Wrapper   : %WRAPPER%
echo Log file  : %LOGFILE%
echo Input     : %INPUT%
echo [INFO] Script location mode: prefer %%USERPROFILE%%\OrcaScripts, then launcher directory.
echo [INFO] Output mode: Orca environment only. The converter writes to the final Save/Save As path provided by Orca.
echo [INFO] Progress mode: stable plain console output by default.
echo.

if "%INPUT%"=="" (
    echo [ERROR] Missing input file from Orca.
    pause
    exit /b 1
)

if not exist "%WRAPPER%" (
    echo [ERROR] Wrapper not found:
    echo %WRAPPER%
    pause
    exit /b 1
)

call :find_python
if errorlevel 1 (
    echo [ERROR] Python was not found on this system.
    pause
    exit /b 1
)

if not defined G2Z_PROGRESS_STYLE set "G2Z_PROGRESS_STYLE=plain"
set "PYTHONUNBUFFERED=1"
set "G2Z_LOG_FILE=%LOGFILE%"

echo [INFO] Python    : %PYTHON_CMD% %PYTHON_ARGS%
echo [START] Launching converter...
echo.

%PYTHON_CMD% %PYTHON_ARGS% "%WRAPPER%" "%INPUT%" --log
set "ERR=%ERRORLEVEL%"

echo.
if not "%ERR%"=="0" (
    echo [ERROR] Converter exited with code %ERR%.
    echo [INFO] See log: %LOGFILE%
    pause
    exit /b %ERR%
)

echo [OK] Conversion finished successfully.
echo [INFO] Log: %LOGFILE%
exit /b 0

:resolve_home
if defined USERPROFILE (
    set "USER_HOME=%USERPROFILE%"
    exit /b 0
)
if defined HOMEDRIVE if defined HOMEPATH (
    set "USER_HOME=%HOMEDRIVE%%HOMEPATH%"
    exit /b 0
)
if defined HOME (
    set "USER_HOME=%HOME%"
    exit /b 0
)
exit /b 1

:find_python
where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=py"
    set "PYTHON_ARGS=-3 -u"
    exit /b 0
)

where python >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    set "PYTHON_ARGS=-u"
    exit /b 0
)

exit /b 1
