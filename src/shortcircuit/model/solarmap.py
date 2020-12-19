# solarmap.py

import collections
import heapq
from typing import Dict

from .evedb import EveDb


class SolarSystem:
  """
  Solar system handler
  """

  def __init__(self, key: int):
    self.id = key
    self.connected_to = {}

  # FIXME refactor neighbor info
  def add_neighbor(self, neighbor, weight: list):
    # Ignoring unspecified GATE connections between systems
    # FIXME this will ignore wormhole connections between gate-neighbors
    if neighbor in self.connected_to:
      return

    self.connected_to[neighbor] = weight

  def get_connections(self):
    return self.connected_to.keys()

  def get_id(self):
    return self.id

  # FIXME refactor neighbor info
  def get_weight(self, neighbor):
    return self.connected_to[neighbor]


class SolarMap:
  """
  Solar map handler
  """

  # FIXME refactor into enum
  GATE = 0
  WORMHOLE = 1

  def __init__(self):
    self.systems_list: Dict[int, SolarSystem] = {}
    self.total_systems: int = 0

    self.eve_db: EveDb = EveDb()
    for row in self.eve_db.gates:
      self.add_connection(row[0], row[1], SolarMap.GATE)

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
      con_type: int,
      con_info: list = None,
  ):
    if source not in self.systems_list:
      self.add_system(source)
    if destination not in self.systems_list:
      self.add_system(destination)

    if con_type == SolarMap.GATE:
      self.systems_list[source].add_neighbor(self.systems_list[destination], [SolarMap.GATE, None])
      self.systems_list[destination].add_neighbor(self.systems_list[source], [SolarMap.GATE, None])
    elif con_type == SolarMap.WORMHOLE:
      [sig_source, code_source, sig_dest, code_dest, wh_size, wh_life, wh_mass, time_elapsed] = con_info
      self.systems_list[source].add_neighbor(
        self.systems_list[destination],
        [SolarMap.WORMHOLE, [sig_source, code_source, wh_size, wh_life, wh_mass, time_elapsed]]
      )
      self.systems_list[destination].add_neighbor(
        self.systems_list[source],
        [SolarMap.WORMHOLE, [sig_dest, code_dest, wh_size, wh_life, wh_mass, time_elapsed]]
      )
    else:
      # you shouldn't be here
      # TODO raise exception
      pass

  def __contains__(self, system_id: int):
    return system_id in self.systems_list

  def __iter__(self):
    return iter(self.systems_list.values())

  # TODO properly type this
  def shortest_path(
      self,
      source: int,
      destination: int,
      avoidance_list,
      size_restriction,
      ignore_eol,
      ignore_masscrit,
      age_threshold
  ):
    path = []
    size_restriction = set(size_restriction)

    if source not in self.systems_list or destination not in self.systems_list:
      return []

    if source == destination:
      return [source]

    queue = collections.deque()
    visited = {self.get_system(x) for x in avoidance_list}
    parent = {}

    # starting point
    root = self.get_system(source)
    queue.append(root)
    visited.add(root)

    while len(queue) > 0:
      current_sys = queue.popleft()

      if current_sys.get_id() == destination:
        # Found!
        path.append(destination)
        while True:
          parent_id = parent[current_sys].get_id()
          path.append(parent_id)

          if parent_id != source:
            current_sys = parent[current_sys]
          else:
            path.reverse()
            return path
      else:
        # Keep searching
        for neighbor in [x for x in current_sys.get_connections() if x not in visited]:
          # Connection check (gate or wormhole size)
          [con_type, con_info] = current_sys.get_weight(neighbor)
          if con_type == SolarMap.GATE:
            proceed = True
          elif con_type == SolarMap.WORMHOLE:
            proceed = True
            [_, _, wh_size, wh_life, wh_mass, time_elapsed] = con_info
            if wh_size not in size_restriction:
              proceed = False
            elif ignore_eol and wh_life == 0:
              proceed = False
            elif ignore_masscrit and wh_mass == 0:
              proceed = False
            elif 0 < age_threshold < time_elapsed:
              proceed = False
          else:
            proceed = False

          if proceed:
            parent[neighbor] = current_sys
            visited.add(neighbor)
            queue.append(neighbor)

    return path

  # TODO properly type this
  def shortest_path_weighted(
      self,
      source: int,
      destination: int,
      avoidance_list,
      size_restriction,
      security_prio,
      ignore_eol,
      ignore_masscrit,
      age_threshold
  ):
    path = []
    size_restriction = set(size_restriction)

    if source not in self.systems_list or destination not in self.systems_list:
      return []

    if source == destination:
      return [source]

    priority_queue = []
    visited = {self.get_system(x) for x in avoidance_list}
    distance = {}
    parent = {}

    # starting point
    root = self.get_system(source)
    distance[root] = 0
    heapq.heappush(priority_queue, (distance[root], id(root), root))

    while len(priority_queue) > 0:
      (_, _, current_sys) = heapq.heappop(priority_queue)
      visited.add(current_sys)

      if current_sys.get_id() == destination:
        # Found!
        path.append(destination)
        while True:
          parent_id = parent[current_sys].get_id()
          path.append(parent_id)

          if parent_id != source:
            current_sys = parent[current_sys]
          else:
            path.reverse()
            return path
      else:
        # Keep searching
        for neighbor in [x for x in current_sys.get_connections() if x not in visited]:
          # Connection check (gate or wormhole size)
          [con_type, con_info] = current_sys.get_weight(neighbor)
          if con_type == SolarMap.GATE:
            proceed = True
            risk = security_prio[self.eve_db.system_type(neighbor.get_id())]
          elif con_type == SolarMap.WORMHOLE:
            proceed = True
            risk = security_prio[3]
            [_, _, wh_size, wh_life, wh_mass, time_elapsed] = con_info
            if wh_size not in size_restriction:
              proceed = False
            elif ignore_eol and wh_life == 0:
              proceed = False
            elif ignore_masscrit and wh_mass == 0:
              proceed = False
            elif 0 < age_threshold < time_elapsed:
              proceed = False
          else:
            proceed = False

          if proceed:
            if neighbor not in distance:
              distance[neighbor] = float('inf')
            if distance[neighbor] > distance[current_sys] + risk:
              distance[neighbor] = distance[current_sys] + risk
              heapq.heappush(priority_queue, (distance[neighbor], id(neighbor), neighbor))
              parent[neighbor] = current_sys

    return path
