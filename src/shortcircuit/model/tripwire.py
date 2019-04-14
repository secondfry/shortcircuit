# tripwire.py

import json
import requests
import urlparse
from logger import Logger
from datetime import datetime
from evedb import EveDb
from solarmap import SolarMap


class Tripwire:
  """
  Tripwire handler
  """
  USER_AGENT = "Short Circuit v0.3.2"

  def __init__(self, username, password, url):
    self.eve_db = EveDb()
    self.username = username
    self.password = password
    self.url = url
    self.session_requests = self.login()

  def login(self):
    response = None

    login_url = urlparse.urljoin(self.url, "login.php")
    session_requests = requests.session()

    payload = {
      "username": self.username,
      "password": self.password,
      "mode": "login",
    }
    headers = {
      "Referer": login_url,
      "User-Agent": Tripwire.USER_AGENT,
    }

    try:
      result = session_requests.post(
        login_url,
        data=payload,
        headers=headers
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
    print 'Getting {}'.format(system_id)

    response = None

    if not self.session_requests:
      return None

    refresh_url = urlparse.urljoin(self.url, "refresh.php")
    payload = {
      "mode": "init",
      "systemID": system_id
    }
    headers = {
      "Referer": refresh_url,
      "User-Agent": Tripwire.USER_AGENT,
    }

    try:
      result = self.session_requests.get(
        refresh_url,
        params=payload,
        headers=headers
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
    self.chain = self.fetch_api_refresh(system_id)
    return self.chain

  def augment_map(self, solar_map):
    connections = -1  # not logged in, yet
    self.get_chain()

    if not self.chain:
      return connections

    # We got some sort of response so at least we're logged in
    connections = 0

    # Process wormholes
    for wormholeId, wormhole in self.chain['wormholes'].iteritems():
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
        signatureIn = self.chain['signatures'][wormhole[parent]]
        signatureOut = self.chain['signatures'][wormhole[sibling]]
        wh_type = wormhole['type']

        systemFrom = convert_to_int(signatureIn['systemID'])
        systemTo = convert_to_int(signatureOut['systemID'])

        if systemFrom == 0 or systemFrom < 10000 or systemTo == 0 or systemTo < 10000:
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
        last_modified = datetime.strptime(signatureIn['modifiedTime'], "%Y-%m-%d %H:%M:%S")
        delta = datetime.utcnow() - last_modified
        time_elapsed = round(delta.total_seconds() / 3600.0, 1)

        # Determine wormhole size
        wh_size = -1
        if wormhole['type']:
          wh_size = self.eve_db.get_whsize_by_code(wormhole['type'])
        if wh_size not in [0, 1, 2, 3]:
          # Wormhole codes are unknown => determine size based on class of wormholes
          wh_size = self.eve_db.get_whsize_by_system(systemFrom, systemTo)

        # Add wormhole conection to solar system
        solar_map.add_connection(
          systemFrom,
          systemTo,
          SolarMap.WORMHOLE,
          [
            signatureIn['signatureID'],
            wh_type,
            signatureOut['signatureID'],
            'K162',
            wh_size,
            wh_life,
            wh_mass,
            time_elapsed
          ],
        )
      except Exception as e:
        pass

    return connections


def is_json(response):
  """
  Check if the response parameter is a valid JSON string
  :param response:
  :return:
  """
  try:
    json.loads(response)
  except ValueError:
    return False
  return True


def convert_to_int(s):
  """
  Convert string to integer
  :param s: Input string
  :return: Interpreted value if successful, 0 otherwise
  """
  try:
    nr = int(s)
  except (ValueError, TypeError):
    nr = 0

  return nr
