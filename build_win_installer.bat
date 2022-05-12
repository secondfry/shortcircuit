python -O -m PyInstaller ^
    --clean ^
    --windowed ^
    --icon src\shortcircuit\resources\images\app_icon.ico ^
    --name shortcircuit src\main.py ^
    --onefile ^
    --paths "build\libs" ^
