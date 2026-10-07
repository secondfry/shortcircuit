#!/bin/bash

pyside6-uic --from-imports resources/ui/gui_main.ui -o src/shortcircuit/view/gui_main.py
pyside6-uic --from-imports resources/ui/gui_tripwire.ui -o src/shortcircuit/view/gui_tripwire.py
pyside6-uic --from-imports resources/ui/gui_mappers.ui -o src/shortcircuit/view/gui_mappers.py
pyside6-uic --from-imports resources/ui/gui_about.ui -o src/shortcircuit/view/gui_about.py
pyside6-rcc --compress-algo zlib resources/resources.qrc -o src/shortcircuit/view/resources_rc.py
