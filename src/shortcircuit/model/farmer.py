# farmer.py

import json
from datetime import datetime, timedelta
from dateutil import parser, relativedelta
from dateutil.tz import tzutc, tzlocal
from PySide2 import QtCore
from time import sleep

from .logger import Logger
from .evedb import EveDb


# https://gist.github.com/wladston/5640961
def humanize_time(time):
  '''
  get a datetime object and return a relative time string like
  'one hour ago', 'yesterday', '3 months ago', 'just now', etc.
  '''

  rd = relativedelta.relativedelta(datetime.now(tzutc()), time)

  def line(number, unit):
    if abs(number) < 10 and unit == 'seconds':
      return 'just now'
    if number == 1 and unit == 'days':
      return 'yesterday'
    if number == -1 and unit == 'days':
      return 'tomorrow'

    prefix, suffix = '', ''
    unit = unit if abs(number) > 1 else unit[:-1]  # Unpluralizing.

    if number > 0:
      suffix = ' ago'
    else:
      prefix = 'in '

    return '%s%d %s%s' % (prefix, abs(number), unit, suffix)

  for attr in ['years', 'months', 'days', 'hours', 'minutes', 'seconds']:
    value = getattr(rd, attr)
    if value != 0:
      return line(value, attr)

  return 'just now'


class Farmer(QtCore.QObject):
  """
  Farmer handler
  """

  finished = QtCore.Signal()

  @property
  def tripwire_obj(self):
    if not self._tripwire_obj:
      self._tripwire_obj = self.navigation_obj.tripwire_obj

    if not self._tripwire_obj.chain:
      self._tripwire_obj = self.navigation_obj.tripwire_obj

    return self._tripwire_obj

  @property
  def app_obj(self):
    return self.navigation_obj.app_obj

  def __init__(self, navigation_obj, parent=None):
    super(Farmer, self).__init__(parent)

    # DI Navigation
    self.navigation_obj = navigation_obj

    # DI Tripwire
    self._tripwire_obj = navigation_obj.tripwire_obj

    # Initialization
    self.filename_world = 'world.json'
    self.filename_report = 'report.txt'
    self.eve_db = EveDb()
    self.world = {
      'data': {},
      'timestamp': datetime.now(tzutc()).strftime('%Y-%m-%d %H:%M:%SZ'),
      'count': 0
    }
    self.load_world()

  def process(self):
    self.load_world()
    self.check_process_all_chains_into_world()
    self.filter_world()
    self.generate_report()
    self.finished.emit()

  def load_world(self):
    try:
      file = open(self.filename_world, 'r')
    except IOError as e:
      if e.errno == 2:
        Logger.info('World state file is not found. Probably running this for the first time')
        return
      Logger.error(e)
      return

    world = json.load(file)
    if 'data' not in world:
      Logger.warning('World state file malformed. \'data\' field is not present')
      return
    if 'timestamp' not in world:
      Logger.warning('World state file malformed. \'timestamp\' field is not present')
      return
    if 'count' not in world:
      Logger.warning('World state file malformed. \'count\' field is not present')
      return
    self.world = world

  def save_world(self):
    with open(self.filename_world, 'w') as file:
      json.dump(self.world, file, indent=2, sort_keys=True)

  def update_world_timestamp(self):
    self.world['timestamp'] = datetime.now(tzutc()).strftime('%Y-%m-%d %H:%M:%SZ')

  def check_process_all_chains_into_world(self, data=None):
    if self.world['count'] == 0:
      self.process_all_chains_into_world(data)
      return

    if datetime.now(tzutc()) - parser.parse(self.world['timestamp']) < timedelta(hours=1):
      return

    self.process_all_chains_into_world(data)

  def process_chain_into_world(self, data=None):
    if not data:
      data = self.tripwire_obj.chain

    for sig_id, sig in data['signatures'].items():
      if sig['type'] not in ['relic', 'data']:
        continue

      if str(sig['name']).startswith('Forgotten') or str(sig['name']).startswith('Unsecured'):
        continue

      if str(sig['name']).startswith('[dirty]'):
        continue

      if 'systemID' not in sig or not sig['systemID']:
        continue

      system_id = int(sig['systemID'])

      if self.eve_db.get_class(system_id) not in ['C1', 'C2', 'C3']:
        continue

      if system_id not in self.world['data']:
        system = {
          'complexes': {
            'all': 0,
            'named': 0,
            'data': 0,
            'ghost_site': 0,
            'sleeper_cache': 0,
            'relic': 0,
            'sansha_relic': 0
          },
          'signatures': {},
          'system_id': system_id,
          'system_name': self.eve_db.id2name(system_id),
          'timestamp': (datetime.now(tzutc()) - timedelta(days=14)).strftime('%Y-%m-%d %H:%M:%SZ')
        }
        system = self.check_route_to(system)
      else:
        system = self.world['data'][system_id]

      system['complexes']['all'] += 1

      if sig['name']:
        system['complexes']['named'] += 1

      if sig['type'] == 'data':
        sig['_type'] = 'data'
        system['complexes']['data'] += 1

        if sig['name'] and 'Covert Research Facility' in sig['name']:
          sig['_type'] = 'ghost_site'
          system['complexes']['ghost_site'] += 1

        if sig['name'] and 'Sleeper Cache' in sig['name']:
          sig['_type'] = 'sleeper_cache'
          system['complexes']['sleeper_cache'] += 1

      elif sig['type'] == 'relic':
        sig['_type'] = 'relic'
        system['complexes']['relic'] += 1

        if sig['name'] and 'Sansha' in sig['name']:
          sig['_type'] = 'sansha'
          system['complexes']['sansha_relic'] += 1

      sig_time = parser.parse('{}Z'.format(sig['modifiedTime']))
      sig['_relative_time'] = humanize_time(sig_time)

      if sig_time > parser.parse(system['timestamp']):
        system['timestamp'] = '{}Z'.format(sig['modifiedTime'])
        system['timestamp_relative'] = sig['_relative_time']

      system['signatures'][sig_id] = sig

      self.world['data'][system_id] = system
      self.world['count'] += 1

    self.save_world()

  def process_all_chains_into_world(self, data=None):
    if not data:
      data = self.tripwire_obj.chain

    if not data:
      self.save_world()
      return

    parsed = {}

    for sig_id, sig in data['signatures'].items():
      if 'systemID' not in sig:
        continue

      if not sig['systemID']:
        continue

      system_id = int(sig['systemID'])

      if parsed.get(system_id, False):
        continue

      if self.eve_db.get_class(system_id) not in ['C1', 'C2', 'C3']:
        continue

      next_data = self.tripwire_obj.fetch_api_refresh(sig['systemID'])
      self.process_chain_into_world(next_data)

      parsed[system_id] = True

      sleep(0.5)

    self.update_world_timestamp()
    self.save_world()

  def check_route_to(self, system):
    [route_list, route_str] = self.navigation_obj.route(self.app_obj.route_source, system['system_name'])
    accessable = True
    route_jumps = len(route_list)
    if route_jumps == 0:
      accessable = False

    system['accessable'] = accessable
    system['route_list'] = route_list
    system['route_str'] = route_str
    system['route_jumps'] = route_jumps

    return system

  def filter_world(self):
    self.world_accessable = {}
    for system_id, system in self.world['data'].items():
      if not system['accessable']:
        continue

      self.world_accessable[system_id] = self.check_route_to(system)

  def generate_report(self):
    with open(self.filename_report, 'w') as f:
      f.write('')
    self.report_world_chunk('## Most Sansha relics', self.world_accessable_get_sansha_relics())
    self.report_world_chunk('## Most Ghost sites', self.world_accessable_get_ghost_sites())
    self.report_world_chunk('## Most Sleeper caches', self.world_accessable_get_sleeper_caches())
    self.report_world_chunk('## Most recent', self.world_accessable_get_recent())
    self.report_world_chunk('## Shortest route', self.world_accessable_get_closest())
    self.report_world_chunk('## Most named sites', self.world_accessable_get_named())

  def world_accessable_get_sansha_relics(self):
    return self.world_accessable_get_complex_type('sansha_relic')

  def world_accessable_get_ghost_sites(self):
    return self.world_accessable_get_complex_type('ghost_site')

  def world_accessable_get_sleeper_caches(self):
    return self.world_accessable_get_complex_type('sleeper_cache')

  def world_accessable_get_named(self):
    return self.world_accessable_get_complex_type('named')

  def world_accessable_get_complex_type(self, site_type):
    ret = [kv for kv in list(self.world_accessable.items()) if kv[1]['complexes'][site_type] > 0]
    ret = sorted(ret, key=lambda kv: (kv[1]['complexes'][site_type], kv[1]['timestamp']), reverse=True)
    return ret

  def world_accessable_get_closest(self):
    ret = [kv for kv in list(self.world_accessable.items()) if kv[1]['route_jumps'] > 0]
    ret = sorted(ret, key=lambda kv: (-kv[1]['route_jumps'], kv[1]['timestamp']), reverse=True)
    return ret

  def world_accessable_get_recent(self):
    ret = sorted(list(self.world_accessable.items()), key=lambda kv: kv[1]['timestamp'], reverse=True)
    return ret

  def report_world_chunk(self, title, data, count=5):
    data = self.get_world_chunk_info(title, data, count)
    print(data)
    with open(self.filename_report, 'a') as f:
      f.write(data)
      f.write('\n')

  def print_world_chunk(self, title, data, count=5):
    print(self.get_world_chunk_info(title, data, count))

  def get_world_chunk_info(self, title, data, count=5):
    ret = title
    for idx, [system_id, system] in enumerate(data):
      if idx > count:
        break
      ret = '{}\n{}'.format(ret, self.get_system_info(system))
    ret = '{}\n'.format(ret)
    return ret

  def print_system(self, system):
    print(self.get_system_info(system))

  def get_system_info(self, system):
    ret = '# {} # [A {}][N {}][D {}][G {}][R {}][S {}]'.format(
      system['system_name'],
      system['complexes']['all'],
      system['complexes']['named'],
      system['complexes']['data'],
      system['complexes']['ghost_site'],
      system['complexes']['relic'],
      system['complexes']['sansha_relic']
    )
    ret = '{}\nRoute: [J {}] {}'.format(
      ret,
      system['route_jumps'],
      system['route_str']
    )
    for [sig_id, signature] in sorted(list(system['signatures'].items()), key=lambda kv: str(kv[1]['name'])):
      ret = '{}\n -> [T {}][RT {:>13}][S {}] {} # {}'.format(
        ret,
        signature['modifiedTime'],
        signature['_relative_time'],
        signature['signatureID'],
        signature['_type'],
        signature['name']
      )
    return ret
