# evedb.py

import csv
from PySide2 import QtCore

from .utility.singleton import Singleton


class FileReader:
  def __init__(self, file_path: str):
    self.reader = None
    self.qfile = QtCore.QFile(file_path)
    self.status = self.qfile.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text)

  def __iter__(self):
    return self

  def __next__(self):
    if self.qfile.atEnd():
      raise StopIteration
    ret = self.qfile.decodeName(self.qfile.readLine())  # I'm kinda sorry, but not at all
    if not ret:
      raise StopIteration
    return ret

  @staticmethod
  def get_dict_from_csv_qfile(file_path: str):
    return csv.reader(FileReader(file_path), delimiter=';')


class EveDb(metaclass=Singleton):
  """
  Eve Database Handler
  """

  # FIXME refactor into enum
  WHSIZE_S = 0
  WHSIZE_M = 1
  WHSIZE_L = 2
  WHSIZE_XL = 3

  SIZE_MATRIX = dict(
    kspace={"kspace": 3, "C1": 1, "C2": 2, "C3": 2, "C4": 2, "C5": 3, "C6": 3, "C12": 2, "C13": 0, "drifter": 2},
    C1={"kspace": 1, "C1": 1, "C2": 1, "C3": 1, "C4": 1, "C5": 1, "C6": 1, "C12": 1, "C13": 0, "drifter": 1},
    C2={"kspace": 2, "C1": 1, "C2": 2, "C3": 2, "C4": 2, "C5": 2, "C6": 2, "C12": 2, "C13": 0, "drifter": 2},
    C3={"kspace": 2, "C1": 1, "C2": 2, "C3": 2, "C4": 2, "C5": 2, "C6": 2, "C12": 2, "C13": 0, "drifter": 2},
    C4={"kspace": 2, "C1": 1, "C2": 2, "C3": 2, "C4": 2, "C5": 2, "C6": 2, "C12": 2, "C13": 0, "drifter": 2},
    C5={"kspace": 3, "C1": 1, "C2": 2, "C3": 2, "C4": 2, "C5": 3, "C6": 3, "C12": 2, "C13": 0, "drifter": 2},
    C6={"kspace": 3, "C1": 1, "C2": 2, "C3": 2, "C4": 2, "C5": 3, "C6": 3, "C12": 2, "C13": 0, "drifter": 2},
    C12={"kspace": 2, "C1": 1, "C2": 2, "C3": 2, "C4": 2, "C5": 2, "C6": 2, "C12": 2, "C13": 0, "drifter": 2},
    C13={"kspace": 0, "C1": 0, "C2": 0, "C3": 0, "C4": 0, "C5": 0, "C6": 0, "C12": 0, "C13": 0, "drifter": 0},
    drifter={"kspace": 2, "C1": 1, "C2": 2, "C3": 2, "C4": 2, "C5": 2, "C6": 2, "C12": 2, "C13": 0, "drifter": 2},
  )

  def __init__(self):
    self.gates = [[int(rows[0]), int(rows[1])] for rows in FileReader.get_dict_from_csv_qfile(':database/system_jumps.csv')]
    self.system_desc = {
      int(rows[0]): {
        'id': int(rows[0]),
        'name': rows[1],
        'class': rows[2],
        'security': float(rows[3])
      }
      for rows in FileReader.get_dict_from_csv_qfile(':database/system_description.csv')
    }
    self.wh_codes = {rows[0]: int(rows[1]) for rows in FileReader.get_dict_from_csv_qfile(':database/statics.csv')}

  # TODO properly type this
  def get_whsize_by_code(self, code):
    whsize = None
    code = code.upper()
    if code in self.wh_codes.keys():
      whsize = self.wh_codes[code]

    return whsize

  # TODO properly type this
  def get_class(self, system_id):
    if system_id not in self.system_desc:
      return "Unknown"

    db_class = self.system_desc[system_id]['class']
    if db_class in ["HS", "LS", "NS", "Unknown"]:
      sys_class = "kspace"
    elif db_class in ["C14", "C15", "C16", "C17", "C18"]:
      sys_class = "drifter"
    else:
      sys_class = db_class
    return sys_class

  # TODO properly type this
  def system_type(self, system_id):
    """
    0 - highsec
    1 - lowsec
    2 - nullsec or unknown
    3 - wspace

    :param system_id:
    :return: Possbile values: 0-3
    """
    db_class = self.system_desc[system_id]['class']
    return {
      'HS': 0,
      'LS': 1,
      'NS': 2,
      'WH': 3
    }.get(db_class, 2)

  # TODO properly type this
  def get_whsize_by_system(self, source_id, dest_id):
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
