# evedb.py

import csv
import sys
from enum import Enum
from os import path
from typing import Dict, List, TypedDict, Union

from importlib.resources import files

from .logger import Logger
from .utility.singleton import Singleton


def get_dict_from_csv(filename: str):
  file = files('resources.database').joinpath(filename)
  Logger.info(file.name)

  data = file.read_text()
  reader = csv.reader(data, delimiter=';')

  return reader


class WormholeSize(int, Enum):
  UNKNOWN = 0
  SMALL = 1
  MEDIUM = 2
  LARGE = 3
  XLARGE = 4


class WormholeTimespan(int, Enum):
  STABLE = 1
  CRITICAL = 2


class WormholeMassspan(int, Enum):
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
  'SystemDescription', {
    'region_id': int,
    'id': int,
    'name': str,
    'class': str,
    'security': float,
    'flags': Dict[str, bool]
  }
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

  TRIGLAVIAN_REGION_ID: int = 10000070

  def __init__(self):
    filename_gates = 'system_jumps.csv'
    filename_descriptions = 'system_description.csv'
    filename_statics = 'statics.csv'

    self.gates = [[int(rows[0]), int(rows[1])] for rows in get_dict_from_csv(filename_gates)]
    self.system_desc: Dict[int, SystemDescription] = {
      int(rows[1]): {
        'region_id': int(rows[0]),
        'id': int(rows[1]),
        'name': rows[2],
        'class': rows[3],
        'security': float(rows[4]),
        'flags': {
          'triglavian': self.is_triglavian(int(rows[0]))
        }
      }
      for rows in get_dict_from_csv(filename_descriptions)
    }
    self.wh_codes: Dict[str, WormholeSize] = {
      rows[0]: WormholeSize(int(rows[1]))
      for rows in get_dict_from_csv(filename_statics)
    }

  def is_triglavian(self, region_id: int):
    return region_id == self.TRIGLAVIAN_REGION_ID

  def get_whsize_by_code(self, code: str) -> WormholeSize:
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

  def system_type(self, system_id: int) -> SpaceType:
    db_class = self.system_desc[system_id]['class']

    return {'HS': SpaceType.HS, 'LS': SpaceType.LS, 'NS': SpaceType.NS, 'WH': SpaceType.WH}.get(db_class, SpaceType.NS)

  def get_whsize_by_system(self, source_id: int, dest_id: int) -> WormholeSize:
    source_class = self.get_class(source_id)
    dest_class = self.get_class(dest_id)
    return EveDb.SIZE_MATRIX[source_class][dest_class]

  def system_name_list(self):
    return [x['name'] for x in self.system_desc.values()]

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
