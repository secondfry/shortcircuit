# navigation.py

from typing import TYPE_CHECKING, Dict, List

from .evedb import EveDb, SystemDescription, WormholeMassspan, WormholeSize, WormholeTimespan
from .evescout import EveScout
from .mapper_registry import MapperRegistry
from .solarmap import ConnectionType, SolarMap
from .tripwire import Tripwire

if TYPE_CHECKING:
  from shortcircuit.app import MainWindow


class Navigation:
  """
  Navigation - handles pathfinding and wormhole mapper integration.
  
  This class manages the solar map and integrates with multiple wormhole
  mapping sources (Tripwire, Eve Scout, etc.) through the MapperRegistry.
  """

  def __init__(self, app_obj: 'MainWindow', eve_db: EveDb):
    self.app_obj = app_obj
    self.eve_db = eve_db

    self.solar_map = SolarMap(self.eve_db)
    self.mapper_registry = MapperRegistry()

    self.tripwire_url = self.app_obj.tripwire_url
    self.tripwire_user = self.app_obj.tripwire_user
    self.tripwire_password = self.app_obj.tripwire_pass

  def reset_chain(self):
    """Reset the solar map to its initial state."""
    self.solar_map = SolarMap(self.eve_db)
    return self.solar_map

  def tripwire_set_login(
    self,
    url: str = None,
    user: str = None,
    password: str = None,
  ):
    """Update Tripwire login credentials."""
    if not url:
      url = self.app_obj.tripwire_url
    self.tripwire_url = url

    if not user:
      user = self.app_obj.tripwire_user
    self.tripwire_user = user

    if not password:
      password = self.app_obj.tripwire_pass
    self.tripwire_password = password

  def setup_mappers(self):
    """
    Configure mapper sources in the registry based on current settings.
    
    This method reads configuration from the app and sets up all enabled
    mapper sources (Tripwire, Eve Scout, etc.) in the registry.
    """
    # Clear existing mappers
    self.mapper_registry.clear()
    
    # Add Tripwire if configured
    if self.tripwire_url and self.tripwire_user and self.tripwire_password:
      tripwire = Tripwire(
        self.tripwire_user,
        self.tripwire_password,
        self.tripwire_url,
        name="Tripwire"
      )
      self.mapper_registry.register(tripwire)
    
    # Add Eve Scout if enabled
    evescout_enabled = self.app_obj.state_evescout.get("enabled", False)
    if evescout_enabled:
      evescout = EveScout(name="Eve Scout")
      self.mapper_registry.register(evescout)

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
      [wh_sig, wh_code, _, _, _, _] = weight[1]
      return "Jump wormhole\n{} [{}]".format(wh_sig, wh_code)

    return "Instructions unclear, initiate self-destruct"

  # FIXME refactor neighbor info - weights
  @staticmethod
  def _get_additional_info(weight, weight_back):
    if not weight or not weight_back:
      return

    if weight_back[0] != ConnectionType.WORMHOLE:
      return

    [wh_sig, wh_code, wh_size, wh_life, wh_mass, time_elapsed] = weight_back[1]
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
    return "Return sig: {0} [{1}], Updated: {5}h ago\nSize: {2}, Life: {3}, Mass: {4}".format(
      wh_sig, wh_code, wh_size_text, wh_life_text, wh_mass_text, time_elapsed
    )

  def route(self, source: int, destination: int):
    path = self.solar_map.shortest_path(
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
        source = self.solar_map.get_system(x)
        dest = self.solar_map.get_system(path[idx + 1])
        weight = source.get_weight(dest)
        weight_back = dest.get_weight(source)

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


# TODO move this augment_map somewhere
def evescout_augment(solar_map: SolarMap):
  evescout = EveScout()
  return evescout.augment_map(solar_map)
