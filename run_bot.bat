@echo off
chcp 65001 > nul
title eFootball Shop Bot Runner

echo Processing setup...
pip install -r requirements.txt --quiet

echo.
echo ===================================================
echo Dashboard is running on: http://localhost:5000
echo Telegram Bot is active.
echo ===================================================
echo.

python main.py

pause