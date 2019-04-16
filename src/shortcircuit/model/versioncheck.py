# versioncheck.py
import json
import requests
import semver
from datetime import datetime, timedelta
from dateutil import parser
from dateutil.tz import tzutc
from PySide2 import QtCore

from .logger import Logger
from .utility.configuration import Configuration
from shortcircuit import __version__ as app_version


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
      response = requests.get(
        url='https://api.github.com/repos/secondfry/shortcircuit/releases/latest',
        timeout=3.1
      )
    except requests.exceptions.RequestException as e:
      Logger.error('Exception raised while trying to get latest version info')
      Logger.error(e)
      self.finished.emit(None)
      return

    if not VersionCheck.should_emit_response(response):
      self.finished.emit(None)
      return

    self.finished.emit(response.text)

  @staticmethod
  def should_emit_response(response):
    if response.status_code != 200:
      Logger.error('Response code is not 200')
      Logger.error(response)
      return False

    try:
      github_data = json.loads(response.text)
    except:
      Logger.error('Response was not json')
      Logger.error(response)
      return False

    if 'tag_name' not in github_data:
      Logger.error('tag_name is missing from response')
      Logger.error(response)
      return False

    github_version = github_data['tag_name'].split('v')[-1]
    try:
      if semver.compare(github_version, app_version) != 1:
        Logger.debug('GitHub version is not newer')
        return False
    except ValueError:
      Logger.error('semver.compare(\'{}\', \'{}\')'.format(github_version, app_version))
      return False
    except Exception as e:
      Logger.error('Something is really wrong', exc_info=e)
      return False

    datetime_now = datetime.now(tzutc())
    datetime_now_string = datetime_now.strftime('%Y-%m-%dT%H:%M:%SZ')

    saved_version = Configuration.settings.value('updates/version')
    Logger.debug('Latest remote version saved is – v{}'.format(saved_version))
    if not saved_version or semver.compare(github_version, saved_version) != 0:
      Configuration.settings.setValue('updates/version', github_version)
      Configuration.settings.setValue('updates/ping_timestamp', datetime_now_string)
      return True

    saved_version_timestamp = Configuration.settings.value('updates/ping_timestamp')
    Logger.debug('Last time user was notified about update was – {}'.format(saved_version_timestamp))
    if not saved_version_timestamp:
      Configuration.settings.setValue('updates/ping_timestamp', datetime_now_string)
      return True

    if datetime_now - parser.parse(timestr=saved_version_timestamp) > timedelta(days=7):
      Configuration.settings.setValue('updates/ping_timestamp', datetime_now_string)
      return True

    return False


def main():
  version_check = VersionCheck()
  version_check.process()


if __name__ == "__main__":
  main()
