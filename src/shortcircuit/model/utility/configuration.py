import json
import semver
from datetime import datetime
from dateutil.tz import tzutc
from PySide2 import QtCore

from shortcircuit import __appname__, __version__
from shortcircuit.model.logger import Logger
from shortcircuit.model.utility.singleton import Singleton


class Configuration(metaclass=Singleton):
  settings = QtCore.QSettings(
    QtCore.QSettings.IniFormat,
    QtCore.QSettings.UserScope,
    __appname__
  )

  def __init__(self):
    self.state = {
      'version': __version__
    }
    self.state_filename = 'config.json'
    self.state_load()

  def state_load(self):
    try:
      file = open(self.state_filename, 'r')
    except IOError as e:
      if e.errno == 2:
        Logger.info('Configuration file is not found. Probably running this for the first time')
        return
      Logger.error(e)
      return

    state = json.load(file)
    if 'version' not in state:
      Logger.warning('World state file malformed. \'version\' field is not present')
      return
    if semver.compare(state['version'], __version__) != 0:
      with open('{}.{}.{}.bak'.format(
          self.state_filename,
          state['version'],
          datetime.now(tzutc()).strftime('%Y-%m-%d %H:%M:%S')
      ), 'w') as backup:
        json.dump(state, backup, indent=2)
      Logger.warning('Backing up and discarding old configuration')
      Logger.warning('TODO implement configuration update strategy')
      return
    self.state = state

  def state_save(self):
    with open(self.state_filename, 'w') as f:
      json.dump(self.state, f, indent=2)

  @staticmethod
  def set(key, val):
    Configuration().state[key] = val
    Configuration().state_save()

  @staticmethod
  def get(key):
    return Configuration().state.get(key, None)
