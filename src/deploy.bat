@echo off
REM filepath: d:\software\script\deploy.bat

REM Set working directory to the batch file location
cd /d %~dp0

REM Set the Python script and output executable name
set SCRIPT_NAME=index.pyw
set OUTPUT_NAME=rotator.exe
set SHORTCUT_NAME=RotatorShortcut.lnk

REM Check if Python is available
where python >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    pause
    exit /b
)

REM Ensure pip is installed
echo Checking for pip...
python -m ensurepip --upgrade >nul 2>&1

REM Install required libraries
echo Installing required libraries...
@REM pip install --upgrade pip >nul 2>&1
@REM pip install -r requirements.txt

REM Kill any running instance of the executable
taskkill /f /im %OUTPUT_NAME% >nul 2>&1

REM Delete the existing executable if it exists
if exist %OUTPUT_NAME% (
    del /f /q %OUTPUT_NAME%
)

REM Remove the dist folder if it exists
if exist dist (
    echo Removing existing dist folder...
    rmdir /s /q dist
)

REM Build the executable
echo Building the executable...
pyinstaller --noconsole --onedir --icon=icon.jpg --add-data "icon.jpg;." --name=compile %SCRIPT_NAME%

:: If build is successful, rename and create shortcut
if exist dist\compile\compile.exe (
    echo Build succeeded. Renaming and creating shortcut...
    ren dist\compile\compile.exe %OUTPUT_NAME%
) else (
    echo Build failed. Check PyInstaller logs for more details.
)

:: Write VBScript with PROPER quotes
> CreateShortcut.vbs echo Set oWS = CreateObject("WScript.Shell")
>>CreateShortcut.vbs echo sLinkFile = oWS.CurrentDirectory ^& "\..\%SHORTCUT_NAME%"
>>CreateShortcut.vbs echo Set oLink = oWS.CreateShortcut(sLinkFile)
>>CreateShortcut.vbs echo oLink.TargetPath = oWS.CurrentDirectory ^& "\dist\compile\%OUTPUT_NAME%"
>>CreateShortcut.vbs echo oLink.WorkingDirectory = oWS.CurrentDirectory ^& "\dist\compile"
>>CreateShortcut.vbs echo oLink.IconLocation = oWS.CurrentDirectory ^& "\dist\compile\_internal\icon.jpg"
>>CreateShortcut.vbs echo oLink.Save

:: Run VBScript to create shortcut
cscript //nologo CreateShortcut.vbs
del CreateShortcut.vbs

echo Shortcut created: ..\%SHORTCUT_NAME%

REM Clean up build artifacts
echo Cleaning up temporary files...
rmdir /s /q build >nul 2>&1
del compile.spec >nul 2>&1
@REM rmdir /s /q dist >nul 2>&1

echo Done!
exit /b
REM End of script
