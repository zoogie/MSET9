py -V >nul 2>&1 && (
    py -3 mset9.py
) || (
    echo Python 3 is not installed.
    echo Please install Python 3 and try again.
    echo https://www.python.org/downloads/
)
pause
