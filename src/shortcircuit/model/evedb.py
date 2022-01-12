# evedb.py

import csv
import sys
from enum import Enum
from os import path
from typing import Dict, List, TypedDict

from .logger import Logger
from .utility.singleton import Singleton


# https://pyinstaller.readthedocs.io/en/stable/runtime-information.html
def resource_path(relative_path):
  """ Get absolute path to resource, works for dev and for PyInstaller """
  current = path.dirname(__file__)
  resources = path.abspath(path.join(current, '../../../resources'))
  base_path = getattr(sys, '_MEIPASS', resources)

  return path.join(base_path, relative_path)


def get_dict_from_csv_qfile(file_path: str):
  result_path = resource_path(file_path)
  Logger.info(result_path)
  f = open(result_path, 'r', encoding='utf-8')
  reader = csv.reader(f, delimiter=';')

  return reader


class WormholeSize(Enum):
  UNKNOWN = 0
  SMALL = 1
  MEDIUM = 2
  LARGE = 3
  XLARGE = 4


class WormholeTimespan(Enum):
  STABLE = 1
  CRITICAL = 2


class WormholeMassspan(Enum):
  STABLE = 1
  DESTAB = 2
  CRITICAL = 3


class SpaceType(Enum):
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


class EveDb(metaclass=Singleton):
  """
  Eve Database Handler
  """

  SIZE_MATRIX: Dict[str, Dict[str, WormholeSize]] = dict(
    kspace={
      "kspace": 4,
      "C2": 2,
      "C3": 3,
      "C4": 3,
      "C4": 3,
      "C5": 4,
      "C6": 4,
      "C23": 3,
      "C24": 1,
      "drifter": 3,
    },
    C1={
      "kspace": 2,
      "C2": 2,
      "C3": 2,
      "C4": 2,
      "C4": 2,
      "C5": 2,
      "C6": 2,
      "C23": 2,
      "C24": 1,
      "drifter": 2,
    },
    C2={
      "kspace": 3,
      "C2": 2,
      "C3": 3,
      "C4": 3,
      "C4": 3,
      "C5": 3,
      "C6": 3,
      "C23": 3,
      "C24": 1,
      "drifter": 3,
    },
    C3={
      "kspace": 3,
      "C2": 2,
      "C3": 3,
      "C4": 3,
      "C4": 3,
      "C5": 3,
      "C6": 3,
      "C23": 3,
      "C24": 1,
      "drifter": 3,
    },
    C4={
      "kspace": 3,
      "C2": 2,
      "C3": 3,
      "C4": 3,
      "C4": 3,
      "C5": 3,
      "C6": 3,
      "C23": 3,
      "C24": 1,
      "drifter": 3,
    },
    C5={
      "kspace": 4,
      "C2": 2,
      "C3": 3,
      "C4": 3,
      "C4": 3,
      "C5": 4,
      "C6": 4,
      "C23": 3,
      "C24": 1,
      "drifter": 3,
    },
    C6={
      "kspace": 4,
      "C2": 2,
      "C3": 3,
      "C4": 3,
      "C4": 3,
      "C5": 4,
      "C6": 4,
      "C23": 3,
      "C24": 1,
      "drifter": 3,
    },
    C12={
      "kspace": 3,
      "C2": 2,
      "C3": 3,
      "C4": 3,
      "C4": 3,
      "C5": 3,
      "C6": 3,
      "C23": 3,
      "C24": 1,
      "drifter": 3,
    },
    C13={
      "kspace": 1,
      "C2": 1,
      "C3": 1,
      "C4": 1,
      "C4": 1,
      "C5": 1,
      "C6": 1,
      "C23": 1,
      "C24": 1,
      "drifter": 1,
    },
    drifter={
      "kspace": 3,
      "C2": 2,
      "C3": 3,
      "C4": 3,
      "C4": 3,
      "C5": 3,
      "C6": 3,
      "C23": 3,
      "C24": 1,
      "drifter": 3,
    },
  )

  TRIGLAVIAN_REGION_ID: int = 10000070

  def __init__(self):
    filepath_gates = path.join('database', 'system_jumps.csv')
    filepath_descriptions = path.join('database', 'system_description.csv')
    filepath_statics = path.join('database', 'statics.csv')

    self.gates = [[int(rows[0]), int(rows[1])] for rows in get_dict_from_csv_qfile(filepath_gates)]
    self.system_desc = {
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
      for rows in get_dict_from_csv_qfile(filepath_descriptions)
    }
    self.wh_codes: Dict[str, WormholeSize] = {rows[0]: int(rows[1]) for rows in get_dict_from_csv_qfile(filepath_statics)}

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

  # TODO properly type this
  def get_system_dict_pair_by_partial_name(self, part):
    if not part:
      return [None, None]

    ret = [None, None]
    matches = 0
    part_upper = part.upper()

    for sid, system in self.system_desc.items():
      name_upper = system['name'].upper()
      if name_upper == part_upper:
        return [sid, system]
      if name_upper.startswith(part_upper):
        ret = [sid, system]
        matches = matches + 1

    if matches > 1:
      return [None, None]

    return ret

  # TODO properly type this
  def normalize_name(self, name):
    [_, system] = self.get_system_dict_pair_by_partial_name(name)

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
