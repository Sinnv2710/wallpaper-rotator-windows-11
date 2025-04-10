@echo off
REM filepath: d:\software\script\deploy.bat

REM Set the Python script and output executable name
set SCRIPT_NAME=.\index.pyw
set OUTPUT_NAME=rotator.exe

REM Ensure pip is installed
echo Checking for pip...
python -m ensurepip --upgrade >nul 2>&1

REM Install required libraries
echo Installing required libraries...
pip install --upgrade pip >nul 2>&1
pip install -r ..\requirements.txt

REM Kill any running instance of the executable
taskkill /f /im %OUTPUT_NAME% >nul 2>&1

REM Delete the existing executable if it exists
if exist %OUTPUT_NAME% (
    del /f /q %OUTPUT_NAME%
)

REM Build the executable
echo Building the executable...
pyinstaller --noconsole --onefile --icon=icon.jpg --name=%OUTPUT_NAME% %SCRIPT_NAME%

REM Move the built executable to the root folder
if exist dist\%OUTPUT_NAME% (
    move dist\%OUTPUT_NAME% ..\
    echo Build successful! Executable created: %OUTPUT_NAME%
) else (
    echo Build failed. Check the PyInstaller logs for details.
)

REM Clean up build artifacts
echo Cleaning up temporary files...
rmdir /s /q build >nul 2>&1
del .\rotator.exe.spec >nul 2>&1
rmdir /s /q dist >nul 2>&1

echo Done!
pause