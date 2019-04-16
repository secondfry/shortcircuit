# evescout.py

import requests
from datetime import datetime

from .evedb import EveDb
from .solarmap import SolarMap
from .logger import Logger
from shortcircuit import USER_AGENT


class EveScout:
  """
  Eve Scout Thera Connections
  """
  TIMEOUT = 2

  def __init__(self, url: str = 'https://www.eve-scout.com/api/wormholes'):
    self.eve_db = EveDb()
    self.evescout_url = url

  def augment_map(self, solar_map: SolarMap):
    """
    :param solar_map: SolarMap
    :return: Number of connections in case of success, -1 in case of failure
    """
    headers = {
      'User-Agent': USER_AGENT
    }
    try:
      result = requests.get(
        url=self.evescout_url,
        headers=headers,
        timeout=EveScout.TIMEOUT
      )
    except requests.exceptions.RequestException as e:
      Logger.error('Exception raised while trying to get eve-scout chain info')
      Logger.error(e)
      return -1

    if result.status_code != 200:
      Logger.error('Result code is not 200')
      Logger.error(result)
      return -1

    # we get some sort of response so at least something is working
    connections = 0
    json_response = result.json()
    for row in json_response:
      connections += 1
      # Retrieve signature meta data
      source = row['sourceSolarSystem']['id']
      dest = row['destinationSolarSystem']['id']
      sig_source = row['signatureId']
      code_source = row['sourceWormholeType']['name']
      sig_dest = row['wormholeDestinationSignatureId']
      code_dest = row['destinationWormholeType']['name']
      if row['wormholeEol'] == 'stable':
        wh_life = 1
      else:
        wh_life = 0
      if row['wormholeEol'] == 'stable':
        wh_mass = 2
      elif row['wormholeEol'] == 'destab':
        wh_mass = 1
      else:
        wh_mass = 0

      # Compute time elapsed from this moment to when the signature was updated
      last_modified = datetime.strptime(row['updatedAt'][:-5], "%Y-%m-%dT%H:%M:%S")
      delta = datetime.utcnow() - last_modified
      time_elapsed = round(delta.total_seconds() / 3600.0, 1)

      if source != 0 and dest != 0:
        # Determine wormhole size
        size_result1 = self.eve_db.get_whsize_by_code(code_source)
        size_result2 = self.eve_db.get_whsize_by_code(code_dest)
        if size_result1 in [0, 1, 2, 3]:
          wh_size = size_result1
        elif size_result2 in [0, 1, 2, 3]:
          wh_size = size_result2
        else:
          # Wormhole codes are unknown => determine size based on class of wormholes
          wh_size = self.eve_db.get_whsize_by_system(source, dest)

        solar_map.add_connection(
          source,
          dest,
          SolarMap.WORMHOLE,
          [sig_source, code_source, sig_dest, code_dest, wh_size, wh_life, wh_mass, time_elapsed],
        )

    return connections
