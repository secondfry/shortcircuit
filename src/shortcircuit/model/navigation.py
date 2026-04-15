# navigation.py

from typing import TYPE_CHECKING, Callable, Dict, List

from .evedb import EveDb, SystemDescription, WormholeMassspan, WormholeSize, WormholeTimespan
from .evescout import EveScout
from .mapper_base import MapperSource
from .mapper_config import TYPE_EVESCOUT, TYPE_TRIPWIRE, MapperConfig
from .mapper_registry import MapperRegistry
from .solarmap import ConnectionType, SolarMap
from .tripwire import Tripwire

if TYPE_CHECKING:
  from shortcircuit.app import MainWindow


def _build_tripwire(cfg: MapperConfig) -> MapperSource:
  return Tripwire(
    username=cfg.user,
    password=cfg.password,
    url=cfg.url,
    name=cfg.name,
  )


def _build_evescout(cfg: MapperConfig) -> MapperSource:
  # Eve Scout takes an optional URL override; fall back to the client default.
  if cfg.url:
    return EveScout(url=cfg.url, name=cfg.name)
  return EveScout(name=cfg.name)


MAPPER_BUILDERS: Dict[str, Callable[[MapperConfig], MapperSource]] = {
  TYPE_TRIPWIRE: _build_tripwire,
  TYPE_EVESCOUT: _build_evescout,
}


class Navigation:
  """
  Navigation - handles pathfinding and wormhole mapper integration.

  Owns the SolarMap and a MapperRegistry. setup_mappers() rebuilds the
  registry from the current list of MapperConfig entries exposed by the
  host app, so multi-instance / mixed-type setups come for free.
  """

  def __init__(self, app_obj: 'MainWindow', eve_db: EveDb):
    self.app_obj = app_obj
    self.eve_db = eve_db

    self.solar_map = SolarMap(self.eve_db)
    self.mapper_registry = MapperRegistry()

  def reset_chain(self):
    """Reset the solar map to its initial state."""
    self.solar_map = SolarMap(self.eve_db)
    return self.solar_map

  def setup_mappers(self):
    """
    Rebuild the registry from app_obj.mapper_configs.

    Disabled configs and unknown types are skipped (unknown types are
    logged but non-fatal, so a settings file from a newer version won't
    crash an older binary). Instantiation errors on one config don't
    prevent the rest from being registered.
    """
    from .logger import Logger

    self.mapper_registry.clear()

    configs: List[MapperConfig] = getattr(self.app_obj, 'mapper_configs', []) or []
    for cfg in configs:
      if not cfg.enabled:
        continue
      builder = MAPPER_BUILDERS.get(cfg.type)
      if builder is None:
        Logger.warning(f"Unknown mapper type '{cfg.type}' for '{cfg.name}', skipping")
        continue
      try:
        source = builder(cfg)
      except Exception as e:
        Logger.error(f"Failed to build mapper '{cfg.name}' (type={cfg.type}): {e}")
        continue
      self.mapper_registry.register(source)

  def augment_map(self, solar_map: SolarMap) -> Dict[str, int]:
    """
    Augment the solar map from all registered mapper sources.
    
    Args:
      solar_map: The solar map to augment
      
    Returns:
      Dictionary mapping source names to connection counts
    """
    return self.mapper_registry.augment_map(solar_map)

  # FIXME refactor neighbor info - weights
  @staticmethod
  def _get_instructions(weight):
    if not weight:
      return "Destination reached"

    if weight[0] == ConnectionType.GATE:
      return "Jump gate"

    if weight[0] == ConnectionType.WORMHOLE:
      wh_sig, wh_code = weight[1][0], weight[1][1]
      return "Jump wormhole\n{} [{}]".format(wh_sig, wh_code)

    return "Instructions unclear, initiate self-destruct"

  # FIXME refactor neighbor info - weights
  @staticmethod
  def _get_additional_info(weight, weight_back):
    if not weight or not weight_back:
      return

    if weight_back[0] != ConnectionType.WORMHOLE:
      return

    info = weight_back[1]
    wh_sig, wh_code = info[0], info[1]
    wh_size, wh_life, wh_mass, time_elapsed = info[2], info[3], info[4], info[5]
    sources = info[6] if len(info) >= 7 else []
    # Wormhole size
    wh_size_text = "Unknown"
    if wh_size == WormholeSize.SMALL:
      wh_size_text = "Small"
    if wh_size == WormholeSize.MEDIUM:
      wh_size_text = "Medium"
    if wh_size == WormholeSize.LARGE:
      wh_size_text = "Large"
    elif wh_size == WormholeSize.XLARGE:
      wh_size_text = "X-large"

    # Wormhole life
    wh_life_text = "Timespan unknown"
    if wh_life == WormholeTimespan.STABLE:
      wh_life_text = "Stable"
    if wh_life == WormholeTimespan.CRITICAL:
      wh_life_text = "Critical"

    # Wormhole mass
    wh_mass_text = "Massspan unknown"
    if wh_mass == WormholeMassspan.STABLE:
      wh_mass_text = "Stable"
    if wh_mass == WormholeMassspan.DESTAB:
      wh_mass_text = "Destab"
    if wh_mass == WormholeMassspan.CRITICAL:
      wh_mass_text = "Critical"

    # Return signature
    base = "Return sig: {0} [{1}], Updated: {5}h ago\nSize: {2}, Life: {3}, Mass: {4}".format(
      wh_sig, wh_code, wh_size_text, wh_life_text, wh_mass_text, time_elapsed
    )
    if sources:
      base += "\nReported by: {}".format(", ".join(sources))
    return base

  def route(self, source: int, destination: int):
    path, path_edges = self.solar_map.shortest_path(
      source,
      destination,
      self.app_obj.get_restrictions(),
    )

    # Construct route
    route: List[SystemDescription] = []
    for idx, x in enumerate(path):
      if idx == len(path) - 1:
        weight = None
        weight_back = None
      else:
        weight, weight_back = path_edges[idx]

      route_step = self.eve_db.system_desc[x]
      route_step['path_action'] = Navigation._get_instructions(weight)
      route_step['path_info'] = Navigation._get_additional_info(
        weight,
        weight_back,
      )
      route_step['path_data'] = weight
      route.append(route_step)

    if not route:
      return (route, 'Path is not found')

    # Construct short format
    short_format = list()
    flag_gate = 0
    for rsid, route_step in enumerate(route):
      # We are adding systems in backwards manner, so skip first one
      if rsid == 0:
        continue

      prev_route_step = route[rsid - 1]

      # We jumped to this system via wormhole
      if prev_route_step['path_data'][0] == ConnectionType.WORMHOLE:
        # ...in case of multiple previous gate jumps, indicate that
        if flag_gate > 1:
          short_format.extend(['...', '-->'])

        # Add previous system to route
        short_format.extend([
          '{} [{}]'.format(
            prev_route_step['name'],
            # FIXME my eyes are bleeding, this gets signature from weight param
            prev_route_step['path_data'][1][0],
          ),
          '~~>'
        ])
        flag_gate = 0
        continue

      # We are skipping multiple gate jumps
      if flag_gate:
        flag_gate += 1
        continue

      # Add previous system to route
      short_format.extend([prev_route_step['name'], '-->'])
      flag_gate += 1

    # Add last system
    # ...in case of multiple previous gate jumps, indicate that
    if flag_gate > 1:
      short_format.extend(['...', '-->'])
    short_format.append(route[-1]['name'])

    short_format = 'Short Circuit: `{}`'.format(' '.join(short_format))

    return (route, short_format)
