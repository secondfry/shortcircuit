#!/bin/bash

python -O -m PyInstaller \
    --clean \
    --windowed \
    --icon src/shortcircuit/resources/images/app_icon.icns \
    --name shortcircuit src/main.py \
    --noupx \
    --osx-bundle-identifier ru.secondfry.shortcircuit

cd dist
tar cfz shortcircuit.app.tar.gz shortcircuit.app
