# wanderer.py

import json
from datetime import UTC, datetime
from typing import Optional

import requests
from shortcircuit import USER_AGENT

from .evedb import EveDb, WormholeMassspan, WormholeSize, WormholeTimespan
from .logger import Logger
from .mapper_base import MapperSource
from .solarmap import ConnectionType, SolarMap


class Wanderer(MapperSource):
  """
  Wanderer wormhole mapper connections provider.

  Wanderer (https://github.com/wanderer-industries/wanderer) exposes a map's
  signatures via a REST API authenticated with a per-map bearer token
  (Map Settings -> API -> Generate token). Signatures of group "Wormhole"
  that have a linked system form the connections.
  """
  TIMEOUT = 10

  def __init__(
    self,
    url: str,
    map_slug: str,
    token: str,
    name: str = "Wanderer",
  ):
    url = (url or '').strip().rstrip('/')
    if url and not (url.startswith('http://') or url.startswith('https://')):
      url = 'https://' + url
    self.url = url
    self.map_slug = (map_slug or '').strip()
    self.token = (token or '').strip()
    self.name = name
    self.eve_db = EveDb()

  def augment_map(self, solar_map: SolarMap):
    """
    :param solar_map: SolarMap
    :return: Number of connections in case of success, -1 in case of failure
    """
    signatures = self._fetch_signatures()
    if signatures is None:
      return -1

    connections = 0
    for sig in signatures:
      if sig.get('group') != 'Wormhole':
        continue

      # A connection needs both ends; an unlinked wormhole signature is
      # just a scanned sig with no destination yet.
      try:
        source = int(sig.get('solar_system_id') or 0)
        dest = int(sig.get('linked_system_id') or 0)
      except (TypeError, ValueError):
        continue
      if not source or not dest:
        continue

      wh_life, wh_mass = self._parse_custom_info(sig.get('custom_info'))

      # Wanderer stores the hole type on the scanned side; the other side
      # is a K162 by definition unless the type is unknown.
      code_source = sig.get('type') or '????'
      code_dest = 'K162' if code_source not in ('????', 'K162') else '????'

      wh_size = self.eve_db.get_whsize_by_code(code_source)
      if not WormholeSize.valid(wh_size):
        wh_size = self.eve_db.get_whsize_by_system(source, dest)

      sig_source = sig.get('eve_id') or '???'

      solar_map.add_connection(
        source,
        dest,
        ConnectionType.WORMHOLE,
        [
          sig_source,
          code_source,
          '???',
          code_dest,
          wh_size,
          wh_life,
          wh_mass,
          self._time_elapsed(sig.get('updated_at')),
        ],
        source_name=self.name,
      )
      connections += 1

    return connections

  def _fetch_signatures(self) -> Optional[list]:
    is_valid, error = self.validate_config()
    if not is_valid:
      Logger.error(f"Wanderer '{self.name}' misconfigured: {error}")
      return None

    api_url = f"{self.url}/api/maps/{self.map_slug}/signatures"
    headers = {
      'User-Agent': USER_AGENT,
      'Authorization': f"Bearer {self.token}",
      'Accept': 'application/json',
    }
    try:
      result = requests.get(
        url=api_url,
        headers=headers,
        timeout=Wanderer.TIMEOUT,
      )
    except requests.exceptions.RequestException as e:
      Logger.error(f"Exception raised while trying to get Wanderer map '{self.map_slug}'")
      Logger.error(e)
      return None

    if result.status_code == 401:
      Logger.error(f"Wanderer '{self.name}': unauthorized - check the API token")
      return None
    if result.status_code == 404:
      Logger.error(f"Wanderer '{self.name}': map '{self.map_slug}' not found - check URL and map slug")
      return None
    if result.status_code != 200:
      Logger.error(f"Wanderer '{self.name}': HTTP {result.status_code}")
      return None

    try:
      payload = result.json()
    except ValueError as e:
      Logger.error(f"Wanderer '{self.name}': invalid JSON response: {e}")
      return None

    data = payload.get('data') if isinstance(payload, dict) else None
    if not isinstance(data, list):
      Logger.error(f"Wanderer '{self.name}': unexpected response shape")
      return None
    return data

  @staticmethod
  def _parse_custom_info(custom_info):
    """
    Wanderer encodes wormhole state in a JSON blob (sometimes pre-decoded):
      time_status: 1 = stable, 2 = end of life
      mass_status: 1 = stable, 2 = destabilized, 3 = critical
    Missing/malformed info is treated as stable, matching Wanderer's own UI
    defaults for an unmarked hole.
    """
    time_status = 1
    mass_status = 1
    if custom_info:
      try:
        if isinstance(custom_info, str):
          custom_info = json.loads(custom_info)
        if isinstance(custom_info, dict):
          time_status = int(custom_info.get('time_status') or 1)
          mass_status = int(custom_info.get('mass_status') or 1)
      except (TypeError, ValueError):
        pass

    wh_life = (
      WormholeTimespan.CRITICAL if time_status == 2 else WormholeTimespan.STABLE
    )
    if mass_status == 3:
      wh_mass = WormholeMassspan.CRITICAL
    elif mass_status == 2:
      wh_mass = WormholeMassspan.DESTAB
    else:
      wh_mass = WormholeMassspan.STABLE
    return wh_life, wh_mass

  @staticmethod
  def _time_elapsed(updated_at: Optional[str]) -> float:
    """Hours since the signature was last updated; 0.0 when unknown."""
    if not updated_at:
      return 0.0
    try:
      if updated_at.endswith('Z'):
        updated_at = updated_at[:-1] + '+00:00'
      last_modified = datetime.fromisoformat(updated_at)
      if last_modified.tzinfo is None:
        last_modified = last_modified.replace(tzinfo=UTC)
    except ValueError:
      return 0.0
    delta = datetime.now(UTC) - last_modified
    return round(delta.total_seconds() / 3600.0, 1)

  def get_name(self) -> str:
    """
    Get the name of this Wanderer instance.

    Returns:
      The name of this mapper source
    """
    return self.name

  def validate_config(self) -> tuple[bool, Optional[str]]:
    """
    Validate the Wanderer configuration.

    Returns:
      Tuple of (is_valid, error_message)
    """
    if not self.url:
      return False, "URL is required"
    if not self.map_slug:
      return False, "Map slug is required"
    if not self.token:
      return False, "API token is required"
    return True, None
