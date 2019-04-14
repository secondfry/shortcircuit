# evedb.py

import csv
import StringIO
from PySide import QtCore
from utility.singleton import Singleton
from solarmap import SolarMap


def dict_from_csvqfile(file_path):
  reader = None

  qfile = QtCore.QFile(file_path)
  if qfile.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
    text = qfile.readAll()
    f = StringIO.StringIO(text)
    reader = csv.reader(f, delimiter=';')

  return reader


class EveDb:
  """
  Eve Database Handler
  """

  __metaclass__ = Singleton

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
    self.gates = [[int(rows[0]), int(rows[1])] for rows in dict_from_csvqfile(":database/system_jumps.csv")]
    self.system_desc = {
      int(rows[0]): [rows[1], rows[2], float(rows[3])]
      for rows in dict_from_csvqfile(":database/system_description.csv")
    }
    self.wh_codes = {rows[0]: int(rows[1]) for rows in dict_from_csvqfile(":database/statics.csv")}

  def get_whsize_by_code(self, code):
    whsize = None
    code = code.upper()
    if code in self.wh_codes.keys():
      whsize = self.wh_codes[code]

    return whsize

  def get_class(self, system_id):
    if system_id not in self.system_desc:
      return "Unknown"

    db_class = self.system_desc[system_id][1]
    if db_class in ["HS", "LS", "NS", "Unknown"]:
      sys_class = "kspace"
    elif db_class in ["C14", "C15", "C16", "C17", "C18"]:
      sys_class = "drifter"
    else:
      sys_class = db_class
    return sys_class

  def system_type(self, system_id):
    """
    0 - highsec
    1 - lowsec
    2 - nullsec or unknown
    3 - wspace
    :param system_id:
    :return: Possbile values: 0-3
    """
    db_class = self.system_desc[system_id][1]
    if db_class == "HS":
      system_type_id = 0
    elif db_class == "LS":
      system_type_id = 1
    elif db_class == "NS" or db_class == "WH":
      system_type_id = 2
    else:
      system_type_id = 3
    return system_type_id

  def get_whsize_by_system(self, source_id, dest_id):
    source_class = self.get_class(source_id)
    dest_class = self.get_class(dest_id)
    return EveDb.SIZE_MATRIX[source_class][dest_class]

  def get_solar_map(self):
    solar_map = SolarMap(self)
    for row in self.gates:
      solar_map.add_connection(row[0], row[1], SolarMap.GATE)

    return solar_map

  def system_name_list(self):
    return [x[0] for x in self.system_desc.values()]

  def get_system_dict_pair_by_partial_name(self, part):
    ret = [None, None]
    matches = 0
    uppart = part.upper()

    for key, value in self.system_desc.iteritems():
      upval = value[0].upper()
      if upval == uppart:
        return [key, value]
      if upval.startswith(uppart):
        ret = [key, value]
        matches = matches + 1

    if matches > 1:
      return [None, None]

    return ret

  def normalize_name(self, name):
    [sid, value] = self.get_system_dict_pair_by_partial_name(name)

    if value is None:
      return None

    return value[0]

  def name2id(self, name):
    [sid, value] = self.get_system_dict_pair_by_partial_name(name)
    return sid

  def id2name(self, idx):
    try:
      sys_name = self.system_desc[idx][0]
    except KeyError:
      sys_name = None
    return sys_name
