@echo off
REM Builds dist\StartupTycoon\StartupTycoon.exe and a zip ready for itch.io. Run from the project root.
python -m pip install -r requirements.txt -r requirements-dev.txt || exit /b 1
python -m unittest discover -s tests || exit /b 1
pyinstaller startup_tycoon.spec --noconfirm || exit /b 1
powershell -Command "Compress-Archive -Force -Path dist\StartupTycoon -DestinationPath dist\StartupTycoon-windows.zip"
echo Done: dist\StartupTycoon-windows.zip
