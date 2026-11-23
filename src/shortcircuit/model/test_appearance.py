# test_appearance.py
"""View > Appearance: the saved choice and the colour scheme it asks Qt for."""

import pytest
from PySide6 import QtCore, QtGui

from shortcircuit import app as app_module
from shortcircuit.app import APPEARANCE_KEY, MainWindow, read_appearance


def _settings(tmp_path, **values):
  settings = QtCore.QSettings(str(tmp_path / 'settings.ini'), QtCore.QSettings.IniFormat)
  for key, value in values.items():
    settings.setValue(key, value)
  return settings


@pytest.mark.parametrize('saved, expected', [
  (None, 'system'),
  ('dark', 'dark'),
  ('light', 'light'),
  ('true', 'system'),
])
def test_read_appearance(tmp_path, saved, expected):
  values = {} if saved is None else {APPEARANCE_KEY: saved}
  assert read_appearance(_settings(tmp_path, **values)) == expected


@pytest.fixture
def window(qapp, tmp_path, monkeypatch):
  # Offscreen Qt ignores scheme requests, so record them and fake the result.
  requested = []
  monkeypatch.setattr(QtGui.QStyleHints, 'setColorScheme', lambda _, scheme: requested.append(scheme))
  monkeypatch.setattr(
    QtGui.QStyleHints, 'colorScheme',
    lambda _: requested[-1] if requested else QtCore.Qt.ColorScheme.Unknown,
  )
  monkeypatch.setattr(app_module.VersionCheck, 'process', lambda _: None)
  QtCore.QSettings.setPath(QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope, str(tmp_path))
  win = MainWindow()
  win.requested = requested
  yield win
  win.version_thread.quit()
  win.version_thread.wait()
  win.deleteLater()


def _choose(win, appearance):
  action = next(a for a in win.appearance_group.actions() if a.data() == appearance)
  action.trigger()
  return action


def test_choosing_dark_sets_scheme_and_saves_it(window):
  assert _choose(window, 'dark').isChecked()
  assert window.requested[-1] == QtCore.Qt.ColorScheme.Dark
  window.write_settings()
  window.settings.beginGroup('MainWindow')
  assert read_appearance(window.settings) == 'dark'
  window.settings.endGroup()


def test_choosing_system_hands_scheme_back_to_os(window):
  _choose(window, 'dark')
  _choose(window, 'system')
  assert window.requested[-1] == QtCore.Qt.ColorScheme.Unknown


def test_light_restores_the_ui_file_spinbox_background(window):
  light_sheet = window.spinBox_prio_hs.styleSheet()
  _choose(window, 'dark')
  assert '#2d4a33' in window.spinBox_prio_hs.styleSheet()
  _choose(window, 'light')
  assert window.spinBox_prio_hs.styleSheet() == light_sheet == 'QSpinBox { background-color: #DFF0D8; }'
