#!/bin/bash

python -O -m PyInstaller \
    --clean \
    --windowed \
    --icon src/shortcircuit/resources/images/app_icon.icns \
    --name shortcircuit src/main.py \
    --noupx \
    --osx-bundle-identifier ru.secondfry.shortcircuit \
    --target-architecture universal2
