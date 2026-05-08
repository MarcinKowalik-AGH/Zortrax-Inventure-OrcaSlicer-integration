@echo off
setlocal
cd /d "%~dp0\.."
py -3 -m pip install -r build\requirements-build.txt
py -3 -m PyInstaller --clean --onedir --name g2z_wrapper_orca --add-data "converter\g2z_wrapper_orca_base_lab14_known_good.py;." converter\g2z_wrapper_orca.py
copy /Y converter\g2z_wrapper_orca_base_lab14_known_good.py dist\g2z_wrapper_orca\g2z_wrapper_orca_base_lab14_known_good.py >nul
echo Built dist\g2z_wrapper_orca\g2z_wrapper_orca.exe
pause
