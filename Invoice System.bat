@echo off

REM Run the Flask app with Waitress
echo Starting the Flask app with Waitress...
start /B waitress-serve --host=0.0.0.0 --port=5000 app:app

REM Wait for 5 seconds to allow the server to start
timeout /t 5 /nobreak > NUL

REM Open the localhost in a new Chrome window
start chrome --new-window http://127.0.0.1:5000
