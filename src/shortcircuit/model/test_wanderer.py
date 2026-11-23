"""Tests for the Wanderer mapper integration

Covers config validation, URL normalization, building holes from the
connections endpoint (life, mass and size codes as Wanderer defines them in
assets/js/hooks/Mapper/types/connection.ts), joining signatures for sig IDs
and hole types, and the failure modes of the API round trips.
"""

import unittest
from unittest import mock

import requests

from shortcircuit.model import wanderer as wanderer_module
from shortcircuit.model.evedb import WormholeMassspan, WormholeSize, WormholeTimespan
from shortcircuit.model.solarmap import ConnectionType
from shortcircuit.model.wanderer import Wanderer

THERA_ID = 31000005
J_SYSTEM_ID = 31002238
BASE = 'https://wanderer.example.com/api/maps/my-map'


def _make_wanderer(**kwargs):
  defaults = dict(
    url='https://wanderer.example.com',
    map_slug='my-map',
    token='secret-token',
    name='Test Wanderer',
  )
  defaults.update(kwargs)
  w = Wanderer(**defaults)
  # Size lookups go through the SDE; tests pin them so they don't depend
  # on database contents.
  w.eve_db = mock.Mock()
  w.eve_db.get_whsize_by_code.return_value = WormholeSize.UNKNOWN
  w.eve_db.get_whsize_by_system.return_value = WormholeSize.MEDIUM
  return w


def _response(status_code=200, payload=None):
  r = mock.Mock()
  r.status_code = status_code
  r.json = mock.Mock(return_value=payload if payload is not None else {'data': []})
  return r


def _connection(**overrides):
  """A healthy wormhole as Wanderer's API returns it (all codes 0 = normal)."""
  conn = {
    'id': 'c1',
    'solar_system_source': J_SYSTEM_ID,
    'solar_system_target': THERA_ID,
    'type': 0,
    'time_status': 0,
    'mass_status': 0,
    'ship_size_type': 2,
    'wormhole_type': None,
    'updated_at': '2026-11-08T00:00:00Z',
  }
  conn.update(overrides)
  return conn


def _signature(**overrides):
  sig = {
    'eve_id': 'ABC-123',
    'group': 'Wormhole',
    'solar_system_id': J_SYSTEM_ID,
    'linked_system_id': THERA_ID,
    'type': 'F353',
  }
  sig.update(overrides)
  return sig


def _routes(connections=None, signatures=None, conn_response=None, sig_response=None):
  """A fake requests.get that answers per endpoint."""
  responses = {
    f'{BASE}/connections': conn_response or _response(payload={'data': connections or []}),
    f'{BASE}/signatures': sig_response or _response(payload={'data': signatures or []}),
  }
  return lambda url, **kwargs: responses[url]


class TestWandererConfig(unittest.TestCase):

  def test_valid_config(self):
    self.assertEqual(_make_wanderer().validate_config(), (True, None))

  def test_missing_fields_are_reported(self):
    for kwargs, expected in (
      (dict(url=''), 'URL is required'),
      (dict(map_slug=''), 'Map slug is required'),
      (dict(token=''), 'API token is required'),
    ):
      is_valid, error = _make_wanderer(**kwargs).validate_config()
      self.assertFalse(is_valid)
      self.assertEqual(error, expected)

  def test_url_normalization(self):
    w = _make_wanderer(url='wanderer.example.com/')
    self.assertEqual(w.url, 'https://wanderer.example.com')

  def test_misconfigured_augment_returns_error_without_network(self):
    w = _make_wanderer(token='')
    solar_map = mock.Mock()
    with mock.patch.object(wanderer_module.requests, 'get') as fake_get:
      self.assertEqual(w.augment_map(solar_map), -1)
    fake_get.assert_not_called()
    solar_map.add_connection.assert_not_called()


class TestWandererAugmentMap(unittest.TestCase):

  def _augment(self, connections, signatures=None, wanderer=None, **route_kwargs):
    w = wanderer or _make_wanderer()
    solar_map = mock.Mock()
    with mock.patch.object(
      wanderer_module.requests, 'get',
      side_effect=_routes(connections, signatures, **route_kwargs),
    ) as fake_get:
      count = w.augment_map(solar_map)
    return count, solar_map, fake_get

  def _info(self, solar_map, index=0):
    return solar_map.add_connection.call_args_list[index].args[3]

  def test_requests_both_endpoints_with_the_token(self):
    _, _, fake_get = self._augment([_connection()])
    urls = [c.args[0] if c.args else c.kwargs['url'] for c in fake_get.call_args_list]
    self.assertEqual(urls, [f'{BASE}/connections', f'{BASE}/signatures'])
    for call in fake_get.call_args_list:
      self.assertEqual(call.kwargs['headers']['Authorization'], 'Bearer secret-token')

  def test_jump_recorded_hole_without_signatures_is_routed(self):
    # Holes Wanderer records from character jumps have no signature.
    count, solar_map, _ = self._augment([_connection()])
    self.assertEqual(count, 1)
    source, dest, con_type, info = solar_map.add_connection.call_args.args
    self.assertEqual((source, dest, con_type), (J_SYSTEM_ID, THERA_ID, ConnectionType.WORMHOLE))
    self.assertEqual(info[0:4], ['???', '----', '???', '----'])
    self.assertEqual(solar_map.add_connection.call_args.kwargs['source_name'], 'Test Wanderer')

  def test_signature_without_a_connection_is_not_routed(self):
    # A deleted (collapsed) connection leaves its signature's linked system
    # behind; only the connections endpoint says the hole is gone.
    count, solar_map, _ = self._augment([], [_signature()])
    self.assertEqual(count, 0)
    solar_map.add_connection.assert_not_called()

  def test_gates_and_bridges_are_skipped(self):
    count, solar_map, _ = self._augment([_connection(type=1), _connection(type=2)])
    self.assertEqual(count, 0)
    solar_map.add_connection.assert_not_called()

  def test_signatures_supply_sig_ids_and_types_on_both_sides(self):
    count, solar_map, _ = self._augment(
      [_connection()],
      [
        _signature(),
        _signature(eve_id='XYZ-789', solar_system_id=THERA_ID, linked_system_id=J_SYSTEM_ID, type='K162'),
      ],
    )
    self.assertEqual(count, 1)
    self.assertEqual(self._info(solar_map)[0:4], ['ABC-123', 'F353', 'XYZ-789', 'K162'])

  def test_known_type_on_one_side_makes_the_far_side_k162(self):
    _, solar_map, _ = self._augment([_connection()], [_signature()])
    self.assertEqual(self._info(solar_map)[0:4], ['ABC-123', 'F353', '???', 'K162'])

  def test_k162_on_one_side_leaves_the_far_side_unknown(self):
    _, solar_map, _ = self._augment([_connection()], [_signature(type='K162')])
    self.assertEqual(self._info(solar_map)[1], 'K162')
    self.assertEqual(self._info(solar_map)[3], '----')

  def test_connection_wormhole_type_is_the_source_side_when_no_signature(self):
    _, solar_map, _ = self._augment([_connection(wormhole_type='d845')])
    self.assertEqual(self._info(solar_map)[1], 'D845')
    self.assertEqual(self._info(solar_map)[3], 'K162')

  def test_signature_group_is_case_insensitive(self):
    _, solar_map, _ = self._augment([_connection()], [_signature(group='wormhole')])
    self.assertEqual(self._info(solar_map)[0], 'ABC-123')

  def test_life_codes(self):
    # 0 normal; 1 = EOL 1h and 2 = EOL 4h are end of life; 3+ are longer.
    expected = {
      0: WormholeTimespan.STABLE,
      1: WormholeTimespan.CRITICAL,
      2: WormholeTimespan.CRITICAL,
      3: WormholeTimespan.STABLE,
      4: WormholeTimespan.STABLE,
      5: WormholeTimespan.STABLE,
      6: WormholeTimespan.STABLE,
    }
    _, solar_map, _ = self._augment([_connection(time_status=code) for code in expected])
    for i, life in enumerate(expected.values()):
      self.assertEqual(self._info(solar_map, i)[5], life, f'time_status {list(expected)[i]}')

  def test_mass_codes(self):
    # 0 more than half, 1 less than half, 2 critical.
    expected = {
      0: WormholeMassspan.STABLE,
      1: WormholeMassspan.DESTAB,
      2: WormholeMassspan.CRITICAL,
    }
    _, solar_map, _ = self._augment([_connection(mass_status=code) for code in expected])
    for i, mass in enumerate(expected.values()):
      self.assertEqual(self._info(solar_map, i)[6], mass, f'mass_status {list(expected)[i]}')

  def test_missing_codes_mean_normal(self):
    conn = _connection()
    del conn['time_status'], conn['mass_status'], conn['type']
    count, solar_map, _ = self._augment([conn, _connection(time_status=None, mass_status=None)])
    self.assertEqual(count, 2)
    for i in range(2):
      self.assertEqual(self._info(solar_map, i)[5], WormholeTimespan.STABLE)
      self.assertEqual(self._info(solar_map, i)[6], WormholeMassspan.STABLE)

  def test_size_prefers_the_hole_type(self):
    w = _make_wanderer()
    w.eve_db.get_whsize_by_code.return_value = WormholeSize.XLARGE
    _, solar_map, _ = self._augment([_connection(ship_size_type=0)], [_signature()], wanderer=w)
    self.assertEqual(self._info(solar_map)[4], WormholeSize.XLARGE)

  def test_size_falls_back_to_ship_size_type(self):
    expected = {0: WormholeSize.SMALL, 1: WormholeSize.MEDIUM, 2: WormholeSize.LARGE,
                3: WormholeSize.XLARGE, 4: WormholeSize.XLARGE}
    _, solar_map, _ = self._augment([_connection(ship_size_type=code) for code in expected])
    for i, size in enumerate(expected.values()):
      self.assertEqual(self._info(solar_map, i)[4], size)

  def test_size_falls_back_to_system_pair(self):
    _, solar_map, _ = self._augment([_connection(ship_size_type=None)])
    self.assertEqual(self._info(solar_map)[4], WormholeSize.MEDIUM)

  def test_malformed_connections_are_skipped(self):
    count, _, _ = self._augment([
      _connection(solar_system_target=None),
      _connection(solar_system_source='not-a-number'),
      'not a dict',
    ])
    self.assertEqual(count, 0)

  def test_signature_failure_still_routes_holes(self):
    count, solar_map, _ = self._augment(
      [_connection()], sig_response=_response(status_code=500),
    )
    self.assertEqual(count, 1)
    self.assertEqual(self._info(solar_map)[0], '???')


class TestWandererFailureModes(unittest.TestCase):

  def _augment_with_response(self, response=None, side_effect=None):
    w = _make_wanderer()
    solar_map = mock.Mock()
    with mock.patch.object(
      wanderer_module.requests, 'get',
      return_value=response, side_effect=side_effect,
    ):
      return w.augment_map(solar_map), solar_map

  def test_unauthorized_returns_error(self):
    count, solar_map = self._augment_with_response(_response(status_code=401))
    self.assertEqual(count, -1)
    solar_map.add_connection.assert_not_called()

  def test_map_not_found_returns_error(self):
    count, _ = self._augment_with_response(_response(status_code=404))
    self.assertEqual(count, -1)

  def test_server_error_returns_error(self):
    count, _ = self._augment_with_response(_response(status_code=500))
    self.assertEqual(count, -1)

  def test_network_exception_returns_error(self):
    count, _ = self._augment_with_response(
      side_effect=requests.ConnectionError('offline')
    )
    self.assertEqual(count, -1)

  def test_unexpected_response_shape_returns_error(self):
    count, _ = self._augment_with_response(
      _response(payload=['not', 'a', 'dict'])
    )
    self.assertEqual(count, -1)


class TestTimeElapsed(unittest.TestCase):

  def test_z_suffix_is_parsed(self):
    self.assertGreater(Wanderer._time_elapsed('2026-01-01T00:00:00Z'), 0.0)

  def test_missing_or_malformed_returns_zero(self):
    self.assertEqual(Wanderer._time_elapsed(None), 0.0)
    self.assertEqual(Wanderer._time_elapsed('yesterday-ish'), 0.0)


if __name__ == '__main__':
  unittest.main()
