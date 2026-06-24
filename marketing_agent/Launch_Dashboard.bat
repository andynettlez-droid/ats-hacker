@echo off
echo Starting ATS Hacker Marketing Dashboard...
start "Flask Server" /B "C:\Users\andyn\AppData\Local\Programs\Python\Python313\python.exe" web_dashboard.py
timeout /t 2 /nobreak > nul
start http://127.0.0.1:5000
exit
