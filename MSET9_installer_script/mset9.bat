@echo off
chcp 65001 > nul

py -V 2> nul
if %errorlevel% EQU 0 py -3 mset9.py
python -V 2> nul
if %errorlevel% EQU 0 python -3 mset9.py else (
    echo Python not found. Do you want to install it? (yes or no)
    set /p pyPrompt="> "
    set confirm=F    

    if %PyPrompt% EQU y set confirm=T
    if %PyPrompt% EQU yes set confirm=T

    if %confirm% EQU T (
      cls
      echo Downloading...
      
      ver | findstr "6.1" > nul & :: 6.1 = Windows 7
      if %errorlevel% EQU 0 (
        powershell -Command "(New-Object Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.8.10/python-3.8.10.exe', 'python.exe')"
      ) else (
        powershell -Command "Invoke-WebRequest https://www.python.org/ftp/python/3.12.2/python-3.12.2-amd64.exe -OutFile python.exe"
      )

      echo  Done & echo Installing...
      python.exe /quiet PrependPath=1
      del python.exe & echo  Done
      start cmd /K py %cd%\mset9.py
      exit
    ) else (
      exit
    )
)
py -3 mset9.py
