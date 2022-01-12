# solarmap.py

import heapq
from enum import Enum
from typing import Dict, List, Tuple

from shortcircuit.model.logger import Logger
from typing_extensions import Self

from .evedb import (EveDb, Restrictions, SpaceType, WormholeSize, WormholeMassspan, WormholeTimespan)


class ConnectionType(Enum):
  GATE = 1
  WORMHOLE = 2


class SolarSystem:
  """
  Solar system handler
  """

  def __init__(self, key: int):
    self.id = key
    self.connected_to: Dict[SolarSystem, Tuple[ConnectionType, List]] = {}

  def add_neighbor(self, neighbor: Self, weight: Tuple[ConnectionType, List]):
    # Ignoring unspecified GATE connections between systems
    # FIXME this will ignore wormhole connections between gate-neighbors
    if neighbor in self.connected_to:
      return

    self.connected_to[neighbor] = weight

  def get_connections(self):
    return self.connected_to.keys()

  def get_id(self) -> int:
    return self.id

  def get_weight(self, neighbor: Self) -> Tuple[ConnectionType, List]:
    return self.connected_to[neighbor]


class SolarMap:
  """
  Solar map handler
  """

  def __init__(self, eve_db: EveDb):
    self.eve_db: EveDb = eve_db
    self.systems_list: Dict[int, SolarSystem] = {}
    self.total_systems: int = 0

    self._init_gates()

  def _init_gates(self):
    for row in self.eve_db.gates:
      self.add_connection(row[0], row[1], ConnectionType.GATE)

  def add_system(self, key: int):
    self.total_systems += 1
    new_system = SolarSystem(key)
    self.systems_list[key] = new_system
    return new_system

  def get_system(self, key: int):
    return self.systems_list.get(key, None)

  def get_all_systems(self):
    return self.systems_list.keys()

  def add_connection(
    self,
    source: int,
    destination: int,
    con_type: ConnectionType,
    con_info: List = None,
  ):
    if source not in self.systems_list:
      self.add_system(source)
    if destination not in self.systems_list:
      self.add_system(destination)

    if con_type == ConnectionType.GATE:
      self.systems_list[source].add_neighbor(self.systems_list[destination], (ConnectionType.GATE, None))
      self.systems_list[destination].add_neighbor(self.systems_list[source], (ConnectionType.GATE, None))
      return

    if con_type == ConnectionType.WORMHOLE:
      [sig_source, code_source, sig_dest, code_dest, wh_size, wh_life, wh_mass, time_elapsed] = con_info
      self.systems_list[source].add_neighbor(
        self.systems_list[destination],
        (ConnectionType.WORMHOLE, [sig_source, code_source, wh_size, wh_life, wh_mass, time_elapsed])
      )
      self.systems_list[destination].add_neighbor(
        self.systems_list[source],
        (ConnectionType.WORMHOLE, [sig_dest, code_dest, wh_size, wh_life, wh_mass, time_elapsed])
      )
      return

    Logger.error("Unknown connection type provided")

  def __contains__(self, system_id: int):
    return system_id in self.systems_list

  def __iter__(self):
    return iter(self.systems_list.values())

  def _check_neighbor(self, current_sys: SolarSystem, neighbor: SolarSystem,
                      restrictions: Restrictions) -> Tuple[bool, float]:
    con_type, con_info = current_sys.get_weight(neighbor)

    if con_type == ConnectionType.GATE:
      return True, restrictions["security_prio"][self.eve_db.system_type(neighbor.get_id())]

    if con_type != ConnectionType.WORMHOLE:
      return False, 0

    [_, _, wh_size, wh_life, wh_mass, time_elapsed] = con_info

    if restrictions["size_restriction"].get(wh_size, False):
      return False, 0

    if restrictions["ignore_eol"] and wh_life == WormholeTimespan.CRITICAL:
      return False, 0

    if restrictions["ignore_masscrit"] and wh_mass == WormholeMassspan.CRITICAL:
      return False, 0

    if time_elapsed > restrictions["age_threshold"]:
      return False, 0

    return True, restrictions["security_prio"][SpaceType.WH]

  # TODO properly type this
  def shortest_path(
    self,
    source: int,
    destination: int,
    restrictions: Restrictions,
  ):
    # We don't have those systems in our SolarMap which means it is wormhole we have no connections to.
    if source not in self.systems_list or destination not in self.systems_list:
      return []

    # Nice.
    if source == destination:
      return [source]

    # Allow source or destination to be from avoidance list.
    avoidance_list = restrictions["avoidance_list"]
    try:
      avoidance_list.remove(source)
    except ValueError:
      pass
    try:
      avoidance_list.remove(destination)
    except ValueError:
      pass

    path = []

    priority_queue: List[Tuple[int, int, SolarSystem]] = []
    visited = {self.get_system(x) for x in avoidance_list}
    distance: Dict[SolarSystem, int] = {}
    parent = {}

    # starting point
    root = self.get_system(source)
    distance[root] = 0
    heapq.heappush(priority_queue, (distance[root], id(root), root))

    while len(priority_queue) > 0:
      (_, _, current_sys) = heapq.heappop(priority_queue)
      visited.add(current_sys)

      # Found!
      if current_sys.get_id() == destination:
        path.append(destination)
        while True:
          parent_id = parent[current_sys].get_id()
          path.append(parent_id)

          if parent_id != source:
            current_sys = parent[current_sys]
          else:
            path.reverse()
            return path

      # Keep searching
      for neighbor in [x for x in current_sys.get_connections() if x not in visited]:
        proceed, risk = self._check_neighbor(current_sys, neighbor, restrictions)

        if not proceed:
          continue

        if neighbor not in distance:
          distance[neighbor] = float('inf')

        if distance[neighbor] > distance[current_sys] + risk:
          distance[neighbor] = distance[current_sys] + risk
          heapq.heappush(priority_queue, (distance[neighbor], id(neighbor), neighbor))
          parent[neighbor] = current_sys

    return path


def main():
  eve_db = EveDb()
  map = SolarMap(eve_db)
  map.add_connection(
    eve_db.name2id("Botane"),
    eve_db.name2id("Ikuchi"),
    ConnectionType.WORMHOLE,
    [
      "ABC-123",
      None,
      "DEF-456",
      None,
      WormholeSize.SMALL,
      WormholeTimespan.CRITICAL,
      WormholeMassspan.CRITICAL,
      4.25,
    ],
  )
  path = map.shortest_path(
    eve_db.name2id("Dodixie"),
    eve_db.name2id("Jita"),
    {
      "size_restriction": {
        WormholeSize.SMALL: False,
        WormholeSize.MEDIUM: True,
        WormholeSize.LARGE: True,
        WormholeSize.XLARGE: True,
      },
      "avoidance_list": [],
      "security_prio": {
        SpaceType.HS: 1,
        SpaceType.LS: 1,
        SpaceType.NS: 1,
        SpaceType.WH: 1,
      },
      "ignore_eol": False,
      "ignore_masscrit": False,
      "age_threshold": float('inf'),
    },
  )
  print([eve_db.id2name(x) for x in path])


if __name__ == "__main__":
  main()
