# solarmap.py

import heapq
from enum import Enum
from typing import Dict, List, Optional, Tuple

from shortcircuit.model.logger import Logger
from typing_extensions import Self

from .evedb import (
  EveDb,
  Restrictions,
  SpaceType,
  WormholeSize,
  WormholeMassspan,
  WormholeTimespan,
)


class ConnectionType(int, Enum):
  GATE = 1
  WORMHOLE = 2


Edge = Tuple[ConnectionType, Optional[List]]

_SIG_PLACEHOLDERS = frozenset(['', '-------', '???', '----'])


def _is_placeholder_sig(s) -> bool:
  if s is None:
    return True
  return s in _SIG_PLACEHOLDERS


class SolarSystem:
  """
  Solar system handler.

  connected_to stores a list of *parallel edges* per neighbor. Gates are
  always a single edge per pair; wormholes can have multiple parallel edges
  when the same system pair is joined by two distinct wormholes
  simultaneously (rare in EVE but physically possible).

  Invariant: for any two systems A and B joined by wormhole(s),
  `len(A.connected_to[B]) == len(B.connected_to[A])` and index i in one list
  corresponds to the same physical wormhole as index i in the other. This is
  maintained by SolarMap.add_connection, which is the only code that mutates
  connected_to after __init__.
  """

  def __init__(self, key: int):
    self.id = key
    self.connected_to: Dict['SolarSystem', List[Edge]] = {}

  def add_gate_edge(self, neighbor: Self):
    """Idempotently add a gate edge to `neighbor`."""
    edges = self.connected_to.setdefault(neighbor, [])
    for con_type, _ in edges:
      if con_type == ConnectionType.GATE:
        return
    edges.append((ConnectionType.GATE, None))

  def add_parallel_edge(self, neighbor: Self, edge: Edge):
    """Unconditionally append `edge` to this neighbor's parallel-edge list."""
    self.connected_to.setdefault(neighbor, []).append(edge)

  def replace_edge_at(self, neighbor: Self, index: int, edge: Edge):
    self.connected_to[neighbor][index] = edge

  def get_edges(self, neighbor: Self) -> List[Edge]:
    return self.connected_to.get(neighbor, [])

  def get_connections(self):
    return self.connected_to.keys()

  def get_id(self) -> int:
    return self.id


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
    source_name: str = None,
  ):
    if source not in self.systems_list:
      self.add_system(source)
    if destination not in self.systems_list:
      self.add_system(destination)

    src_sys = self.systems_list[source]
    dst_sys = self.systems_list[destination]

    if con_type == ConnectionType.GATE:
      src_sys.add_gate_edge(dst_sys)
      dst_sys.add_gate_edge(src_sys)
      return

    if con_type == ConnectionType.WORMHOLE:
      self._add_wormhole(src_sys, dst_sys, con_info, source_name)
      return

    Logger.error("Unknown connection type provided")

  def _add_wormhole(
    self,
    src_sys: SolarSystem,
    dst_sys: SolarSystem,
    con_info: List,
    source_name: Optional[str],
  ):
    [
      sig_source,
      code_source,
      sig_dest,
      code_dest,
      wh_size,
      wh_life,
      wh_mass,
      time_elapsed,
    ] = con_info
    new_sources = [source_name] if source_name else []

    match_idx = self._find_matching_wormhole(
      src_sys, dst_sys, sig_source, sig_dest
    )

    if match_idx is None:
      src_sys.add_parallel_edge(
        dst_sys,
        (ConnectionType.WORMHOLE,
         [sig_source, code_source, wh_size, wh_life, wh_mass, time_elapsed, list(new_sources)]),
      )
      dst_sys.add_parallel_edge(
        src_sys,
        (ConnectionType.WORMHOLE,
         [sig_dest, code_dest, wh_size, wh_life, wh_mass, time_elapsed, list(new_sources)]),
      )
      return

    self._merge_wormhole_at(
      src_sys, dst_sys, match_idx,
      sig_source, code_source, sig_dest, code_dest,
      wh_size, wh_life, wh_mass, time_elapsed, new_sources,
    )

  def _find_matching_wormhole(
    self,
    src_sys: SolarSystem,
    dst_sys: SolarSystem,
    new_sig_source: str,
    new_sig_dest: str,
  ) -> Optional[int]:
    """
    Find the index of a parallel wormhole edge whose sig pair matches the
    incoming report, or None. Prefers an exact two-sided match over a
    one-sided-concrete match; falls back to placeholder-only compatibility
    when there are no contradictions at all.

    Returns the earliest-indexed match in the preferred tier.
    """
    src_edges = src_sys.get_edges(dst_sys)
    dst_edges = dst_sys.get_edges(src_sys)
    # Only check the range where both directions have entries, which
    # respects the lockstep invariant even if somehow it's been broken.
    upper = min(len(src_edges), len(dst_edges))

    exact_idx: Optional[int] = None
    one_sided_idx: Optional[int] = None
    placeholder_idx: Optional[int] = None

    for i in range(upper):
      if src_edges[i][0] != ConnectionType.WORMHOLE:
        continue
      if dst_edges[i][0] != ConnectionType.WORMHOLE:
        continue
      existing_sig_source = src_edges[i][1][0]
      existing_sig_dest = dst_edges[i][1][0]

      tier = self._classify_sig_pair(
        new_sig_source, new_sig_dest,
        existing_sig_source, existing_sig_dest,
      )
      if tier == 'exact' and exact_idx is None:
        exact_idx = i
      elif tier == 'one_sided' and one_sided_idx is None:
        one_sided_idx = i
      elif tier == 'placeholder' and placeholder_idx is None:
        placeholder_idx = i

    if exact_idx is not None:
      return exact_idx
    if one_sided_idx is not None:
      return one_sided_idx
    return placeholder_idx

  @staticmethod
  def _classify_sig_pair(
    new_source: str, new_dest: str,
    existing_source: str, existing_dest: str,
  ) -> str:
    """
    Classify whether a new sig pair refers to the same wormhole as an
    existing one. A sig ID uniquely identifies a wormhole endpoint within
    one system, so a concrete match on *either* side means "same wormhole".

    Returns one of: 'exact', 'one_sided', 'placeholder', 'incompat'.
    """
    source_match, source_mismatch = SolarMap._compare_sig_slot(new_source, existing_source)
    dest_match, dest_mismatch = SolarMap._compare_sig_slot(new_dest, existing_dest)

    if source_match and dest_match:
      return 'exact'
    if source_match or dest_match:
      return 'one_sided'
    if source_mismatch or dest_mismatch:
      return 'incompat'
    return 'placeholder'

  @staticmethod
  def _compare_sig_slot(new: str, existing: str) -> Tuple[bool, bool]:
    """Return (concrete_match, concrete_mismatch) for one side's sig slot."""
    if _is_placeholder_sig(new) or _is_placeholder_sig(existing):
      return False, False
    return new == existing, new != existing

  def _merge_wormhole_at(
    self,
    src_sys: SolarSystem,
    dst_sys: SolarSystem,
    idx: int,
    new_sig_source: str,
    new_code_source: str,
    new_sig_dest: str,
    new_code_dest: str,
    new_size,
    new_life,
    new_mass,
    new_time: float,
    new_sources: List[str],
  ):
    """
    Merge a new report into parallel-edge slot `idx` in both directions.
    Sources are unioned. Placeholder sig/code slots are upgraded to concrete
    values from the new report. The fresher report (smaller time_elapsed)
    wins for size/life/mass. If the two reports' concrete sig pairs match
    exactly on one side but disagree on the other, log a warning — that's a
    scan-disagreement case, not a parallel-wormhole case.
    """
    # Capture pre-merge sigs so we can detect scan disagreement even when
    # the fresher report is about to overwrite the disagreeing slot.
    pre_src_sig = src_sys.get_edges(dst_sys)[idx][1][0]
    pre_dst_sig = dst_sys.get_edges(src_sys)[idx][1][0]

    self._merge_one_direction(
      src_sys, dst_sys, idx,
      new_sig_source, new_code_source,
      new_size, new_life, new_mass, new_time, new_sources,
    )
    self._merge_one_direction(
      dst_sys, src_sys, idx,
      new_sig_dest, new_code_dest,
      new_size, new_life, new_mass, new_time, new_sources,
    )

    if self._has_scan_disagreement(
      new_sig_source, new_sig_dest, pre_src_sig, pre_dst_sig,
    ):
      Logger.warning(
        f"Wormhole between {src_sys.get_id()} and {dst_sys.get_id()} has "
        f"disagreeing sigs across reports on one side "
        f"(stored {pre_src_sig!r}/{pre_dst_sig!r} vs incoming "
        f"{new_sig_source!r}/{new_sig_dest!r}); kept fresher"
      )

  @staticmethod
  def _has_scan_disagreement(
    new_source: str, new_dest: str,
    stored_source: str, stored_dest: str,
  ) -> bool:
    source_ok = _is_placeholder_sig(new_source) or _is_placeholder_sig(stored_source) or new_source == stored_source
    dest_ok = _is_placeholder_sig(new_dest) or _is_placeholder_sig(stored_dest) or new_dest == stored_dest
    return not (source_ok and dest_ok)

  @staticmethod
  def _merge_one_direction(
    system: SolarSystem,
    neighbor: SolarSystem,
    idx: int,
    new_sig: str,
    new_code: str,
    new_size,
    new_life,
    new_mass,
    new_time: float,
    new_sources: List[str],
  ):
    _, existing = system.get_edges(neighbor)[idx]
    # existing payload: [sig, code, size, life, mass, time, sources]
    existing_sig, existing_code = existing[0], existing[1]
    existing_size, existing_life, existing_mass = existing[2], existing[3], existing[4]
    existing_time = existing[5]
    existing_sources = existing[6]

    # Sources: union (preserve order: existing first, then new entries)
    merged_sources = list(existing_sources)
    for name in new_sources:
      if name and name not in merged_sources:
        merged_sources.append(name)

    # Sig/code: concrete value wins over placeholder; otherwise fresher.
    if _is_placeholder_sig(existing_sig) and not _is_placeholder_sig(new_sig):
      merged_sig = new_sig
    elif _is_placeholder_sig(new_sig):
      merged_sig = existing_sig
    else:
      merged_sig = new_sig if new_time < existing_time else existing_sig

    if not existing_code:
      merged_code = new_code
    elif not new_code:
      merged_code = existing_code
    else:
      merged_code = new_code if new_time < existing_time else existing_code

    # Size/life/mass/time: fresher wins wholesale
    if new_time < existing_time:
      merged_size, merged_life, merged_mass, merged_time = new_size, new_life, new_mass, new_time
    else:
      merged_size, merged_life, merged_mass, merged_time = existing_size, existing_life, existing_mass, existing_time

    system.replace_edge_at(
      neighbor, idx,
      (ConnectionType.WORMHOLE,
       [merged_sig, merged_code, merged_size, merged_life, merged_mass, merged_time, merged_sources]),
    )

  def __contains__(self, system_id: int):
    return system_id in self.systems_list

  def __iter__(self):
    return iter(self.systems_list.values())

  def _check_edge(
    self,
    neighbor: SolarSystem,
    edge: Edge,
    restrictions: Restrictions,
  ) -> Tuple[bool, float]:
    con_type, con_info = edge

    if con_type == ConnectionType.GATE:
      system_type = self.eve_db.system_type(neighbor.get_id())
      return True, restrictions["security_prio"][system_type]

    if con_type != ConnectionType.WORMHOLE:
      return False, 0

    wh_size = con_info[2]
    wh_life = con_info[3]
    wh_mass = con_info[4]
    time_elapsed = con_info[5]

    if restrictions["size_restriction"].get(wh_size, False):
      return False, 0

    if restrictions["ignore_eol"] and wh_life == WormholeTimespan.CRITICAL:
      return False, 0

    if restrictions["ignore_masscrit"] and wh_mass == WormholeMassspan.CRITICAL:
      return False, 0

    if time_elapsed > restrictions["age_threshold"]:
      return False, 0

    return True, restrictions["security_prio"][SpaceType.WH]

  def _pick_best_edge(
    self,
    current_sys: SolarSystem,
    neighbor: SolarSystem,
    restrictions: Restrictions,
  ) -> Optional[Tuple[float, int]]:
    """Return (risk, edge_index) for the cheapest traversable parallel edge, or None."""
    best: Optional[Tuple[float, int]] = None
    for i, edge in enumerate(current_sys.get_edges(neighbor)):
      proceed, risk = self._check_edge(neighbor, edge, restrictions)
      if not proceed:
        continue
      if best is None or risk < best[0]:
        best = (risk, i)
    return best

  # TODO properly type this
  def shortest_path(
    self,
    source: int,
    destination: int,
    restrictions: Restrictions,
  ) -> Tuple[List[int], List[Tuple[Edge, Edge]]]:
    """
    Dijkstra over the parallel-edge graph.

    Returns a tuple ``(path_ids, path_edges)``:
      - ``path_ids`` is the list of system IDs from source to destination.
      - ``path_edges`` has length ``len(path_ids) - 1``; each element is the
        pair ``(edge_forward, edge_backward)`` for the hop from
        ``path_ids[i]`` to ``path_ids[i+1]``.
    Both are empty on no-path.
    """
    if source not in self.systems_list or destination not in self.systems_list:
      return [], []

    if source == destination:
      return [source], []

    avoidance_list = restrictions["avoidance_list"]
    try:
      avoidance_list.remove(source)
    except ValueError:
      pass
    try:
      avoidance_list.remove(destination)
    except ValueError:
      pass

    # Capsuleers will only be able to leave Zarzakh via the gate through which
    # they arrived until the 6-hour timer runs out.
    # See: https://www.eveonline.com/news/view/zarzakh-is-under-siege
    # However, players can always exit Zarzakh via the Deathless Shipcaster,
    # Clone Jumping, or being pod killed, regardless of the lock.
    # See: https://wiki.eveuniversity.org/Zarzakh
    if self.eve_db.ZARZAKH_SYSTEM_ID not in [source, destination]:
      avoidance_list = avoidance_list + [self.eve_db.ZARZAKH_SYSTEM_ID]

    priority_queue: List[Tuple[float, int, SolarSystem]] = []
    visited = {self.get_system(x) for x in avoidance_list}
    distance: Dict[SolarSystem, float] = {}
    parent: Dict[SolarSystem, Tuple[SolarSystem, Edge, Edge]] = {}

    root = self.get_system(source)
    distance[root] = 0
    heapq.heappush(priority_queue, (distance[root], id(root), root))

    while priority_queue:
      (_, _, current_sys) = heapq.heappop(priority_queue)
      visited.add(current_sys)

      if current_sys.get_id() == destination:
        path_ids: List[int] = [destination]
        path_edges: List[Tuple[Edge, Edge]] = []
        cs = current_sys
        while cs.get_id() != source:
          prev_sys, edge_fwd, edge_back = parent[cs]
          path_ids.append(prev_sys.get_id())
          path_edges.append((edge_fwd, edge_back))
          cs = prev_sys
        path_ids.reverse()
        path_edges.reverse()
        return path_ids, path_edges

      for neighbor in [x for x in current_sys.get_connections()
                       if x not in visited]:
        pick = self._pick_best_edge(current_sys, neighbor, restrictions)
        if pick is None:
          continue
        risk, idx = pick
        edge_fwd = current_sys.get_edges(neighbor)[idx]
        edge_back = neighbor.get_edges(current_sys)[idx]

        if neighbor not in distance:
          distance[neighbor] = float('inf')

        if distance[neighbor] > distance[current_sys] + risk:
          distance[neighbor] = distance[current_sys] + risk
          heapq.heappush(
            priority_queue, (distance[neighbor], id(neighbor), neighbor)
          )
          parent[neighbor] = (current_sys, edge_fwd, edge_back)

    return [], []


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
  path, _ = map.shortest_path(
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
