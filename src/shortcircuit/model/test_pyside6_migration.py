# test_pyside6_migration.py
"""
Regression tests for the PySide2/Qt5 -> PySide6/Qt6 migration.

The migration is mostly mechanical, so these tests lock in its observable
contract rather than re-asserting the diff:

  * the generated ``view/gui_*.py`` artifacts build widgets under PySide6;
  * no Qt5-only API (``PySide2`` imports, the deprecated ``.exec_()``) is
    left anywhere in the hand-written or generated tree;
  * a ``QSettings`` INI file written by the Qt5 build still reads back
    correctly, including the legacy mapper-config migration path;
  * the ``.ui``-backed dialogs open and close under an offscreen platform
    without emitting the ``.exec_()`` deprecation warning.

They live beside the model tests because that is where this repo's suite
lives; the QSettings cases in particular exercise ``mapper_config``.
"""

import ast
import os
import warnings
from pathlib import Path

# The suite is headless: select the Qt platform plugin before Qt is imported.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6 import QtCore, QtWidgets

_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[3]
_SRC = _REPO_ROOT / "src" / "shortcircuit"

# A settings file in the layout the pre-migration (Qt5) build wrote: plain
# scalar keys under [General], the old grouped Tripwire block, and the
# MainWindow group. Kept as a frozen literal so the assertion values are an
# independent source of truth from this repo's writer code.
_QT5_SETTINGS_INI = (
  '[General]\n'
  'avoidance_enabled=true\n'
  'avoidance_list="Jita,Amarr"\n'
  'proxy=http://proxy.example:8080\n'
  '\n'
  '[MainWindow]\n'
  'table_widths="110,75,75,180"\n'
  '\n'
  '[Tripwire]\n'
  'url=https://tw.example\n'
  'user=bob\n'
  'pass=hunter2\n'
  'evescout_enabled=true\n'
)


@pytest.fixture(scope="session")
def qapp():
  app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
  yield app


def _python_sources():
  for path in sorted(_SRC.rglob('*.py')):
    yield path


def test_no_pyside2_or_exec_underscore_left_in_tree():
  """Qt5-only API must be gone from every source file, generated included."""
  offenders = []
  for path in _python_sources():
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    for node in ast.walk(tree):
      if isinstance(node, ast.ImportFrom):
        if (node.module or '').startswith('PySide2'):
          offenders.append(f'{path}:{node.lineno} imports from PySide2')
      elif isinstance(node, ast.Import):
        for alias in node.names:
          if alias.name.startswith('PySide2'):
            offenders.append(f'{path}:{node.lineno} imports {alias.name}')
      elif isinstance(node, ast.Attribute) and node.attr == 'exec_':
        offenders.append(f'{path}:{node.lineno} calls the deprecated exec_()')

  assert offenders == [], 'Qt5-only API left in tree:\n' + '\n'.join(offenders)


def test_generated_ui_modules_build_widgets_under_pyside6(qapp):
  from shortcircuit.view.gui_about import Ui_AboutDialog
  from shortcircuit.view.gui_main import Ui_MainWindow
  from shortcircuit.view.gui_mappers import Ui_MappersDialog
  from shortcircuit.view.gui_tripwire import Ui_TripwireDialog

  cases = [
    (Ui_MainWindow, QtWidgets.QMainWindow, 'tableWidget_path'),
    (Ui_TripwireDialog, QtWidgets.QDialog, 'lineEdit_pass'),
    (Ui_MappersDialog, QtWidgets.QDialog, 'tableWidget_mappers'),
    (Ui_AboutDialog, QtWidgets.QDialog, 'label_title'),
  ]
  for ui_class, host_class, probe in cases:
    host = host_class()
    try:
      ui = ui_class()
      ui.setupUi(host)
      assert host.findChild(QtWidgets.QWidget, probe) is not None, (
        f'{ui_class.__name__} did not build {probe}'
      )
    finally:
      host.close()
      host.deleteLater()


def test_qt5_written_settings_still_read_by_pyside6(tmp_path):
  from shortcircuit.model.mapper_config import (
    TYPE_EVESCOUT,
    TYPE_TRIPWIRE,
    load_configs,
    migrate_legacy,
  )

  path = tmp_path / 'shortcircuit.ini'
  path.write_text(_QT5_SETTINGS_INI, encoding='utf-8')
  settings = QtCore.QSettings(str(path), QtCore.QSettings.IniFormat)

  # Scalars the Qt5 build wrote survive unchanged.
  assert settings.value('proxy') == 'http://proxy.example:8080'
  assert settings.value('avoidance_list') == 'Jita,Amarr'
  assert settings.value('MainWindow/table_widths') == '110,75,75,180'

  # The legacy grouped mapper layout migrates into the current format.
  migrated = migrate_legacy(settings)
  assert migrated is not None
  tripwire = next(c for c in migrated if c.type == TYPE_TRIPWIRE)
  assert (tripwire.url, tripwire.user, tripwire.password) == (
    'https://tw.example', 'bob', 'hunter2',
  )
  evescout = next(c for c in migrated if c.type == TYPE_EVESCOUT)
  assert evescout.enabled is True

  settings.sync()
  assert load_configs(settings) == migrated


class _FakeEvent:

  def __init__(self):
    self.accepted = False

  def accept(self):
    self.accepted = True


def _close_active_modal():
  app = QtWidgets.QApplication.instance()
  modal = app.activeModalWidget() if app is not None else None
  if modal is not None:
    modal.close()


def test_dialog_exec_sites_emit_no_deprecation_warning(qapp):
  from shortcircuit.app import MainWindow, MappersDialog
  from shortcircuit.model.mapper_config import MapperConfig, TYPE_TRIPWIRE

  with warnings.catch_warnings():
    warnings.simplefilter('error', DeprecationWarning)

    event = _FakeEvent()
    QtCore.QTimer.singleShot(0, _close_active_modal)
    MainWindow.banner_click(event)
    assert event.accepted

    dialog = MappersDialog([], '')
    try:
      QtCore.QTimer.singleShot(0, _close_active_modal)
      dialog._edit_tripwire(MapperConfig(type=TYPE_TRIPWIRE, name='Tripwire'))
    finally:
      dialog.close()


if __name__ == '__main__':
  raise SystemExit(pytest.main([__file__, '-v']))
