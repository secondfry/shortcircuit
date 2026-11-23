# test_appearance.py
"""View > Appearance: the saved choice, the colour scheme it asks Qt for, and
the colours that follow the palette Qt actually draws."""

import os

import pytest
from PySide6 import QtCore, QtGui

from shortcircuit import app as app_module
from shortcircuit.app import APPEARANCE_KEY, MainWindow, read_appearance

LIGHT_HS_SHEET = 'QSpinBox { background-color: #DFF0D8; }'
DARK, LIGHT = '#1e1e1e', '#f3f3f3'


@pytest.mark.parametrize('saved, expected', [
  (None, 'system'),
  ('dark', 'dark'),
  ('light', 'light'),
  ('true', 'system'),
])
def test_read_appearance(make_settings, saved, expected):
  values = {} if saved is None else {APPEARANCE_KEY: saved}
  assert read_appearance(make_settings(**values)) == expected


def _palette(window_colour):
  # Built from the button colour, which QPalette also uses for Window.
  return QtGui.QPalette(QtGui.QColor(window_colour))


@pytest.fixture
def window(qapp, tmp_path, monkeypatch):
  # Offscreen Qt ignores scheme requests: record them, and let each test
  # decide whether the style answers with a dark palette.
  requested = []
  monkeypatch.setattr(QtGui.QStyleHints, 'setColorScheme', lambda _, scheme: requested.append(scheme))
  monkeypatch.setattr(app_module.VersionCheck, 'process', lambda _: None)
  ini, user = QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope
  # QSettings(format, scope, org) lives at <scope path>/<org>.ini.
  old_path = os.path.dirname(QtCore.QSettings(ini, user, 'probe').fileName())
  old_palette = qapp.palette()
  QtCore.QSettings.setPath(ini, user, str(tmp_path))
  qapp.setPalette(_palette(LIGHT))
  win = MainWindow()
  win.requested = requested
  yield win
  win.version_thread.quit()
  win.version_thread.wait()
  win.deleteLater()
  QtCore.QSettings.setPath(ini, user, old_path)
  qapp.setPalette(old_palette)


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


def _switch_palette(qapp, window_colour):
  # A scheme switch gives a new application palette; its PaletteChange is
  # posted to the window, so let it arrive.
  qapp.setPalette(_palette(window_colour))
  qapp.processEvents()


def test_dark_palette_darkens_and_light_restores_the_ui_file_background(window, qapp):
  _switch_palette(qapp, DARK)
  assert '#2d4a33' in window.spinBox_prio_hs.styleSheet()
  _switch_palette(qapp, LIGHT)
  assert window.spinBox_prio_hs.styleSheet() == LIGHT_HS_SHEET


def test_dark_request_kept_light_by_the_style_stays_light(window, monkeypatch):
  # windowsvista (Windows 10's default) reports the Dark request from
  # colorScheme() but keeps drawing a light palette.
  monkeypatch.setattr(QtGui.QStyleHints, 'colorScheme', lambda _: window.requested[-1])
  _choose(window, 'dark')
  assert window.spinBox_prio_hs.styleSheet() == LIGHT_HS_SHEET


def test_dark_palette_at_start_up_applies_without_a_palette_event(window, qapp):
  # Under System on a dark OS the palette is already dark at start-up, so no
  # PaletteChange comes; set_appearance must apply the colours itself.
  qapp.setPalette(_palette(DARK))
  window.set_appearance('system')
  assert '#2d4a33' in window.spinBox_prio_hs.styleSheet()
