@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul

py -V > nul 2>&1
if %errorlevel% EQU 0 py -3 mset9.py & exit /B
python -V > nul 2>&1
if %errorlevel% EQU 0 python mset9.py & exit /B else (
  del p.exe 2> nul
  echo Python not found. Do you want to install it? ^(yes or no^)
  set /p pyPrompt="> "
  set confirm=F

  if [%PyPrompt%] EQU [y] set confirm=T
  if [%PyPrompt%] EQU [yes] set confirm=T

  if %confirm% EQU T ( 
    cls
    echo Downloading...
      
    echo 6.1.7601> temp.txt & echo 6.2>> temp.txt & echo 6.3>> temp.txt & echo 10>> temp.txt
    for /F "tokens=*" %%G in (temp.txt) do (
      ver | findstr /i "%%G"> nul
      if !errorlevel! EQU 0 if "%%G" EQU "6.1.7601 " (
        powershell -Command "(New-Object Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.8.10/python-3.8.10.exe', 'p.exe')"
        goto :doneDownloading
      ) else if "%%G" EQU "6.2 " (goto :newWin) else if "%%G" EQU "6.3 " (goto :newWin) else if "%%G" EQU "10" goto :newWin)) else exit /B)

if not exist p.exe (
  cls
  del temp.txt
  echo Your Windows version is not supported. Please use a computer with at least Windows 7 + SP1 and rerun this script.
  pause
  exit /B)

:newWin
 powershell -Command "Invoke-WebRequest https://www.python.org/ftp/python/3.12.2/python-3.12.2-amd64.exe -OutFile p.exe"

:doneDownloading
 del temp.txt
 if !errorlevel! NEQ 0 echo Error downloading Python. Rerun this file again or download and install Python manually. & pause & exit /B    
 echo  Done & echo Installing...
 p.exe /quiet AppendPath=1
 if %errorlevel% NEQ 0 echo Error installing Python. Rerun this file again or install Python manually. & pause & exit /B
 del p.exe & echo  Done
 echo Python installed successfully. Please rerun this script to open MSET9.
 pause & exit
