# versioncheck.py

import requests
from PySide2 import QtCore

from .logger import Logger


class VersionCheck(QtCore.QObject):
  """
  Version Check on Github releases
  """

  finished = QtCore.Signal(str)

  def __init__(self, parent=None):
    super(VersionCheck, self).__init__(parent)

  def process(self):
    """
    Emits latest version string
    """

    try:
      result = requests.get(
        url='https://api.github.com/repos/secondfry/shortcircuit/releases/latest',
        timeout=3.1
      )
    except requests.exceptions.RequestException as e:
      Logger.error('Exception raised while trying to get latest version info')
      Logger.error(e)
      self.finished.emit(None)
      return

    if result.status_code != 200:
      Logger.error('Result code is not 200')
      Logger.error(result)
      self.finished.emit(None)
      return

    version = result.json()['tag_name']
    self.finished.emit(version)


def main():
  version_check = VersionCheck()
  version_check.process()


if __name__ == "__main__":
  main()
