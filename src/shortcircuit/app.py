# app.py
import json
import sys
import time
from functools import partial

from PySide2 import QtCore, QtGui, QtWidgets

from . import __appname__, __version__, __date__ as last_update
from .model.esi_processor import ESIProcessor
from .model.evedb import EveDb
from .model.logger import Logger
from .model.navigation import Navigation
from .model.navprocessor import NavProcessor
from .model.versioncheck import VersionCheck
from .view.gui_about import Ui_AboutDialog
from .view.gui_main import Ui_MainWindow
from .view.gui_tripwire import Ui_TripwireDialog


class TripwireDialog(QtWidgets.QDialog, Ui_TripwireDialog):
  """
  Tripwire Configuration Window
  """
  def __init__(self, trip_url, trip_user, trip_pass, proxy, evescout_enabled, parent=None):
    super().__init__(parent)
    self.setupUi(self)
    self.lineEdit_url.setText(trip_url)
    self.lineEdit_user.setText(trip_user)
    self.lineEdit_pass.setText(trip_pass)
    self.lineEdit_proxy.setText(proxy)
    self.checkBox_evescout.setChecked(evescout_enabled)
    self.label_evescout_logo.mouseReleaseEvent = TripwireDialog.logo_click

  @staticmethod
  def logo_click(event):
    event.accept()
    QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://www.eve-scout.com/"))


class AboutDialog(QtWidgets.QDialog, Ui_AboutDialog):
  """
  Tripwire Configuration Window
  """
  def __init__(self, parent=None):
    super().__init__(parent)
    self.setupUi(self)
    self.label_title.setText('{} v{} ({})'.format(__appname__, __version__, last_update))
    # noinspection PyUnresolvedReferences
    self.pushButton_o7.clicked.connect(self.close)
    self.label_icon.mouseReleaseEvent = AboutDialog.icon_click

  @staticmethod
  def icon_click(event):
    event.accept()
    QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://github.com/secondfry/shortcircuit"))


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
  """
  Main Window GUI
  """

  MSG_OK = 2
  MSG_ERROR = 1
  MSG_INFO = 0

  @property
  def route_source(self):
    text_input = self.lineEdit_source.text().strip()
    eve_db = EveDb()
    ret = eve_db.normalize_name(text_input)

    if not ret:
      ret = 'Jita'

    return ret

  def __init__(self, parent=None):
    super().__init__(parent)
    self.setupUi(self)
    self.settings = QtCore.QSettings(
      QtCore.QSettings.IniFormat,
      QtCore.QSettings.UserScope,
      __appname__
    )

    self.tripwire_url = None
    self.tripwire_user = None
    self.tripwire_pass = None
    self.global_proxy = None
    self.evescout_enabled = None

    # Table configuration
    self.tableWidget_path.setColumnCount(5)
    self.tableWidget_path.setHorizontalHeaderLabels(
      ["System", "Cls", "Sec", "Instructions", "Additional information"]
    )
    header: QtWidgets.QHeaderView = self.tableWidget_path.horizontalHeader()
    header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
    self.tableWidget_path.horizontalHeader().setStretchLastSection(True)

    # Read stored settings
    self.read_settings()

    # Read resources
    self.nav = Navigation(self)

    # Additional GUI setup
    self.additional_gui_setup()
    self.label_status_bar = QtWidgets.QLabel("Not connected to EvE")
    self.statusBar().addWidget(self.label_status_bar, 1)
    if self.evescout_enabled:
      self.label_evescout_status.setText("Eve-Scout: enabled")
    else:
      self.label_evescout_status.setText("Eve-Scout: disabled")

    # Icons
    self.icon_wormhole = QtGui.QIcon(":images/wh_icon.png")

    # Thread initial config
    Logger.register_thread(QtCore.QThread.currentThread(), 'main')

    # NavProcessor thread
    self.worker_thread = QtCore.QThread()
    Logger.register_thread(self.worker_thread, 'worker_thread / NavProcessor')
    self.nav_processor = NavProcessor(self.nav)
    self.nav_processor.moveToThread(self.worker_thread)
    self.nav_processor.finished.connect(self.worker_thread_done)
    # noinspection PyUnresolvedReferences
    self.worker_thread.started.connect(self.nav_processor.process)

    # Version check thread
    self.version_thread = QtCore.QThread()
    Logger.register_thread(self.version_thread, 'version_thread / VersionCheck')
    self.version_check = VersionCheck()
    self.version_check.moveToThread(self.version_thread)
    self.version_check.finished.connect(self.version_check_done)
    # noinspection PyUnresolvedReferences
    self.version_thread.started.connect(self.version_check.process)

    # ESI
    self.eve_connected = False
    self.esip = ESIProcessor()
    self.esip.login_response.connect(self.login_handler)
    self.esip.logout_response.connect(self.logout_handler)
    self.esip.location_response.connect(self.location_handler)
    self.esip.destination_response.connect(self.destination_handler)

    # Start version check
    self.version_thread.start()

  # noinspection PyUnresolvedReferences
  def additional_gui_setup(self):
    # Additional GUI setup
    self.setWindowTitle('{} v{} ({})'.format(__appname__, __version__, last_update))
    self.banner_image.mouseReleaseEvent = MainWindow.banner_click
    self.banner_button.mouseReleaseEvent = MainWindow.banner_click
    self._path_message("", MainWindow.MSG_OK)
    self._avoid_message("", MainWindow.MSG_OK)
    self.lineEdit_source.setFocus()
    self.lineEdit_short_format.mousePressEvent = partial(MainWindow.short_format_click, self)

    # Auto-completion
    system_list = self.nav.eve_db.system_name_list()
    for line_edit_field in [
      self.lineEdit_source,
      self.lineEdit_destination,
      self.lineEdit_avoid_name,
      self.lineEdit_set_dest,
    ]:
      completer = QtWidgets.QCompleter(system_list, self)
      completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
      line_edit_field.setCompleter(completer)

    # Signals
    self.pushButton_eve_login.clicked.connect(self.btn_eve_login_clicked)
    self.pushButton_player_location.clicked.connect(self.btn_player_location_clicked)
    self.pushButton_find_path.clicked.connect(self.btn_find_path_clicked)
    self.pushButton_trip_config.clicked.connect(self.btn_trip_config_clicked)
    self.pushButton_trip_get.clicked.connect(self.btn_trip_get_clicked)
    self.pushButton_avoid_add.clicked.connect(self.btn_avoid_add_clicked)
    self.pushButton_avoid_delete.clicked.connect(self.btn_avoid_delete_clicked)
    self.pushButton_avoid_clear.clicked.connect(self.btn_avoid_clear_clicked)
    self.pushButton_set_dest.clicked.connect(self.btn_set_dest_clicked)
    self.pushButton_reset.clicked.connect(self.btn_reset_clicked)
    self.lineEdit_source.returnPressed.connect(self.line_edit_source_return)
    self.lineEdit_destination.returnPressed.connect(self.line_edit_destination_return)
    self.lineEdit_avoid_name.returnPressed.connect(self.line_edit_avoid_name_return)
    self.lineEdit_set_dest.returnPressed.connect(self.btn_set_dest_clicked)
    self.tableWidget_path.itemSelectionChanged.connect(self.table_item_selection_changed)

  def migrate_settings_tripwire(self):
    Logger.info('Mirgating Tripwire dialog settings to their own category')
    tripwire_url = self.settings.value('MainWindow/tripwire_url')
    tripwire_user = self.settings.value('MainWindow/tripwire_user')
    tripwire_pass = self.settings.value('MainWindow/tripwire_pass')
    evescout_enabled = self.settings.value('MainWindow/evescout_enable', 'false') == 'true'
    self.settings.beginGroup('Tripwire')
    self.settings.setValue('url', tripwire_url)
    self.settings.setValue('user', tripwire_user)
    self.settings.setValue('pass', tripwire_pass)
    self.settings.setValue('evescout_enabled', evescout_enabled)
    self.settings.endGroup()
    self.settings.remove('MainWindow/tripwire_url')
    self.settings.remove('MainWindow/tripwire_user')
    self.settings.remove('MainWindow/tripwire_pass')
    self.settings.remove('MainWindow/evescout_enable')

  def read_settings_tripwire(self):
    self.global_proxy = self.settings.value('proxy')
    self.settings.beginGroup('Tripwire')
    self.tripwire_url = self.settings.value('url', 'https://tripwire.eve-apps.com')
    self.tripwire_user = self.settings.value('user')
    self.tripwire_pass = self.settings.value('pass')
    self.evescout_enabled = self.settings.value('evescout_enabled', 'false') == 'true'
    self.settings.endGroup()

  def read_settings(self):
    if self.settings.value('MainWindow/tripwire_url'):
      self.migrate_settings_tripwire()
    self.read_settings_tripwire()

    self.settings.beginGroup("MainWindow")

    # Window state
    win_geometry = self.settings.value("win_geometry")
    if win_geometry:
      self.restoreGeometry(win_geometry)
    win_state = self.settings.value("win_state")
    if win_state:
      self.restoreState(win_state)
    for col_idx, column_width in enumerate(self.settings.value("table_widths", "110,75,75,180").split(',')):
      self.tableWidget_path.setColumnWidth(col_idx, int(column_width))

    # Avoidance list
    self.checkBox_avoid_enabled.setChecked(self.settings.value("avoidance_enabled", "false") == "true")
    for sys_name in self.settings.value("avoidance_list", "").split(','):
      if sys_name != "":
        self._avoid_system_name(sys_name)

    # Restrictions
    self.comboBox_size.setCurrentIndex(
      int(self.settings.value("restrictions_whsize", "0"))
    )
    self.checkBox_eol.setChecked(self.settings.value("restriction_eol", "false") == "true")
    self.checkBox_masscrit.setChecked(self.settings.value("restriction_masscrit", "false") == "true")
    self.checkBox_ignore_old.setChecked(self.settings.value("restriction_ignore_old", "false") == "true")
    self.doubleSpinBox_hours.setValue(
      float(self.settings.value("restriction_hours", "16.0"))
    )

    # Security prioritization
    self.checkBox_security_enabled.setChecked(self.settings.value("security_enabled", "false") == "true")
    self.spinBox_prio_hs.setValue(int(self.settings.value("prio_hs", "1")))
    self.spinBox_prio_ls.setValue(int(self.settings.value("prio_ls", "1")))
    self.spinBox_prio_ns.setValue(int(self.settings.value("prio_ns", "1")))
    self.spinBox_prio_wh.setValue(int(self.settings.value("prio_wh", "1")))

    self.settings.endGroup()

  def write_settings_tripwire(self):
    self.settings.setValue('proxy', self.global_proxy)
    self.settings.beginGroup('Tripwire')
    self.settings.setValue('url', self.tripwire_url)
    self.settings.setValue('user', self.tripwire_user)
    self.settings.setValue('pass', self.tripwire_pass)
    self.settings.setValue('evescout_enabled', self.evescout_enabled)
    self.settings.endGroup()

  def write_settings(self):
    self.write_settings_tripwire()

    self.settings.beginGroup("MainWindow")

    # Window state
    self.settings.setValue("win_geometry", self.saveGeometry())
    self.settings.setValue("win_state", self.saveState())
    self.settings.setValue("table_widths", ",".join([
      str(self.tableWidget_path.columnWidth(0)),
      str(self.tableWidget_path.columnWidth(1)),
      str(self.tableWidget_path.columnWidth(2)),
      str(self.tableWidget_path.columnWidth(3)),
    ]))

    # Avoidance list
    self.settings.setValue(
      "avoidance_enabled",
      self.checkBox_avoid_enabled.isChecked()
    )
    avoidance_list_string = ",".join(self.avoidance_list())
    self.settings.setValue(
      "avoidance_list",
      avoidance_list_string
    )

    # Restrictions
    self.settings.setValue(
      "restrictions_whsize",
      self.comboBox_size.currentIndex()
    )
    self.settings.setValue(
      "restriction_eol",
      self.checkBox_eol.isChecked()
    )
    self.settings.setValue(
      "restriction_masscrit",
      self.checkBox_masscrit.isChecked()
    )
    self.settings.setValue(
      "restriction_ignore_old",
      self.checkBox_ignore_old.isChecked()
    )
    self.settings.setValue(
      "restriction_hours",
      self.doubleSpinBox_hours.value()
    )

    # Security prioritization
    self.settings.setValue(
      "security_enabled",
      self.checkBox_security_enabled.isChecked()
    )
    self.settings.setValue("prio_hs", self.spinBox_prio_hs.value())
    self.settings.setValue("prio_ls", self.spinBox_prio_ls.value())
    self.settings.setValue("prio_ns", self.spinBox_prio_ns.value())
    self.settings.setValue("prio_wh", self.spinBox_prio_wh.value())

    self.settings.endGroup()

  def _message_box(self, title, text):
    msg_box = QtWidgets.QMessageBox(self)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)
    return msg_box.exec_()

  @staticmethod
  def _label_message(label, message, message_type):
    if message_type == MainWindow.MSG_OK:
      label.setStyleSheet("QLabel {color: green;}")
    elif message_type == MainWindow.MSG_ERROR:
      label.setStyleSheet("QLabel {color: red;}")
    else:
      label.setStyleSheet("QLabel {color: black;}")
    label.setText(message)

  def _avoid_message(self, message, message_type):
    MainWindow._label_message(self.label_avoid_status, message, message_type)

  def _path_message(self, message, message_type):
    MainWindow._label_message(self.label_status, message, message_type)

  def _trip_message(self, message, message_type):
    MainWindow._label_message(self.label_trip_status, message, message_type)

  def _statusbar_message(self, message, message_type):
    MainWindow._label_message(self.label_status_bar, message, message_type)

  def avoidance_enabled(self):
    return self.checkBox_avoid_enabled.isChecked()

  def avoidance_list(self):
    items = []
    for index in range(self.listWidget_avoid.count()):
      items.append(self.listWidget_avoid.item(index))
    return [i.text() for i in items]

  def _avoid_system_name(self, sys_name):
    if sys_name:
      if sys_name not in self.avoidance_list():
        QtWidgets.QListWidgetItem(sys_name, self.listWidget_avoid)
        self._avoid_message("Added", MainWindow.MSG_OK)
      else:
        self._avoid_message("Already in list!", MainWindow.MSG_ERROR)
    else:
      self._avoid_message("Invalid system name :(", MainWindow.MSG_ERROR)

  def avoid_system(self):
    sys_name = self.nav.eve_db.normalize_name(
      self.lineEdit_avoid_name.text()
    )
    self._avoid_system_name(sys_name)

  @staticmethod
  def get_system_class_color(sclass):
    return {
      'HS': QtGui.QColor(223, 240, 216),
      'LS': QtGui.QColor(252, 248, 227),
      'NS': QtGui.QColor(242, 222, 222),
      'WH': QtGui.QColor(210, 226, 242),
      '▲': QtGui.QColor(242, 212, 212),
    }.get(sclass, QtGui.QColor(220, 220, 220))

  def add_data_to_table(self, route):
    self.tableWidget_path.setRowCount(len(route))

    for route_step_id, route_step in enumerate(route):
      color = self.get_system_class_color(route_step['class'])
      ui_col_id = 0
      for col_id in [
        'name',
        'class',
        'security',
        'path_action',
        'path_info'
      ]:
        text = str(route_step[col_id])
        item = QtWidgets.QTableWidgetItem(text)

        if col_id in ['class', 'security']:
          item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

        if col_id == 'path_action' and 'wormhole' in text:
          item.setIcon(self.icon_wormhole)

        item.setBackground(color)
        self.tableWidget_path.setItem(route_step_id, ui_col_id, item)
        ui_col_id += 1

    self.tableWidget_path.resizeRowsToContents()

  def get_restrictions_size(self):
    size_restriction = []

    combo_index = self.comboBox_size.currentIndex()
    if combo_index < 1:
      size_restriction.append(EveDb.WHSIZE_S)
    if combo_index < 2:
      size_restriction.append(EveDb.WHSIZE_M)
    if combo_index < 3:
      size_restriction.append(EveDb.WHSIZE_L)
    if combo_index < 4:
      size_restriction.append(EveDb.WHSIZE_XL)

    return size_restriction

  def get_restrictions_age(self):
    age_threshold = 0

    if self.checkBox_ignore_old.isChecked():
      age_threshold = self.doubleSpinBox_hours.value()

    return age_threshold

  def get_restrictions_security(self):
    security_prio = []

    if self.checkBox_security_enabled.isChecked():
      security_prio = [
        self.spinBox_prio_hs.value(),
        self.spinBox_prio_ls.value(),
        self.spinBox_prio_ns.value(),
        self.spinBox_prio_wh.value(),
      ]

    return security_prio

  def get_restrictions_avoidance(self):
    avoidance_list = []

    if self.avoidance_enabled():
      avoidance_list = self.avoidance_list()

    return avoidance_list

  def get_restrictions(self):
    size_restriction = self.get_restrictions_size()
    ignore_eol = self.checkBox_eol.isChecked()
    ignore_masscrit = self.checkBox_masscrit.isChecked()
    age_threshold = self.get_restrictions_age()
    security_prio = self.get_restrictions_security()
    avoidance_list = self.get_restrictions_avoidance()

    return [size_restriction, ignore_eol, ignore_masscrit, age_threshold, security_prio, avoidance_list]

  def _clear_results(self):
    self.tableWidget_path.setRowCount(0)
    self.lineEdit_short_format.setText("")

  def find_path(self):
    source_sys_name = self.nav.eve_db.normalize_name(
      self.lineEdit_source.text().strip()
    )
    dest_sys_name = self.nav.eve_db.normalize_name(
      self.lineEdit_destination.text().strip()
    )

    if not source_sys_name or not dest_sys_name:
      self._clear_results()
      error_msg = []
      if not source_sys_name:
        error_msg.append("source")
      if not dest_sys_name:
        error_msg.append("destination")
      error_msg = "Invalid system name in {}.".format(" and ".join(error_msg))
      self._path_message(error_msg, MainWindow.MSG_ERROR)
      return

    # TODO Why destination can't be in avoidance list?
    # Should refactored
    if self.avoidance_enabled() and dest_sys_name in self.avoidance_list():
      self._path_message("Destination in avoidance list, dummy ;)", MainWindow.MSG_ERROR)
      self._clear_results()
      return

    [route, short_format] = self.nav.route(
      source_sys_name,
      dest_sys_name
    )

    if not route:
      self._clear_results()
      self._path_message("No path found between the solar systems.", MainWindow.MSG_ERROR)
      return

    route_length = len(route)
    if route_length == 1:
      self._path_message("Set the same source and destination :P", MainWindow.MSG_OK)
    else:
      self._path_message("Total number of jumps: {}".format(route_length - 1), MainWindow.MSG_OK)

    self.add_data_to_table(route)
    self.lineEdit_short_format.setText(short_format)

  @staticmethod
  def banner_click(event):
    event.accept()
    AboutDialog().exec_()

  def short_format_click(self, event):
    event.accept()
    if not self.lineEdit_short_format.text():
      return
    self.lineEdit_short_format.selectAll()
    self.lineEdit_short_format.copy()
    self._statusbar_message("Copied travel info to clipboard!", MainWindow.MSG_INFO)

  @QtCore.Slot(str)
  def login_handler(self, char_name):
    if char_name:
      self._statusbar_message("Welcome, {}".format(char_name), MainWindow.MSG_OK)
      self.pushButton_eve_login.setText("Logout")
      self.pushButton_player_location.setEnabled(True)
      self.pushButton_set_dest.setEnabled(True)
      self.eve_connected = True
    else:
      self._statusbar_message("Error: Unable to connect with ESI", MainWindow.MSG_ERROR)

  @QtCore.Slot()
  def logout_handler(self):
    self._statusbar_message("Not connected to EvE", MainWindow.MSG_INFO)
    self.pushButton_eve_login.setText("Log in with EvE")
    self.pushButton_player_location.setEnabled(False)
    self.pushButton_set_dest.setEnabled(False)
    self.eve_connected = False

  @QtCore.Slot(str)
  def location_handler(self, location):
    if location:
      self.lineEdit_source.setText(location)
    else:
      self._message_box("Player destination", "Unable to get location (character not online or ESI error)")
    self.pushButton_player_location.setEnabled(True)

  @QtCore.Slot(bool)
  def destination_handler(self, response):
    if not response:
      self._message_box("Player destination", "ESI error when trying to set destination")
    self.pushButton_set_dest.setEnabled(True)

  @QtCore.Slot(int)
  def worker_thread_done(self, connections, evescout_connections):
    self.worker_thread.quit()

    # wait for thread to finish
    while self.worker_thread.isRunning():
      time.sleep(0.01)

    if self.evescout_enabled:
      if evescout_connections >= 0:
        self.label_evescout_status.setText("Eve-Scout: {} connections".format(evescout_connections))
      else:
        self.label_evescout_status.setText("Eve-Scout: error :(")
    else:
      self.label_evescout_status.setText("Eve-Scout: disabled")
    if connections > 0:
      self._trip_message(
        "Retrieved {} Tripwire connections!".format(connections),
        MainWindow.MSG_OK
      )
    elif connections == 0:
      self._trip_message(
        "No Tripwire connections exist!",
        MainWindow.MSG_ERROR
      )
    else:
      self._trip_message(
        "Tripwire error. Check url/user/pass.",
        MainWindow.MSG_ERROR
      )

    self.pushButton_trip_get.setEnabled(True)
    self.pushButton_find_path.setEnabled(True)

  @QtCore.Slot()
  def btn_eve_login_clicked(self):
    if not self.eve_connected:
      self.esip.login()
    else:
      self.esip.logout()

  @QtCore.Slot()
  def btn_player_location_clicked(self):
    self.pushButton_player_location.setEnabled(False)
    self.esip.get_location()

  @QtCore.Slot()
  def btn_set_dest_clicked(self):
    if self.pushButton_set_dest.isEnabled():
      dest_sys_name = self.nav.eve_db.normalize_name(
        self.lineEdit_set_dest.text().strip()
      )
      sys_id = self.nav.eve_db.name2id(dest_sys_name)
      if sys_id:
        self.pushButton_set_dest.setEnabled(False)
        self.esip.set_destination(sys_id)
      else:
        if self.lineEdit_set_dest.text().strip() == "":
          msg_txt = "No system name give as input"
        else:
          msg_txt = "Invalid system name: '{}'".format(self.lineEdit_set_dest.text())
        self._message_box("Player destination", msg_txt)

  @QtCore.Slot()
  def btn_find_path_clicked(self):
    self.find_path()

  @QtCore.Slot()
  def btn_trip_config_clicked(self):
    tripwire_dialog = TripwireDialog(
      self.tripwire_url,
      self.tripwire_user,
      self.tripwire_pass,
      self.global_proxy,
      self.evescout_enabled
    )

    if not tripwire_dialog.exec_():
      return

    self.tripwire_url = tripwire_dialog.lineEdit_url.text()
    self.tripwire_user = tripwire_dialog.lineEdit_user.text()
    self.tripwire_pass = tripwire_dialog.lineEdit_pass.text()
    self.global_proxy = tripwire_dialog.lineEdit_proxy.text()
    self.nav.tripwire_set_login()
    self.evescout_enabled = tripwire_dialog.checkBox_evescout.isChecked()
    if self.evescout_enabled:
      self.label_evescout_status.setText("Eve-Scout: enabled")
    else:
      self.label_evescout_status.setText("Eve-Scout: disabled")
    self.write_settings_tripwire()

  @QtCore.Slot()
  def btn_trip_get_clicked(self):
    if not self.worker_thread.isRunning():
      self.pushButton_trip_get.setEnabled(False)
      self.pushButton_find_path.setEnabled(False)
      self.nav_processor.evescout_enable = self.evescout_enabled
      self.worker_thread.start()
    else:
      self._trip_message("Error! Process already running", MainWindow.MSG_ERROR)

  @QtCore.Slot()
  def btn_avoid_add_clicked(self):
    self.avoid_system()

  @QtCore.Slot()
  def btn_avoid_delete_clicked(self):
    for item in self.listWidget_avoid.selectedItems():
      self.listWidget_avoid.takeItem(self.listWidget_avoid.row(item))

  @QtCore.Slot()
  def btn_avoid_clear_clicked(self):
    self.listWidget_avoid.clear()

  @QtCore.Slot()
  def btn_reset_clicked(self):
    msg_box = QtWidgets.QMessageBox(self)
    msg_box.setWindowTitle("Reset chain")
    msg_box.setText("Are you sure you want to clear all Tripwire data?")
    msg_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    msg_box.setDefaultButton(QtWidgets.QMessageBox.No)
    ret = msg_box.exec_()

    if ret == QtWidgets.QMessageBox.Yes:
      self.nav.reset_chain()
      self._trip_message("Not connected to Tripwire, yet", MainWindow.MSG_INFO)

  @QtCore.Slot()
  def line_edit_avoid_name_return(self):
    self.avoid_system()

  @QtCore.Slot()
  def line_edit_source_return(self):
    self.lineEdit_destination.setFocus()

  @QtCore.Slot()
  def line_edit_destination_return(self):
    self.find_path()

  def _table_style(self, red_value, green_value, blue_value):
    self.tableWidget_path.setStyleSheet(
      "selection-color: black; selection-background-color: rgb({}, {}, {});".format(
        red_value,
        green_value,
        blue_value,
      )
    )

  @QtCore.Slot()
  def table_item_selection_changed(self):
    selection = self.tableWidget_path.selectedItems()
    if selection:
      sys_class = selection[1].text()
      if sys_class == "HS":
        self._table_style(193, 210, 186)
      elif sys_class == "LS":
        self._table_style(222, 218, 197)
      elif sys_class == "NS":
        self._table_style(212, 192, 192)
      else:
        self._table_style(180, 196, 212)

      self.lineEdit_set_dest.setText(selection[0].text())

  @QtCore.Slot(str)
  def version_check_done(self, latest):
    self.version_thread.quit()

    if not latest:
      return

    latest = json.loads(latest)
    version = latest['tag_name'].split('v')[-1]
    changelog = latest['body']
    if len(latest['body']) > 1200:
      changelog = latest['body'][0:1200].split(' ')
      del changelog[-1]
      changelog = ' '.join(changelog)

    version_box = QtWidgets.QMessageBox(self)
    version_box.setWindowTitle('New version available!')
    version_box.setText(
      'Your version: v{} ({}).\nGitHub latest release: v{} ({}).\n\n{}'.format(
        __version__,
        last_update,
        version,
        latest['published_at'],
        changelog
      )
    )
    version_box.addButton('Download now', QtWidgets.QMessageBox.AcceptRole)
    version_box.addButton('Remind me later', QtWidgets.QMessageBox.RejectRole)
    ret = version_box.exec_()

    if ret != QtWidgets.QMessageBox.AcceptRole:
      return

    QtGui.QDesktopServices.openUrl(
      QtCore.QUrl('https://github.com/secondfry/shortcircuit/releases/tag/{}'.format(latest['tag_name']))
    )

  # event: QCloseEvent
  def closeEvent(self, event):
    self.write_settings()
    event.accept()


def run():
  appl = QtWidgets.QApplication(sys.argv)
  form = MainWindow()
  form.show()
  appl.exec_()
