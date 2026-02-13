# evedb.py

import csv
from enum import Enum
from os import path
from typing import Dict, List, Optional, TypedDict, Union
from typing_extensions import deprecated

from .logger import Logger
from .utility.singleton import Singleton


def get_csv_reader(filename: str):
  bundle_dir = path.abspath(path.dirname(__file__))
  filepath = path.join(bundle_dir, '..', '..', 'database', filename)
  normpath = path.normpath(filepath)
  Logger.info(normpath)

  f = open(normpath, 'r', encoding='utf-8')
  reader = csv.reader(f, delimiter=',')

  # NOTE(secondfry): skip headings.
  next(reader)

  return reader


class WormholeSize(int, Enum):
  UNKNOWN = 0
  SMALL = 1
  MEDIUM = 2
  LARGE = 3
  XLARGE = 4

  @staticmethod
  def valid(value):
    return value in [
      WormholeSize.SMALL,
      WormholeSize.MEDIUM,
      WormholeSize.LARGE,
      WormholeSize.XLARGE,
    ]


class WormholeTimespan(int, Enum):
  STABLE = 1
  CRITICAL = 2


class WormholeMassspan(int, Enum):
  UNKNOWN = 0
  STABLE = 1
  DESTAB = 2
  CRITICAL = 3


class SpaceType(int, Enum):
  HS = 1,
  LS = 2,
  NS = 3,
  WH = 4


class Restrictions(TypedDict):
  size_restriction: Dict[WormholeSize, bool]
  ignore_eol: bool
  ignore_masscrit: bool
  age_threshold: float
  security_prio: Dict[SpaceType, float]
  avoidance_list: List[int]


SystemDescription = TypedDict(
  'SystemDescription',
  {
    'class': str,
    'flags': Dict[str, bool],
    'id': int,
    'name': str,
    'region_id': int,
    'security': float,
  }
)


class SolarSystem:

  MAP_LOCATION_WORMHOLE_CLASSES = {
    int(row[0]): int(row[1])
    for row in get_csv_reader('mapLocationWormholeClasses.csv')
  }

  def __init__(
    self,
    regionID: int,
    constellationID: int,
    solarSystemID: int,
    solarSystemName: str,
    x: float,
    y: float,
    z: float,
    xMin: float,
    xMax: float,
    yMin: float,
    yMax: float,
    zMin: float,
    zMax: float,
    luminosity: float,
    border: int,
    fringe: int,
    corridor: int,
    hub: int,
    international: int,
    regional: int,
    constellation: Union[str, None],
    security: float,
    factionID: Union[int, None],
    radius: float,
    sunTypeID: Union[int, None],
    securityClass: str
  ):
    self.regionID = regionID
    self.constellationID = constellationID
    self.solarSystemID = solarSystemID
    self.solarSystemName = solarSystemName
    self.x = x
    self.y = y
    self.z = z
    self.xMin = xMin
    self.xMax = xMax
    self.yMin = yMin
    self.yMax = yMax
    self.zMin = zMin
    self.zMax = zMax
    self.luminosity = luminosity
    self.border = border
    self.fringe = fringe
    self.corridor = corridor
    self.hub = hub
    self.international = international
    self.regional = regional
    self.constellation = constellation
    self.security = security
    self.factionID = factionID
    self.radius = radius
    self.sunTypeID = sunTypeID
    self.securityClass = securityClass

  @staticmethod
  def from_row(row: List[str]) -> 'SolarSystem':
    regionID, constellationID, solarSystemID, solarSystemName, x, y, z, xMin, xMax, yMin, yMax, zMin, zMax, luminosity, border, fringe, corridor, hub, international, regional, constellation, security, factionID, radius, sunTypeID, securityClass = row
    return SolarSystem(
      int(regionID),
      int(constellationID),
      int(solarSystemID),
      solarSystemName,
      float(x),
      float(y),
      float(z),
      float(xMin),
      float(xMax),
      float(yMin),
      float(yMax),
      float(zMin),
      float(zMax),
      float(luminosity),
      int(border),
      int(fringe),
      int(corridor),
      int(hub),
      int(international),
      int(regional),
      constellation if constellation != 'None' else None,
      float(security),
      int(factionID) if factionID != 'None' else None,
      float(radius),
      int(sunTypeID) if sunTypeID != 'None' else None,
      securityClass
    )

  def is_known_space(self):
    return self.regionID > 10000000 and self.regionID < 10000070

  def is_triglavian(self):
    TRIGLAVIAN_REGION_ID = 10000070
    return self.regionID == TRIGLAVIAN_REGION_ID

  def is_zarzakh(self):
    ZARZAKH_REGION_ID = 10001000
    return self.regionID == ZARZAKH_REGION_ID

  def is_anoikis(self):
    return self.regionID > 11000000 and self.regionID < 11000034

  def is_abyssal(self):
    return self.regionID > 12000000 and self.regionID < 12000006

  def is_PR(self):
    PR_01_REGION_ID = 13000001
    return self.regionID == PR_01_REGION_ID

  def is_void(self):
    return self.regionID > 14000000 and self.regionID < 14000006

  def get_system_class(self):
    if self.is_known_space():
      if self.security > 0.45: return 'HS'
      if self.security > 0: return 'LS'
      return 'NS'

    if self.is_triglavian(): return '▲'
    if self.is_zarzakh(): return 'Z'

    if self.is_anoikis():
      system_class = self.MAP_LOCATION_WORMHOLE_CLASSES.get(self.solarSystemID)
      if system_class: return 'C{}'.format(system_class)
      region_class = self.MAP_LOCATION_WORMHOLE_CLASSES.get(self.regionID)
      if region_class: return 'C{}'.format(region_class)
      return 'C??'

    if self.is_abyssal(): return 'ADR'
    if self.is_PR(): return 'PR'
    if self.is_void(): return 'VR'

    return '??'


class Region:

  def __init__(
    self,
    regionID: int,
    regionName: str,
    x: float,
    y: float,
    z: float,
    xMin: float,
    xMax: float,
    yMin: float,
    yMax: float,
    zMin: float,
    zMax: float,
    factionID: Optional[int],
    nebula: str,
    radius: Optional[float]
  ):
    self.regionID = regionID
    self.regionName = regionName
    self.x = x
    self.y = y
    self.z = z
    self.xMin = xMin
    self.xMax = xMax
    self.yMin = yMin
    self.yMax = yMax
    self.zMin = zMin
    self.zMax = zMax
    self.factionID = factionID
    self.nebula = nebula
    self.radius = radius

  @staticmethod
  def from_row(row: List[str]):
    regionID, regionName, x, y, z, xMin, xMax, yMin, yMax, zMin, zMax, factionID, nebula, radius = row
    return Region(
      regionID=int(regionID),
      regionName=regionName,
      x=float(x),
      y=float(y),
      z=float(z),
      xMin=float(xMin),
      xMax=float(xMax),
      yMin=float(yMin),
      yMax=float(yMax),
      zMin=float(zMin),
      zMax=float(zMax),
      factionID=int(factionID) if factionID != 'None' else None,
      nebula=nebula,
      radius=float(radius) if radius != 'None' else None
    )


class EveDb(metaclass=Singleton):
  """
  Eve Database Handler
  """

  SIZE_MATRIX: Dict[str, Dict[str, WormholeSize]] = {
    "kspace": {
      "kspace": WormholeSize.XLARGE,
      "C1": WormholeSize.MEDIUM,
      "C2": WormholeSize.LARGE,
      "C3": WormholeSize.LARGE,
      "C4": WormholeSize.LARGE,
      "C5": WormholeSize.XLARGE,
      "C6": WormholeSize.XLARGE,
      "C12": WormholeSize.LARGE,
      "C13": WormholeSize.SMALL,
      "drifter": WormholeSize.LARGE,
    },
    "C1": {
      "kspace": WormholeSize.MEDIUM,
      "C1": WormholeSize.MEDIUM,
      "C2": WormholeSize.MEDIUM,
      "C3": WormholeSize.MEDIUM,
      "C4": WormholeSize.MEDIUM,
      "C5": WormholeSize.MEDIUM,
      "C6": WormholeSize.MEDIUM,
      "C12": WormholeSize.MEDIUM,
      "C13": WormholeSize.SMALL,
      "drifter": WormholeSize.MEDIUM,
    },
    "C2": {
      "kspace": WormholeSize.LARGE,
      "C1": WormholeSize.MEDIUM,
      "C2": WormholeSize.LARGE,
      "C3": WormholeSize.LARGE,
      "C4": WormholeSize.LARGE,
      "C5": WormholeSize.LARGE,
      "C6": WormholeSize.LARGE,
      "C12": WormholeSize.LARGE,
      "C13": WormholeSize.SMALL,
      "drifter": WormholeSize.LARGE,
    },
    "C3": {
      "kspace": WormholeSize.LARGE,
      "C1": WormholeSize.MEDIUM,
      "C2": WormholeSize.LARGE,
      "C3": WormholeSize.LARGE,
      "C4": WormholeSize.LARGE,
      "C5": WormholeSize.LARGE,
      "C6": WormholeSize.LARGE,
      "C12": WormholeSize.LARGE,
      "C13": WormholeSize.SMALL,
      "drifter": WormholeSize.LARGE,
    },
    "C4": {
      "kspace": WormholeSize.LARGE,
      "C1": WormholeSize.MEDIUM,
      "C2": WormholeSize.LARGE,
      "C3": WormholeSize.LARGE,
      "C4": WormholeSize.LARGE,
      "C5": WormholeSize.LARGE,
      "C6": WormholeSize.LARGE,
      "C12": WormholeSize.LARGE,
      "C13": WormholeSize.SMALL,
      "drifter": WormholeSize.LARGE,
    },
    "C5": {
      "kspace": WormholeSize.XLARGE,
      "C1": WormholeSize.MEDIUM,
      "C2": WormholeSize.LARGE,
      "C3": WormholeSize.LARGE,
      "C4": WormholeSize.LARGE,
      "C5": WormholeSize.XLARGE,
      "C6": WormholeSize.XLARGE,
      "C12": WormholeSize.LARGE,
      "C13": WormholeSize.SMALL,
      "drifter": WormholeSize.LARGE,
    },
    "C6": {
      "kspace": WormholeSize.XLARGE,
      "C1": WormholeSize.MEDIUM,
      "C2": WormholeSize.LARGE,
      "C3": WormholeSize.LARGE,
      "C4": WormholeSize.LARGE,
      "C5": WormholeSize.XLARGE,
      "C6": WormholeSize.XLARGE,
      "C12": WormholeSize.LARGE,
      "C13": WormholeSize.SMALL,
      "drifter": WormholeSize.LARGE,
    },
    "C12": {
      "kspace": WormholeSize.LARGE,
      "C1": WormholeSize.MEDIUM,
      "C2": WormholeSize.LARGE,
      "C3": WormholeSize.LARGE,
      "C4": WormholeSize.LARGE,
      "C5": WormholeSize.LARGE,
      "C6": WormholeSize.LARGE,
      "C12": WormholeSize.LARGE,
      "C13": WormholeSize.SMALL,
      "drifter": WormholeSize.LARGE,
    },
    "C13": {
      "kspace": WormholeSize.SMALL,
      "C1": WormholeSize.SMALL,
      "C2": WormholeSize.SMALL,
      "C3": WormholeSize.SMALL,
      "C4": WormholeSize.SMALL,
      "C5": WormholeSize.SMALL,
      "C6": WormholeSize.SMALL,
      "C12": WormholeSize.SMALL,
      "C13": WormholeSize.SMALL,
      "drifter": WormholeSize.SMALL,
    },
    "drifter": {
      "kspace": WormholeSize.LARGE,
      "C1": WormholeSize.MEDIUM,
      "C2": WormholeSize.LARGE,
      "C3": WormholeSize.LARGE,
      "C4": WormholeSize.LARGE,
      "C5": WormholeSize.LARGE,
      "C6": WormholeSize.LARGE,
      "C12": WormholeSize.LARGE,
      "C13": WormholeSize.SMALL,
      "drifter": WormholeSize.LARGE,
    }
  }

  ZARZAKH_SYSTEM_ID = 30100000

  def __init__(self):
    filename_statics = 'statics.csv'
    filaname_renames = 'renames.csv'

    # NOTE(secondfry): thank you, Steve Ronuken.
    # @see https://www.fuzzwork.co.uk/dump/
    filename_gates = 'mapSolarSystemJumps.csv'
    filename_descriptions = 'mapSolarSystems.csv'
    filename_regions = 'mapRegions.csv'

    self._init_gates(get_csv_reader(filename_gates))
    self._init_system_descriptions(get_csv_reader(filename_descriptions))
    self._init_renames(get_csv_reader(filaname_renames))
    self._init_regions(get_csv_reader(filename_regions))

    self.wh_codes: Dict[str, WormholeSize] = {
      rows[0]: WormholeSize(int(rows[1]))
      for rows in get_csv_reader(filename_statics)
    }

  def _init_gates(self, reader):
    """
    Data is stored in 6 column format.
    0: fromRegionID,
    1: fromConstellationID,
    2: fromSolarSystemID,
    3: toSolarSystemID,
    4: toConstellationID,
    5: toRegionID.
    """
    self.gates = [[int(row[2]), int(row[3])] for row in reader]

  def _init_system_descriptions(self, reader):
    self.system_desc: Dict[int, SystemDescription] = {}
    self.region_systems: Dict[int, List[SystemDescription]] = {}
    for row in reader:
      system = SolarSystem.from_row(row)
      description = SystemDescription({
        'class': system.get_system_class(),
        'flags': {
          'triglavian': system.is_triglavian()
        },
        'id': system.solarSystemID,
        'name': system.solarSystemName,
        'region_id': system.regionID,
        'security': system.security
      })
      self.system_desc[system.solarSystemID] = description
      if description['region_id'] not in self.region_systems:
        self.region_systems[description['region_id']] = []
      self.region_systems[description['region_id']].append(description)

  def _init_renames(self, reader):
    for row in reader:
      id = int(row[0])
      name = row[1]
      self.system_desc[id]['name'] = name

  def _init_regions(self, reader):
    self.regions: Dict[int, Region] = {}
    for row in reader:
      region = Region.from_row(row)
      self.regions[region.regionID] = region

  def get_whsize_by_code(self, code: Optional[str]) -> WormholeSize:
    if not code:
      return WormholeSize.UNKNOWN
    return self.wh_codes.get(code.upper(), WormholeSize.UNKNOWN)

  def get_class(self, system_id: int):
    if system_id not in self.system_desc:
      return "Unknown"

    db_class = self.system_desc[system_id]['class']
    # FIXME learn about triglavian wormhole sizes
    if db_class in ["HS", "LS", "NS", "▲", "Unknown"]:
      sys_class = "kspace"
    elif db_class in ["C14", "C15", "C16", "C17", "C18"]:
      sys_class = "drifter"
    else:
      sys_class = db_class
    return sys_class

  @deprecated('FIXME(secondfry): this seems to be broken')
  def system_type(self, system_id: int) -> SpaceType:
    db_class = self.system_desc[system_id]['class']

    return {
      'HS': SpaceType.HS,
      'LS': SpaceType.LS,
      'NS': SpaceType.NS,
      'WH': SpaceType.WH,
    }.get(db_class, SpaceType.NS)

  def get_whsize_by_system(self, source_id: int, dest_id: int) -> WormholeSize:
    source_class = self.get_class(source_id)
    dest_class = self.get_class(dest_id)
    return EveDb.SIZE_MATRIX[source_class][dest_class]

  def system_name_list(self):
    return [x['name'] for x in self.system_desc.values()]

  def region_name_list(self):
    return [x.regionName for x in self.regions.values()]

  def get_system_dict_pair_by_partial_name(self, part: str):
    if not part:
      return (None, None)

    ret = (None, None)
    matches = 0
    part_upper = part.upper()

    for sid, system in self.system_desc.items():
      name_upper = system['name'].upper()
      if name_upper == part_upper:
        return (sid, system)
      if name_upper.startswith(part_upper):
        ret = (sid, system)
        matches = matches + 1

    if matches > 1:
      return (None, None)

    return ret

  # TODO properly type this
  def normalize_name(self, name) -> Union[None, str]:
    _, system = self.get_system_dict_pair_by_partial_name(name)

    if system is None:
      return None

    return system['name']

  def normalize_region_name(self, partial: str):
    for region in self.regions.values():
      if partial.lower() in region.regionName.lower():
        return region.regionName
    return None

  # TODO properly type this
  def name2id(self, name):
    [sid, _] = self.get_system_dict_pair_by_partial_name(name)
    return sid

  # TODO properly type this
  def id2name(self, sid):
    try:
      sys_name = self.system_desc[sid]['name']
    except KeyError:
      sys_name = None
    return sys_name

  def region_name_to_id(self, name: str):
    for region in self.regions.values():
      if name == region.regionName:
        return region.regionID
    return None

  def get_region_system_ids(self, idx: int):
    return [x["id"] for x in self.region_systems[idx]]
