#!/bin/bash

python -O -m PyInstaller \
    --clean \
    --onefile \
    --windowed \
    --icon src/resources/images/app_icon.ico \
    --name shortcircuit src/main.py
