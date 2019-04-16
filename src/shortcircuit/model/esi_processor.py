# esi_processor.py

import threading
from PySide2 import QtCore

from .esi.esi import ESI


class ESIProcessor(QtCore.QObject):
  """
  ESI Middleware
  """
  login_response = QtCore.Signal(str)
  logout_response = QtCore.Signal()
  location_response = QtCore.Signal(str)
  destination_response = QtCore.Signal(bool)

  def __init__(self, parent=None):
    super(ESIProcessor, self).__init__(parent)
    self.esi = ESI(self._login_callback, self._logout_callback)

  def login(self):
    return self.esi.start_server()

  def logout(self):
    self.esi.logout()

  def get_location(self):
    server_thread = threading.Thread(target=self._get_location)
    server_thread.setDaemon(True)
    server_thread.start()

  def _get_location(self):
    location = self.esi.get_char_location()
    self.location_response.emit(location)

  # TODO properly type this
  def set_destination(self, sys_id):
    server_thread = threading.Thread(target=self._set_destination, args=(sys_id, ))
    server_thread.setDaemon(True)
    server_thread.start()

  # TODO properly type this
  def _set_destination(self, sys_id):
    response = self.esi.set_char_destination(sys_id)
    self.destination_response.emit(response)

  # TODO properly type this
  def _login_callback(self, char_name):
    self.login_response.emit(char_name)

  def _logout_callback(self):
    self.logout_response.emit()
