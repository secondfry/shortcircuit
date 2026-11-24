# test_launch_flow.py
"""Auto-location after login, the swap button, and the startup fetch.

These exercise MainWindow's handlers on a stand-in object holding just the
widgets they touch, so no settings, database or network are involved.
"""

import os

# The suite is headless: select the Qt platform plugin before Qt is imported.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest import mock

import pytest
from PySide6 import QtWidgets


@pytest.fixture(scope="session")
def qapp():
  app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
  yield app


class _Window:
  """The parts of MainWindow the flow handlers read and write."""

  def __init__(self):
    from shortcircuit.app import MainWindow
    self.lineEdit_source = QtWidgets.QLineEdit()
    self.lineEdit_destination = QtWidgets.QLineEdit()
    self.pushButton_player_location = QtWidgets.QPushButton()
    self.state_eve_connection = {"connected": False, "char_name": None, "error": None}
    self.esip = mock.Mock()
    self.worker_thread = mock.Mock()
    self.worker_thread.isRunning.return_value = False
    self._message_box = mock.Mock()
    self._status_eve_connection_update = mock.Mock()
    self.btn_trip_get_clicked = mock.Mock()
    from shortcircuit.model.mapper_config import TYPE_EVESCOUT, MapperConfig
    self.mapper_configs = [MapperConfig(type=TYPE_EVESCOUT, name="Eve Scout")]
    for name in (
      "login_handler", "location_handler", "btn_player_location_clicked",
      "btn_swap_clicked", "_startup_fetch", "_mappers_ready",
    ):
      setattr(self, name, getattr(MainWindow, name).__get__(self))


def test_login_fetches_location_and_fills_empty_source(qapp):
  w = _Window()
  w.login_handler(True, "Cormorant Fell")
  w.esip.get_location.assert_called_once()
  w.location_handler("Perimeter")
  assert w.lineEdit_source.text() == "Perimeter"


def test_failed_login_does_not_fetch_location(qapp):
  w = _Window()
  w.login_handler(False, None)
  w.esip.get_location.assert_not_called()


def test_automatic_fill_never_overwrites_a_typed_source(qapp):
  w = _Window()
  w.lineEdit_source.setText("Jita")
  w.login_handler(True, "Cormorant Fell")
  w.location_handler("Perimeter")
  assert w.lineEdit_source.text() == "Jita"


def test_automatic_failure_is_silent_but_manual_failure_reports(qapp):
  w = _Window()
  w.login_handler(True, "Cormorant Fell")
  w.location_handler("")  # pilot offline / ESI error
  w._message_box.assert_not_called()

  w.btn_player_location_clicked()
  w.location_handler("")
  w._message_box.assert_called_once()


def test_manual_location_overwrites_the_source(qapp):
  w = _Window()
  w.lineEdit_source.setText("Jita")
  w.btn_player_location_clicked()
  w.location_handler("Perimeter")
  assert w.lineEdit_source.text() == "Perimeter"


def test_swap_exchanges_source_and_destination(qapp):
  w = _Window()
  w.lineEdit_source.setText("Perimeter")
  w.lineEdit_destination.setText("Amarr")
  w.btn_swap_clicked()
  assert (w.lineEdit_source.text(), w.lineEdit_destination.text()) == ("Amarr", "Perimeter")


def test_startup_fetch_runs_once_unless_a_fetch_is_already_running(qapp):
  w = _Window()
  w._startup_fetch()
  w.btn_trip_get_clicked.assert_called_once()

  w.btn_trip_get_clicked.reset_mock()
  w.worker_thread.isRunning.return_value = True
  w._startup_fetch()
  w.btn_trip_get_clicked.assert_not_called()


def test_startup_fetch_skips_a_mapper_without_credentials(qapp):
  # A fresh install: the default Tripwire is enabled but has no account.
  from shortcircuit.model.mapper_config import default_configs
  w = _Window()
  w.mapper_configs = default_configs()
  w._startup_fetch()
  w.btn_trip_get_clicked.assert_not_called()


def test_swap_button_is_in_the_window(qapp):
  from shortcircuit.view.gui_main import Ui_MainWindow

  ui = Ui_MainWindow()
  window = QtWidgets.QMainWindow()
  ui.setupUi(window)
  assert ui.pushButton_swap.text().startswith("Swap")
