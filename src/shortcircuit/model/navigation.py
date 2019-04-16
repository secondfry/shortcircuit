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
    if weight:
      if weight[0] == SolarMap.GATE:
        instructions = "Jump gate"
      elif weight[0] == SolarMap.WORMHOLE:
        [wh_sig, wh_code, _, _, _, _] = weight[1]
        instructions = "Jump wormhole {}[{}]".format(wh_sig, wh_code)
      else:
        instructions = "Instructions unclear, initiate self-destruct"
    else:
      instructions = "Destination reached"

    return instructions

  # FIXME refactor neighbor info - weights
  @staticmethod
  def _get_additional_info(weight, weight_back):
    info = ""
    if weight and weight_back:
      if weight_back[0] == SolarMap.WORMHOLE:
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
        info = "Return sig: {}[{}], Size: {}, Life: {}, Mass: {}, Updated: {}h ago".format(
          wh_sig,
          wh_code,
          wh_size_text,
          wh_life_text,
          wh_mass_text,
          time_elapsed
        )

    return info

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

    route = []
    short_format = ""
    prev_gate = None  # Previous gate - will be the system ID of the previous system if connection was a gate

    for idx, x in enumerate(path):
      # Construct route
      if idx < len(path) - 1:
        source = self.solar_map.get_system(x)
        dest = self.solar_map.get_system(path[idx + 1])
        weight = source.get_weight(dest)
        weight_back = dest.get_weight(source)
      else:
        weight = None
        weight_back = None
      system_description = list(self.eve_db.system_desc[x])
      system_description.append(Navigation._get_instructions(weight))
      system_description.append(Navigation._get_additional_info(weight, weight_back))
      route.append(system_description)

      # Build short format message (travelling between multiple consecutive gates will be denoted as '...')
      if not weight:
        # destination reached
        if prev_gate:
          if prev_gate != path[idx - 1]:
            short_format += "...-->"
        short_format += system_description[0]
      else:
        # keep looking
        if weight[0] == SolarMap.WORMHOLE:
          if prev_gate:
            if prev_gate != path[idx - 1]:
              short_format += "...-->"
          [wh_sig, _, _, _, _, _] = weight[1]
          short_format += system_description[0] + "[{}]~~>".format(wh_sig)
          prev_gate = None
        elif weight[0] == SolarMap.GATE:
          if not prev_gate:
            short_format += system_description[0] + "-->"
            prev_gate = path[idx]
        else:
          # Not supposed to be here
          short_format += "Where am I?-->"

    return [route, short_format]
