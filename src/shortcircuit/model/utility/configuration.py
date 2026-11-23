from PySide6 import QtCore

from shortcircuit import __appname__
from shortcircuit.model.utility.singleton import Singleton


class Configuration(metaclass=Singleton):
  settings = QtCore.QSettings(
    QtCore.QSettings.IniFormat,
    QtCore.QSettings.UserScope,
    __appname__,
  )
