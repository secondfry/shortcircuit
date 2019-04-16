# tripwire.py

import json
import requests
from datetime import datetime

from .evedb import EveDb
from .logger import Logger
from .solarmap import SolarMap
from .utility.configuration import Configuration
from shortcircuit import USER_AGENT


class Tripwire:
  """
  Tripwire handler
  """

  def __init__(self, username: str, password: str, url: str):
    self.eve_db = EveDb()
    self.username = username
    self.password = password
    self.url = url
    self.session_requests = self.login()
    self.chain = None

  def login(self):
    Logger.debug('Logging in...')

    login_url = '{}/login.php'.format(self.url)
    session_requests = requests.session()

    payload = {
      'username': self.username,
      'password': self.password,
      'mode': 'login',
    }
    headers = {
      'Referer': login_url,
      'User-Agent': USER_AGENT,
    }
    proxies = {}
    proxy = Configuration.settings.value('proxy')
    if proxy:
      proxies = {
        'http': proxy,
        'https': proxy
      }

    try:
      result = session_requests.post(
        login_url,
        data=payload,
        headers=headers,
        proxies=proxies
      )
    except requests.exceptions.RequestException as e:
      Logger.error('Exception raised while trying to login')
      Logger.error(e)
      return None

    if result.status_code != 200:
      Logger.error('Result code is not 200')
      Logger.error(result)
      return None

    response = session_requests
    return response

  def fetch_api_refresh(self, system_id="30000142"):
    Logger.debug('Getting {}...'.format(system_id))

    if not self.session_requests:
      return None

    refresh_url = '{}/refresh.php'.format(self.url)
    payload = {
      'mode': 'init',
      'systemID': system_id
    }
    headers = {
      'Referer': refresh_url,
      'User-Agent': USER_AGENT,
    }
    proxies = {}
    proxy = Configuration.settings.value('proxy')
    if proxy:
      proxies = {
        'http': proxy,
        'https': proxy
      }

    try:
      result = self.session_requests.get(
        refresh_url,
        params=payload,
        headers=headers,
        proxies=proxies
      )
    except requests.exceptions.RequestException as e:
      Logger.error('Exception raised while trying to refresh')
      Logger.error(e)
      return None

    if result.status_code != 200:
      Logger.error('Result code is not 200')
      Logger.error(result)
      return None

    if not is_json(result.text):
      Logger.error('Result is not JSON')
      Logger.error(result)
      return None

    response = result.json()
    return response

  def get_chain(self, system_id="30000142"):
    """
    :param system_id: str Numerical solar system ID
    :return: Raw Tripwire chain (JSON object)
    """
    self.chain = self.fetch_api_refresh(system_id)
    return self.chain

  def augment_map(self, solar_map: SolarMap):
    """
    :param solar_map: SolarMap
    :return: Number of connections in case of success, -1 in case of failure
    """
    self.get_chain()

    if not self.chain:
      return -1

    # We got some sort of response so at least we're logged in
    connections = 0

    # Process wormholes
    for wormholeId, wormhole in self.chain['wormholes'].items():
      try:
        if wormhole['type'] == 'GATE':
          continue

        if wormhole['initialID'] not in self.chain['signatures']:
          continue

        if wormhole['secondaryID'] not in self.chain['signatures']:
          continue

        if not wormhole['parent']:
          parent = 'initialID'
        else:
          parent = wormhole['parent'] + 'ID'
        sibling = {
          'initialID': 'secondaryID',
          'secondaryID': 'initialID',
        }.get(parent)
        signature_in = self.chain['signatures'][wormhole[parent]]
        signature_out = self.chain['signatures'][wormhole[sibling]]
        wh_type = wormhole['type']

        system_from = convert_to_int(signature_in['systemID'])
        system_to = convert_to_int(signature_out['systemID'])

        if system_from == 0 or system_from < 10000 or system_to == 0 or system_to < 10000:
          continue

        connections += 1

        wh_life = {
          'stable': 1,
          'critical': 0,
        }.get(wormhole['life'], 0)

        wh_mass = {
          'stable': 2,
          'destab': 1,
          'critical': 0,
        }.get(wormhole['mass'], 0)

        # Compute time elapsed from this moment to when the signature was updated
        last_modified = datetime.strptime(signature_in['modifiedTime'], "%Y-%m-%d %H:%M:%S")
        delta = datetime.utcnow() - last_modified
        time_elapsed = round(delta.total_seconds() / 3600.0, 1)

        # Determine wormhole size
        wh_size = -1
        if wormhole['type']:
          wh_size = self.eve_db.get_whsize_by_code(wormhole['type'])
        if wh_size not in [0, 1, 2, 3]:
          # Wormhole codes are unknown => determine size based on class of wormholes
          wh_size = self.eve_db.get_whsize_by_system(system_from, system_to)

        # Add wormhole connection to solar system
        solar_map.add_connection(
          system_from,
          system_to,
          SolarMap.WORMHOLE,
          [
            signature_in['signatureID'],
            wh_type,
            signature_out['signatureID'],
            'K162',
            wh_size,
            wh_life,
            wh_mass,
            time_elapsed
          ],
        )
      except Exception as e:
        Logger.error('pepega', exc_info=e)
        pass

    return connections


def is_json(data: str):
  """
  :param data: str
  :return: True if the response parameter is a valid JSON string, False if else
  """
  try:
    json.loads(data)
  except ValueError:
    return False
  return True


def convert_to_int(s: str):
  """
  Convert string to integer

  :param s: str Input string
  :return: Interpreted value if successful, 0 otherwise
  """
  try:
    nr = int(s)
  except (ValueError, TypeError):
    nr = 0

  return nr
