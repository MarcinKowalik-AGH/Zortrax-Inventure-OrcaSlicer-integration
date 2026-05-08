@echo off
setlocal
set SCRIPT_DIR=%~dp0
py -3 -u "%SCRIPT_DIR%g2z_wrapper_orca.py" %*
if errorlevel 1 pause
exit /b %errorlevel%
