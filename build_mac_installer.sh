#!/bin/bash

python -O -m PyInstaller \
    --clean \
    --windowed \
    --icon resources/images/app_icon.icns \
    --add-data 'src/database/*;database' \
    --noconfirm \
    --name shortcircuit src/main.py \
    --noupx \
    --osx-bundle-identifier ru.secondfry.shortcircuit

cd dist
tar cfz shortcircuit.app.tar.gz shortcircuit.app
