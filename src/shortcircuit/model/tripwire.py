# tripwire.py

import json
from datetime import datetime
from typing import Dict, List, Literal, Optional, TypedDict, Union

import requests
from shortcircuit import USER_AGENT

from .evedb import EveDb, WormholeSize, WormholeMassspan, WormholeTimespan
from .logger import Logger
from .solarmap import ConnectionType, SolarMap
from .utility.configuration import Configuration


class TripwireESIToken(TypedDict):
  """
  Represents ESI authentication token data from Tripwire.
  """
  characterID: str
  characterName: str
  accessToken: str
  refreshToken: str
  tokenExpire: str


class TripwireSignature(TypedDict):
  """
  Represents a signature entry from the Tripwire API.
  
  Signatures are scan results in a solar system, typically representing
  wormholes, combat sites, data/relic sites, etc.
  """
  id: str
  signatureID: Optional[str]  # Can be "???", null, or actual sig like "ABC-123"
  systemID: str
  type: str
  name: Optional[str]
  bookmark: Optional[str]
  lifeTime: str
  lifeLeft: str
  lifeLength: str
  createdByID: str
  createdByName: str
  modifiedByID: str
  modifiedByName: str
  modifiedTime: str
  maskID: str


class TripwireWormhole(TypedDict):
  """
  Represents a wormhole connection from the Tripwire API.
  
  Wormholes connect two signatures (initialID and secondaryID) which
  are references to signature IDs in the signatures dictionary.
  """
  id: str
  initialID: str  # Reference to a signature ID
  secondaryID: str  # Reference to another signature ID
  type: Optional[str]  # Wormhole type code (e.g., "K162", "GATE") or empty string/null
  parent: Optional[str]  # "initial", "secondary", empty string, or null
  life: str  # "stable", "critical"
  mass: str  # "stable", "destab", "critical"
  maskID: str


class TripwireFlare(TypedDict):
  """
  Represents a system flare (wormhole effect) from Tripwire.
  """
  systemID: str
  flare: str  # Color: "red", "yellow", "green", etc.
  time: str  # Timestamp when the flare was recorded


class TripwireFlares(TypedDict):
  """
  Represents the flares (wormhole effects) data from Tripwire.
  """
  flares: List[TripwireFlare]
  last_modified: str


class RawTripwireChain(TypedDict):
  """
  Represents the complete Tripwire API response structure.
  
  The chain contains dictionaries of signatures and wormholes, keyed by their
  unique numerical IDs (as strings). Wormholes reference signatures via
  initialID and secondaryID fields.
  
  Note: signatures and wormholes can be empty lists [] when there are no
  connections in the chain, or dictionaries when connections exist.
  """
  esi: Dict[str, TripwireESIToken]  # ESI authentication tokens keyed by character ID
  sync: str  # Synchronization timestamp
  signatures: Union[Dict[str, TripwireSignature], List]  # Signatures keyed by ID, or [] if empty
  wormholes: Union[Dict[str, TripwireWormhole], List]  # Wormholes keyed by ID, or [] if empty
  flares: TripwireFlares  # System effects data
  proccessTime: str  # API processing time (note: typo in API)
  discord_integration: bool  # Discord integration flag


class TripwireChain(TypedDict):
  """
  Represents a normalized Tripwire API response where signatures and wormholes
  are dictionaries.
  """
  esi: Dict[str, TripwireESIToken]
  sync: str
  signatures: Dict[str, TripwireSignature]
  wormholes: Dict[str, TripwireWormhole]
  flares: TripwireFlares
  proccessTime: str
  discord_integration: bool


SignatureKey = Literal['initialID', 'secondaryID']


class Tripwire:
  """
  Tripwire handler
  """

  WTYPE_UNKNOWN = '----'
  SIG_UNKNOWN = '-------'

  def __init__(self, username: str, password: str, url: str):
    self.eve_db = EveDb()
    self.username = username
    self.password = password
    self.url = url
    self.session_requests = self.login()
    self.chain: TripwireChain = self._empty_chain()

  @staticmethod
  def _empty_chain() -> TripwireChain:
    return {
      'esi': {},
      'sync': '',
      'signatures': {},
      'wormholes': {},
      'flares': {
        'flares': [],
        'last_modified': '',
      },
      'proccessTime': '',
      'discord_integration': False,
    }

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
    proxies: Dict[str, str] = {}
    proxy = Configuration.settings.value('proxy')
    if proxy:
      proxies = {
        'http': str(proxy),
        'https': str(proxy),
      }

    try:
      result = session_requests.post(
        login_url,
        data=payload,
        headers=headers,
        proxies=proxies,
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

  def fetch_api_refresh(self, system_id="30000142") -> Optional[RawTripwireChain]:
    Logger.debug('Getting {}...'.format(system_id))

    if not self.session_requests:
      return None

    refresh_url = '{}/refresh.php'.format(self.url)
    payload = {
      'mode': 'init',
      'systemID': system_id,
    }
    headers = {
      'Referer': refresh_url,
      'User-Agent': USER_AGENT,
    }
    proxies: Dict[str, str] = {}
    proxy = Configuration.settings.value('proxy')
    if proxy:
      proxies = {
        'http': str(proxy),
        'https': str(proxy),
      }

    try:
      result = self.session_requests.get(
        refresh_url,
        params=payload,
        headers=headers,
        proxies=proxies,
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

    response: RawTripwireChain = result.json()
    return response

  def _normalize_chain(self, raw_chain: Optional[RawTripwireChain]) -> TripwireChain:
    if raw_chain is None:
      return self._empty_chain()

    signatures = raw_chain['signatures'] if isinstance(raw_chain['signatures'], dict) else {}
    wormholes = raw_chain['wormholes'] if isinstance(raw_chain['wormholes'], dict) else {}

    return {
      'esi': raw_chain['esi'],
      'sync': raw_chain['sync'],
      'signatures': signatures,
      'wormholes': wormholes,
      'flares': raw_chain['flares'],
      'proccessTime': raw_chain['proccessTime'],
      'discord_integration': raw_chain['discord_integration'],
    }

  def get_chain(self, system_id="30000142") -> bool:
    """
    Fetch and normalize the Tripwire chain data.
    
    Updates self.chain only if fetch is successful, preserving existing data on failure.
    
    :param system_id: str Numerical solar system ID
    :return: True if fetch was successful, False on connection/auth failure
    """
    raw_chain = self.fetch_api_refresh(system_id)
    
    if raw_chain is None:
      return False
    
    self.chain = self._normalize_chain(raw_chain)
    return True

  def _get_parent_sibling_keys(self, wormhole: TripwireWormhole) -> tuple[SignatureKey, SignatureKey]:
    """
    Determine which signature IDs represent the parent (in) and sibling (out) sides.
    
    The parent field indicates direction: 'initial', 'secondary', empty string, or null.
    If not set, defaults to 'initial' as the parent.
    
    :param wormhole: TripwireWormhole to get keys for
    :return: Tuple of (parent_key, sibling_key) like ('initialID', 'secondaryID')
    """
    if wormhole['parent'] == 'secondary':
      return ('secondaryID', 'initialID')
    return ('initialID', 'secondaryID')

  def _get_wormhole_signatures(
    self, wormhole: TripwireWormhole
  ) -> tuple[TripwireSignature, TripwireSignature]:
    """
    Get the signature pair (in, out) for a wormhole connection.
    
    Determines the correct direction based on the wormhole's parent field,
    then retrieves both signatures from the chain.
    
    :param wormhole: TripwireWormhole to get signatures for
    :return: Tuple of (signature_in, signature_out)
    :raises KeyError: If signatures are not found in the chain
    """
    parent, sibling = self._get_parent_sibling_keys(wormhole)
    signature_in: TripwireSignature = self.chain['signatures'][str(wormhole[parent])]
    signature_out: TripwireSignature = self.chain['signatures'][str(wormhole[sibling])]
    return (signature_in, signature_out)

  def _get_wormhole_properties(
    self, wormhole: TripwireWormhole, system_from: int, system_to: int
  ) -> tuple[str, str, WormholeTimespan, WormholeMassspan, WormholeSize]:
    """
    Determine wormhole properties (types, life, mass, size) based on connection type.
    
    GATE type wormholes (permanent connections like jump bridges) are always stable
    and permanent, while regular wormholes have variable properties.
    
    :param wormhole: TripwireWormhole to get properties for
    :param system_from: Source system ID
    :param system_to: Destination system ID
    :return: Tuple of (wh_type_in, wh_type_out, wh_life, wh_mass, wh_size)
    """
    is_gate = wormhole['type'] == 'GATE'
    
    if is_gate:
      wh_type_in = 'GATE'
      wh_type_out = 'GATE'
      wh_life = WormholeTimespan.STABLE
      wh_mass = WormholeMassspan.STABLE
      wh_size = WormholeSize.UNKNOWN  # GATE type doesn't have a size
      return (wh_type_in, wh_type_out, wh_life, wh_mass, wh_size)
    
    wh_type_in = wormhole['type'] if wormhole['type'] else Tripwire.WTYPE_UNKNOWN
    wh_type_out = Tripwire.WTYPE_UNKNOWN if wh_type_in == Tripwire.WTYPE_UNKNOWN else 'K162'

    wh_life = {
      'stable': WormholeTimespan.STABLE,
      'critical': WormholeTimespan.CRITICAL,
    }.get(wormhole['life'], WormholeTimespan.CRITICAL)

    wh_mass = {
      'stable': WormholeMassspan.STABLE,
      'destab': WormholeMassspan.DESTAB,
      'critical': WormholeMassspan.CRITICAL,
    }.get(wormhole['mass'], WormholeMassspan.CRITICAL)

    wh_size = self.eve_db.get_whsize_by_code(wormhole['type'])
    if not WormholeSize.valid(wh_size):
      # Wormhole codes are unknown => determine size based on class of wormholes
      wh_size = self.eve_db.get_whsize_by_system(system_from, system_to)

    return (wh_type_in, wh_type_out, wh_life, wh_mass, wh_size)

  def _process_wormhole(
    self, wormhole: TripwireWormhole, solar_map: SolarMap
  ) -> bool:
    """
    Process a single wormhole connection from Tripwire and add it to the solar map.
    
    The wormhole contains initialID and secondaryID fields which reference
    signature IDs in self.chain['signatures']. These TripwireSignature objects
    contain the actual system IDs and signature codes for both ends of the connection.
    
    :param wormhole: TripwireWormhole from Tripwire API
    :param solar_map: SolarMap to add the connection to
    :return: True if connection was added, False otherwise
    """
    # Validate that both signatures exist in the chain
    if str(wormhole['initialID']) not in self.chain['signatures']:
      return False

    if str(wormhole['secondaryID']) not in self.chain['signatures']:
      return False

    signature_in, signature_out = self._get_wormhole_signatures(wormhole)

    system_from = convert_to_int(signature_in['systemID'])
    system_to = convert_to_int(signature_out['systemID'])

    if system_from == 0 or system_from < 10000 or system_to == 0 or system_to < 10000:
      return False

    sig_id_in = self.format_tripwire_signature(signature_in['signatureID'])
    sig_id_out = self.format_tripwire_signature(
      signature_out['signatureID']
    )

    # Get wormhole properties (handles GATE vs regular wormholes)
    wh_type_in, wh_type_out, wh_life, wh_mass, wh_size = self._get_wormhole_properties(
      wormhole, system_from, system_to
    )

    # Compute time elapsed from this moment to when the signature was updated
    last_modified = datetime.strptime(
      signature_in['modifiedTime'], "%Y-%m-%d %H:%M:%S"
    )
    delta = datetime.utcnow() - last_modified
    time_elapsed = round(delta.total_seconds() / 3600.0, 1)

    # Add wormhole connection to solar system
    solar_map.add_connection(
      system_from,
      system_to,
      ConnectionType.WORMHOLE,
      [
        sig_id_in,
        wh_type_in,
        sig_id_out,
        wh_type_out,
        wh_size,
        wh_life,
        wh_mass,
        time_elapsed,
      ],
    )
    return True

  def augment_map(self, solar_map: SolarMap):
    """
    Augment the solar map with wormhole connections from Tripwire.
    
    :param solar_map: SolarMap to augment
    :return: Number of connections added, or -1 on connection/auth failure
    """
    success = self.get_chain()
    
    if not success:
      return -1
    
    if len(self.chain['wormholes']) == 0:
      return 0

    # We got some sort of response so at least we're logged in
    connections = 0

    # Process wormholes
    for _, wormhole in self.chain['wormholes'].items():
      try:
        if self._process_wormhole(wormhole, solar_map):
          connections += 1
      except Exception as e:
        Logger.error('pepega', exc_info=e)

    return connections

  @staticmethod
  def format_tripwire_wormhole_type(wtype):
    if not wtype or wtype == '' or wtype == '????':
      return Tripwire.WTYPE_UNKNOWN

    return wtype

  @staticmethod
  def format_tripwire_signature(signatureID: Optional[str]):
    if not signatureID or signatureID == '' or signatureID == '???':
      return Tripwire.SIG_UNKNOWN

    left = signatureID[0:3]
    right = signatureID[3:6]
    letters = left.upper() if left.isalpha() else right.upper() if right.isalpha() else '---'
    numbers = right if right.isnumeric() else left if left.isnumeric() else '---'
    return '{}-{}'.format(letters, numbers)


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
