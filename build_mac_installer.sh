#!/bin/bash

python -O -m PyInstaller \
    --noupx \
    --clean \
    --windowed \
    --icon src/shortcircuit/resources/images/app_icon.ico \
    --name shortcircuit src/main.py
