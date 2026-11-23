import os

# The suite is headless: select the Qt platform plugin before Qt is imported.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6 import QtWidgets


@pytest.fixture(scope="session")
def qapp():
  app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
  yield app
