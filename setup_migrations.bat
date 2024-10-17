@echo off
SETLOCAL

REM Install dependencies from requirements.txt
REM Check if the migrations folder exists
IF NOT EXIST "migrations" (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo Migrations folder not found, initializing migrations...

    REM Run migration commands
    echo Running migrations...
    flask db init
    flask db migrate -m "Initial migration."
    flask db upgrade
)


REM Create a desktop shortcut for the 'run_app_waitress.bat' file
echo Creating desktop shortcut...

REM Set project directory and target file
set PROJECT_DIR=%cd%
set TARGET_BAT=%PROJECT_DIR%\run_app_waitress.bat

REM Create a VBS script to generate the shortcut
echo Set WshShell = CreateObject("WScript.Shell") > create_shortcut.vbs
echo DesktopPath = WshShell.SpecialFolders("Desktop") >> create_shortcut.vbs
echo Set MyShortcut = WshShell.CreateShortcut(DesktopPath ^& "\Run App - Waitress.lnk") >> create_shortcut.vbs
echo MyShortcut.TargetPath = "%TARGET_BAT%" >> create_shortcut.vbs
echo MyShortcut.WorkingDirectory = "%PROJECT_DIR%" >> create_shortcut.vbs
echo MyShortcut.WindowStyle = 1 >> create_shortcut.vbs
echo MyShortcut.Save >> create_shortcut.vbs

REM Run the VBS script to create the shortcut
cscript //nologo create_shortcut.vbs

REM Clean up the VBS script
del create_shortcut.vbs

echo Shortcut created on the desktop.

ENDLOCAL
