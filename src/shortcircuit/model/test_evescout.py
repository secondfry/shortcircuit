"""Tests for how the Eve Scout mapper sizes holes."""

from unittest import mock

from shortcircuit.model import evescout as evescout_module
from shortcircuit.model.evedb import EveDb, WormholeSize
from shortcircuit.model.evescout import EveScout
from shortcircuit.model.solarmap import ConnectionType, SolarMap


def _size(wh_type, source='Thera', dest='Jita', **extra):
  """Size of the hole as stored in a SolarMap, i.e. after any capital-ban cap."""
  eve_db = EveDb()
  source_id, dest_id = eve_db.name2id(source), eve_db.name2id(dest)
  connection = {
    'in_system_id': source_id,
    'in_signature': 'ABC-123',
    'out_system_id': dest_id,
    'out_signature': 'DEF-456',
    'wh_exits_outward': True,
    'wh_type': wh_type,
    'remaining_hours': 10,
    'updated_at': '2026-11-08T00:00:00.000Z',
  }
  connection.update(extra)
  response = mock.Mock(status_code=200)
  response.json.return_value = [connection]
  solar_map = SolarMap(eve_db)
  with mock.patch.object(evescout_module.requests, 'get', return_value=response):
    EveScout().augment_map(solar_map)
  edges = solar_map.get_system(source_id).get_edges(solar_map.get_system(dest_id))
  [(con_type, con_info)] = [e for e in edges if e[0] == ConnectionType.WORMHOLE]
  return con_info[2]


def test_unknown_code_uses_max_ship_size():
  assert _size('XXXX', max_ship_size='small') == WormholeSize.SMALL
  assert _size('XXXX', max_ship_size='medium') == WormholeSize.MEDIUM


def test_xlarge_into_thera_is_capped_at_large():
  # Capped whatever Eve Scout reports; see EveDb.cap_whsize_for_capital_bans.
  assert _size('XXXX', max_ship_size='xlarge') == WormholeSize.LARGE
  assert _size('XXXX', max_ship_size='capital') == WormholeSize.LARGE


def test_xlarge_between_capital_accessible_systems_is_kept():
  # Turnur (low-sec) to null-sec: not capped.
  assert _size('XXXX', 'Turnur', 'HED-GP', max_ship_size='xlarge') == WormholeSize.XLARGE
  assert _size('XXXX', 'Turnur', 'HED-GP', max_ship_size='capital') == WormholeSize.XLARGE


def test_unknown_max_ship_size_falls_back_to_system_pair():
  assert _size('XXXX', max_ship_size='huge') == WormholeSize.LARGE
  assert _size('XXXX') == WormholeSize.LARGE


def test_hole_code_beats_max_ship_size():
  # N110 is a Medium hole in CCP's data, whatever max_ship_size says.
  assert _size('N110', 'Turnur', 'HED-GP', max_ship_size='xlarge') == WormholeSize.MEDIUM
