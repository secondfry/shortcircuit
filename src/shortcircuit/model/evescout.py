# evescout.py

from datetime import datetime

import requests
from shortcircuit import USER_AGENT

from .evedb import EveDb, WormholeSize, WormholeMassspan, WormholeTimespan
from .logger import Logger
from .solarmap import ConnectionType, SolarMap


class EveScout:
  """
  Eve Scout Thera Connections
  """
  TIMEOUT = 2

  def __init__(
    self,
    url: str = 'https://api.eve-scout.com/v2/public/signatures',
  ):
    self.eve_db = EveDb()
    self.evescout_url = url

  def augment_map(self, solar_map: SolarMap):
    """
    :param solar_map: SolarMap
    :return: Number of connections in case of success, -1 in case of failure
    """
    headers = {'User-Agent': USER_AGENT}
    try:
      result = requests.get(
        url=self.evescout_url,
        headers=headers,
        timeout=EveScout.TIMEOUT,
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
    for connection in json_response:
      connections += 1

      # Retrieve signature meta data
      source = connection['in_system_id']
      sig_source = connection['in_signature']
      dest = connection['out_system_id']
      sig_dest = connection['out_signature']
      if connection['wh_exits_outward']:
        code_source = 'K162'
        code_dest = connection['wh_type']
      else:
        code_source = connection['wh_type']
        code_dest = 'K162'

      if connection['remaining_hours'] >= 4:
        wh_life = WormholeTimespan.STABLE
      else:
        wh_life = WormholeTimespan.CRITICAL

      wh_mass = WormholeMassspan.UNKNOWN

      # Compute time elapsed from this moment to when the signature was updated
      last_modified = datetime.strptime(
        connection['updated_at'], "%Y-%m-%dT%H:%M:%S.000Z"
      )
      delta = datetime.utcnow() - last_modified
      time_elapsed = round(delta.total_seconds() / 3600.0, 1)

      if source != 0 and dest != 0:
        # Determine wormhole size
        size_result1 = self.eve_db.get_whsize_by_code(code_source)
        size_result2 = self.eve_db.get_whsize_by_code(code_dest)
        if WormholeSize.valid(size_result1):
          wh_size = size_result1
        elif WormholeSize.valid(size_result2):
          wh_size = size_result2
        else:
          # Wormhole codes are unknown => determine size based on class of wormholes
          wh_size = self.eve_db.get_whsize_by_system(source, dest)

        solar_map.add_connection(
          source,
          dest,
          ConnectionType.WORMHOLE,
          [
            sig_source,
            code_source,
            sig_dest,
            code_dest,
            wh_size,
            wh_life,
            wh_mass,
            time_elapsed,
          ],
        )

    return connections
