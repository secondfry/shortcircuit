"""Tests for how the Eve Scout mapper sizes holes."""

from unittest import mock

from shortcircuit.model import evescout as evescout_module
from shortcircuit.model.evedb import EveDb, WormholeSize
from shortcircuit.model.evescout import EveScout

THERA_ID = 31000005


def _size(wh_type, **extra):
  eve_db = EveDb()
  connection = {
    'in_system_id': THERA_ID,
    'in_signature': 'ABC-123',
    'out_system_id': eve_db.name2id('Jita'),
    'out_signature': 'DEF-456',
    'wh_exits_outward': True,
    'wh_type': wh_type,
    'remaining_hours': 10,
    'updated_at': '2026-11-08T00:00:00.000Z',
  }
  connection.update(extra)
  response = mock.Mock(status_code=200)
  response.json.return_value = [connection]
  solar_map = mock.Mock()
  with mock.patch.object(evescout_module.requests, 'get', return_value=response):
    EveScout().augment_map(solar_map)
  return solar_map.add_connection.call_args.args[3][4]


def test_unknown_code_uses_max_ship_size():
  # Thera<->high-sec falls back to Large, so these come from max_ship_size.
  assert _size('XXXX', max_ship_size='medium') == WormholeSize.MEDIUM
  assert _size('XXXX', max_ship_size='xlarge') == WormholeSize.XLARGE
  assert _size('XXXX', max_ship_size='capital') == WormholeSize.XLARGE


def test_unknown_max_ship_size_falls_back_to_system_pair():
  assert _size('XXXX', max_ship_size='huge') == WormholeSize.LARGE
  assert _size('XXXX') == WormholeSize.LARGE


def test_hole_code_beats_max_ship_size():
  # B520 is Large (capital-ban shortcut) though Eve Scout says xlarge.
  assert _size('B520', max_ship_size='xlarge') == WormholeSize.LARGE
