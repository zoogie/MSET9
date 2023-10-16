@echo off
chcp 65001 > nul
py -V > nul
if %errorlevel% NEQ 0 (
    echo Python 3 is not installed.
    echo Please install Python 3 and try again.
    echo https://www.python.org/downloads/
    echo.
    pause
    exit
)
py -3 mset9.py