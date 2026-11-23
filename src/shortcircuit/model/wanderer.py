# wanderer.py

from datetime import UTC, datetime
from typing import Dict, Optional, Tuple

import requests
from shortcircuit import USER_AGENT

from .evedb import EveDb, WormholeMassspan, WormholeSize, WormholeTimespan
from .logger import Logger
from .mapper_base import MapperSource
from .solarmap import ConnectionType, SolarMap

# Wanderer's connection state codes, from wanderer-industries/wanderer
# assets/js/hooks/Mapper/types/connection.ts and
# lib/wanderer_app/api/map_connection.ex.
#   type:          0 = wormhole, 1 = gate, 2 = bridge
#   time_status:   0 = normal, 1 = EOL 1h, 2 = EOL 4h, 3 = 4.5h, 4 = 16h,
#                  5 = 24h, 6 = 48h
#   mass_status:   0 = more than half, 1 = less than half, 2 = critical (<10%)
#   ship_size_type: 0 = frigate, 1 = medium, 3 = freight, 4 = capital; 2 is
#                  "Normal" (assets/js/hooks/Mapper/components/map/constants.ts
#                  SHIP_SIZES_NAMES) and Wanderer's default for any mass it
#                  doesn't match (lib/wanderer_app/utils/eve_util.ex
#                  get_connection_size_status), so it is treated as unknown
#                  and sized by system pair
CONNECTION_TYPE_WORMHOLE = 0
EOL_TIME_STATUSES = (1, 2)
MASS_HALF = 1
MASS_CRITICAL = 2
SHIP_SIZE_TO_WH_SIZE = {
  0: WormholeSize.SMALL,
  1: WormholeSize.MEDIUM,
  3: WormholeSize.XLARGE,
  4: WormholeSize.XLARGE,
}

SIG_UNKNOWN = '???'
TYPE_UNKNOWN = '----'


class Wanderer(MapperSource):
  """
  Wanderer wormhole mapper connections provider.

  Wanderer (https://github.com/wanderer-industries/wanderer) exposes a map
  over a REST API authenticated with a per-map bearer token (Map Settings ->
  Public Api -> Generate).

  The holes come from GET /api/maps/:map/connections: it includes holes
  Wanderer recorded from character jumps or that were drawn by hand, which
  have no signature, and it drops a hole when the connection is deleted,
  whereas a signature keeps its linked system after its connection is gone.
  GET /api/maps/:map/signatures only adds what connections lack: the
  signature IDs on each side and, where scanned, the hole's type code. If
  the signatures request fails, the holes are still routed, without sig IDs.
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
    is_valid, error = self.validate_config()
    if not is_valid:
      Logger.error(f"Wanderer '{self.name}' misconfigured: {error}")
      return -1

    connections_list = self._get('connections')
    if connections_list is None:
      return -1

    signatures = self._get('signatures')
    if signatures is None:
      Logger.warning(f"Wanderer '{self.name}': signatures unavailable, routing without sig IDs")
      signatures = []
    sig_index = self._index_signatures(signatures)

    connections = 0
    for conn in connections_list:
      if self._add_connection(conn, sig_index, solar_map):
        connections += 1
    return connections

  def _add_connection(self, conn, sig_index, solar_map: SolarMap) -> bool:
    if not isinstance(conn, dict):
      return False
    if self._as_int(conn.get('type'), CONNECTION_TYPE_WORMHOLE) != CONNECTION_TYPE_WORMHOLE:
      return False
    source = self._as_int(conn.get('solar_system_source'), 0)
    dest = self._as_int(conn.get('solar_system_target'), 0)
    if not source or not dest:
      return False

    sig_source = sig_index.get((source, dest))
    sig_dest = sig_index.get((dest, source))
    code_source = self._sig_type(sig_source)
    code_dest = self._sig_type(sig_dest)
    if code_source is None and code_dest is None:
      # Wanderer copies the linking signature's type onto the connection,
      # and that signature sits in the connection's source system.
      code_source = self._clean_code(conn.get('wormhole_type'))
    code_source, code_dest = self._infer_far_side(code_source, code_dest)

    wh_size = self._size(conn, code_source, code_dest, source, dest)
    time_status = self._as_int(conn.get('time_status'), 0)
    mass_status = self._as_int(conn.get('mass_status'), 0)
    wh_life = (
      WormholeTimespan.CRITICAL if time_status in EOL_TIME_STATUSES else WormholeTimespan.STABLE
    )
    if mass_status == MASS_CRITICAL:
      wh_mass = WormholeMassspan.CRITICAL
    elif mass_status == MASS_HALF:
      wh_mass = WormholeMassspan.DESTAB
    else:
      wh_mass = WormholeMassspan.STABLE

    return solar_map.add_connection(
      source,
      dest,
      ConnectionType.WORMHOLE,
      [
        self._sig_id(sig_source),
        code_source,
        self._sig_id(sig_dest),
        code_dest,
        wh_size,
        wh_life,
        wh_mass,
        self._time_elapsed(conn.get('updated_at')),
      ],
      source_name=self.name,
    )

  @staticmethod
  def _index_signatures(signatures) -> Dict[Tuple[int, int], dict]:
    """Wormhole signatures keyed by (system they sit in, system they lead to)."""
    index = {}
    for sig in signatures:
      if not isinstance(sig, dict):
        continue
      if str(sig.get('group') or '').lower() != 'wormhole':
        continue
      system = Wanderer._as_int(sig.get('solar_system_id'), 0)
      linked = Wanderer._as_int(sig.get('linked_system_id'), 0)
      if system and linked:
        index[(system, linked)] = sig
    return index

  @staticmethod
  def _infer_far_side(code_source, code_dest):
    """A known non-K162 type means the far side is a K162; otherwise unknown."""
    if code_source and code_source != 'K162' and code_dest is None:
      code_dest = 'K162'
    elif code_dest and code_dest != 'K162' and code_source is None:
      code_source = 'K162'
    return code_source or TYPE_UNKNOWN, code_dest or TYPE_UNKNOWN

  def _size(self, conn, code_source, code_dest, source, dest) -> WormholeSize:
    for code in (code_source, code_dest):
      if code not in (TYPE_UNKNOWN, 'K162'):
        size = self.eve_db.get_whsize_by_code(code)
        if WormholeSize.valid(size):
          return size
    ship_size = self._as_int(conn.get('ship_size_type'), None)
    if ship_size in SHIP_SIZE_TO_WH_SIZE:
      return SHIP_SIZE_TO_WH_SIZE[ship_size]
    return self.eve_db.get_whsize_by_system(source, dest)

  @staticmethod
  def _clean_code(code) -> Optional[str]:
    code = str(code or '').strip().upper()
    return code or None

  @staticmethod
  def _sig_type(sig) -> Optional[str]:
    return Wanderer._clean_code(sig.get('type')) if sig else None

  @staticmethod
  def _sig_id(sig) -> str:
    return (sig.get('eve_id') or SIG_UNKNOWN) if sig else SIG_UNKNOWN

  @staticmethod
  def _as_int(value, default):
    try:
      return int(value)
    except (TypeError, ValueError):
      return default

  def _get(self, resource: str) -> Optional[list]:
    api_url = f"{self.url}/api/maps/{self.map_slug}/{resource}"
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
      Logger.error(f"Exception raised while trying to get Wanderer '{self.name}' {resource}")
      Logger.error(e)
      return None

    if result.status_code == 401:
      Logger.error(f"Wanderer '{self.name}': unauthorized - check the API token")
      return None
    if result.status_code == 404:
      Logger.error(f"Wanderer '{self.name}': map '{self.map_slug}' not found - check URL and map slug")
      return None
    if result.status_code != 200:
      Logger.error(f"Wanderer '{self.name}': HTTP {result.status_code} for {resource}")
      return None

    try:
      payload = result.json()
    except ValueError as e:
      Logger.error(f"Wanderer '{self.name}': invalid JSON response for {resource}: {e}")
      return None

    data = payload.get('data') if isinstance(payload, dict) else None
    if not isinstance(data, list):
      Logger.error(f"Wanderer '{self.name}': unexpected response shape for {resource}")
      return None
    return data

  @staticmethod
  def _time_elapsed(updated_at: Optional[str]) -> float:
    """Hours since the connection was last updated; 0.0 when unknown."""
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
