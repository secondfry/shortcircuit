#!/bin/bash
#
# Build the macOS .app. Pass the target architecture (arm64, x86_64, or
# universal2); the default is the architecture of the running Python. PySide6
# ships a single universal2 wheel, so either slice builds from the same
# dependency set -- this argument only tells PyInstaller which slice to keep.

target_arch="${1:-}"

arch_args=()
if [ -n "$target_arch" ]; then
    arch_args=(--target-arch "$target_arch")
fi

python -O -m PyInstaller \
    --clean \
    --windowed \
    --icon resources/images/app_icon.icns \
    --add-data 'src/database/*:database' \
    --noconfirm \
    --name shortcircuit src/main.py \
    --noupx \
    "${arch_args[@]}" \
    --osx-bundle-identifier ru.secondfry.shortcircuit

cd dist || exit 1
tar cfz shortcircuit.app.tar.gz shortcircuit.app
