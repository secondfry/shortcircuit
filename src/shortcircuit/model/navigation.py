# navigation.py

from .evedb import EveDb
from .evescout import EveScout
from .solarmap import SolarMap
from .tripwire import Tripwire


class Navigation:
  """
  Navigation
  """
  def __init__(self, app_obj: 'MainWindow'):
    self.app_obj = app_obj
    self.eve_db = EveDb()
    self.solar_map = SolarMap()
    self.tripwire_obj = None

    self.tripwire_url = self.app_obj.tripwire_url
    self.tripwire_user = self.app_obj.tripwire_user
    self.tripwire_password = self.app_obj.tripwire_pass

  def reset_chain(self):
    self.solar_map = SolarMap()
    return self.solar_map

  def tripwire_set_login(self, url: str = None, user: str = None, password: str = None):
    if not url:
      url = self.app_obj.tripwire_url
    self.tripwire_url = url

    if not user:
      user = self.app_obj.tripwire_user
    self.tripwire_user = user

    if not password:
      password = self.app_obj.tripwire_pass
    self.tripwire_password = password

  # TODO move this augment_map somewhere
  def evescout_augment(self, solar_map: SolarMap):
    evescout = EveScout()
    return evescout.augment_map(solar_map)

  def tripwire_augment(self, solar_map: SolarMap):
    self.tripwire_obj = Tripwire(self.tripwire_user, self.tripwire_password, self.tripwire_url)
    connections = self.tripwire_obj.augment_map(solar_map)
    return connections

  # FIXME refactor neighbor info - weights
  @staticmethod
  def _get_instructions(weight):
    if not weight:
      return "Destination reached"

    if weight[0] == SolarMap.GATE:
      return "Jump gate"

    if weight[0] == SolarMap.WORMHOLE:
      [wh_sig, wh_code, _, _, _, _] = weight[1]
      return "Jump wormhole\n{} [{}]".format(wh_sig, wh_code)

    return "Instructions unclear, initiate self-destruct"

  # FIXME refactor neighbor info - weights
  @staticmethod
  def _get_additional_info(weight, weight_back):
    if not weight or not weight_back:
      return

    if weight_back[0] != SolarMap.WORMHOLE:
      return

    [wh_sig, wh_code, wh_size, wh_life, wh_mass, time_elapsed] = weight_back[1]
    # Wormhole size
    if wh_size == 0:
      wh_size_text = "Small"
    elif wh_size == 1:
      wh_size_text = "Medium"
    elif wh_size == 2:
      wh_size_text = "Large"
    elif wh_size == 3:
      wh_size_text = "X-large"
    else:
      wh_size_text = "Unknown"

    # Wormhole life
    if wh_life == 1:
      wh_life_text = "Stable"
    else:
      wh_life_text = "Critical"

    # Wormhole mass
    if wh_mass == 2:
      wh_mass_text = "Stable"
    elif wh_mass == 1:
      wh_mass_text = "Destab"
    else:
      wh_mass_text = "Critical"

    # Return signature
    return "Return sig: {0} [{1}], Updated: {5}h ago\nSize: {2}, Life: {3}, Mass: {4}".format(
      wh_sig,
      wh_code,
      wh_size_text,
      wh_life_text,
      wh_mass_text,
      time_elapsed
    )

  def route(
      self,
      source: str,
      destination: str
  ):
    [size_restriction, ignore_eol, ignore_masscrit, age_threshold, security_prio, avoidance_list] = self.app_obj.get_restrictions()

    source_id = self.eve_db.name2id(source)
    dest_id = self.eve_db.name2id(destination)
    avoidance_list_ids = [self.eve_db.name2id(x) for x in avoidance_list]

    if security_prio:
      path = self.solar_map.shortest_path_weighted(
        source_id,
        dest_id,
        avoidance_list_ids,
        size_restriction,
        security_prio,
        ignore_eol,
        ignore_masscrit,
        age_threshold
      )
    else:
      path = self.solar_map.shortest_path(
        source_id,
        dest_id,
        avoidance_list_ids,
        size_restriction,
        ignore_eol,
        ignore_masscrit,
        age_threshold
      )

    # Construct route
    route = []
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
      route_step['path_info'] = Navigation._get_additional_info(weight, weight_back)
      route_step['path_data'] = weight
      route.append(route_step)

    # Construct short format
    short_format = list()
    flag_gate = 0
    for rsid, route_step in enumerate(route):
      # We are adding systems in backwards manner, so skip first one
      if rsid == 0:
        continue

      prev_route_step = route[rsid - 1]

      # We jumped to this system via wormhole
      if prev_route_step['path_data'][0] == SolarMap.WORMHOLE:
        # ...in case of multiple previous gate jumps, indicate that
        if flag_gate > 1:
          short_format.extend(['...', '-->'])

        # Add previous system to route
        short_format.extend([
          '{} [{}]'.format(
            prev_route_step['name'],
            prev_route_step['path_data'][1][0]  # FIXME my eyes are bleeding, this gets signature from weight param
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
      short_format.extend([
        prev_route_step['name'],
        '-->'
      ])
      flag_gate += 1

    # Add last system
    # ...in case of multiple previous gate jumps, indicate that
    if flag_gate > 1:
      short_format.extend(['...', '-->'])
    short_format.append(route[-1]['name'])

    short_format = 'Short Circuit: `{}`'.format(' '.join(short_format))

    return [route, short_format]
