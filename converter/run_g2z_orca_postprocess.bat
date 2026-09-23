@echo off
REM Author: Marcin Kowalik <mkowalik@agh.edu.pl>
REM SPDX-License-Identifier: MIT
setlocal
set SCRIPT_DIR=%~dp0
py -3 -u "%SCRIPT_DIR%g2z_wrapper_orca.py" %*
if errorlevel 1 pause
exit /b %errorlevel%
