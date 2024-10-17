@echo off

REM Run the Flask app
echo Starting the Flask app...
start /B python app.py

REM Wait for 5 seconds to allow the server to start
timeout /t 10 /nobreak > NUL

REM Open the default web browser to the localhost
start http://127.0.0.1:5000
