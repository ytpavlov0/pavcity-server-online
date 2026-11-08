@echo off
chcp 65001 >nul
title PAVCITY Sunucu
rem Gerçek zamanlı sunucu arka planda çalışmıyorsa başlatır, sonra konsolu açar.
rem Konsolu kapatmak oyunu kapatmaz; sunucular arka planda çalışmaya devam eder.
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\PAVCITY\support\rt172\start_pavrt172.ps1"
"C:\PAVCITY\support\rt172\pavrt.exe" "C:\PAVCITY"
pause
