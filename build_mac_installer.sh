python -O -m PyInstaller ^
    --clean ^
    --onefile ^
    --windowed ^
    --icon resources\images\app_icon.ico ^
    --name shortcircuit src\main.py ^
    --add-data "resources\database\statics.csv;database" ^
    --add-data "resources\database\system_description.csv;database" ^
    --add-data "resources\database\system_jumps.csv;database" ^