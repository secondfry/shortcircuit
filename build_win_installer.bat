python -O -m PyInstaller ^
    --clean ^
    --windowed ^
    --icon resources\images\app_icon.ico ^
    --add-data "src\database\*;database" ^
    --noconfirm ^
    --name shortcircuit src\main.py ^
    --onefile ^
    --paths "build\libs" ^
