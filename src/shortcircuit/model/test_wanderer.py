"""Tests for the Wanderer mapper integration

Covers config validation, URL normalization, the signature-to-connection
translation (K162 inference, life/mass mapping from custom_info, elapsed
time), and the failure modes of the API round trip.
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
  w.eve_db.get_whsize_by_system.return_value = WormholeSize.LARGE
  return w


def _response(status_code=200, payload=None):
  r = mock.Mock()
  r.status_code = status_code
  r.json = mock.Mock(return_value=payload if payload is not None else {'data': []})
  return r


def _signature(**overrides):
  sig = {
    'eve_id': 'ABC-123',
    'group': 'Wormhole',
    'solar_system_id': J_SYSTEM_ID,
    'linked_system_id': THERA_ID,
    'type': 'F353',
    'custom_info': '{"time_status": 1, "mass_status": 1}',
    'updated_at': '2026-11-08T00:00:00Z',
  }
  sig.update(overrides)
  return sig


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

  def _augment(self, signatures, wanderer=None):
    w = wanderer or _make_wanderer()
    solar_map = mock.Mock()
    with mock.patch.object(
      wanderer_module.requests, 'get',
      return_value=_response(payload={'data': signatures}),
    ) as fake_get:
      count = w.augment_map(solar_map)
    return count, solar_map, fake_get

  def test_linked_wormhole_becomes_connection(self):
    count, solar_map, fake_get = self._augment([_signature()])

    self.assertEqual(count, 1)
    url = fake_get.call_args.kwargs['url']
    self.assertEqual(url, 'https://wanderer.example.com/api/maps/my-map/signatures')
    headers = fake_get.call_args.kwargs['headers']
    self.assertEqual(headers['Authorization'], 'Bearer secret-token')

    args, kwargs = solar_map.add_connection.call_args
    source, dest, con_type, info = args
    self.assertEqual(source, J_SYSTEM_ID)
    self.assertEqual(dest, THERA_ID)
    self.assertEqual(con_type, ConnectionType.WORMHOLE)
    sig_source, code_source, sig_dest, code_dest = info[0:4]
    self.assertEqual(sig_source, 'ABC-123')
    self.assertEqual(code_source, 'F353')
    self.assertEqual(sig_dest, '???')
    # The scanned side carries the hole type; the far side is a K162.
    self.assertEqual(code_dest, 'K162')
    self.assertEqual(kwargs['source_name'], 'Test Wanderer')

  def test_unknown_type_does_not_fabricate_k162(self):
    count, solar_map, _ = self._augment([_signature(type=None)])
    self.assertEqual(count, 1)
    info = solar_map.add_connection.call_args.args[3]
    self.assertEqual(info[1], '????')
    self.assertEqual(info[3], '????')

  def test_unlinked_and_non_wormhole_signatures_are_skipped(self):
    count, solar_map, _ = self._augment([
      _signature(linked_system_id=None),
      _signature(group='Data'),
      _signature(solar_system_id='not-a-number'),
    ])
    self.assertEqual(count, 0)
    solar_map.add_connection.assert_not_called()

  def test_eol_and_mass_status_map_to_enums(self):
    count, solar_map, _ = self._augment([
      _signature(custom_info='{"time_status": 2, "mass_status": 3}'),
    ])
    self.assertEqual(count, 1)
    info = solar_map.add_connection.call_args.args[3]
    self.assertEqual(info[5], WormholeTimespan.CRITICAL)
    self.assertEqual(info[6], WormholeMassspan.CRITICAL)

  def test_custom_info_accepts_dict_and_tolerates_garbage(self):
    count, solar_map, _ = self._augment([
      _signature(custom_info={'time_status': 1, 'mass_status': 2}),
      _signature(custom_info='not json'),
      _signature(custom_info=None),
    ])
    self.assertEqual(count, 3)
    first = solar_map.add_connection.call_args_list[0].args[3]
    self.assertEqual(first[6], WormholeMassspan.DESTAB)
    for call in solar_map.add_connection.call_args_list[1:]:
      info = call.args[3]
      self.assertEqual(info[5], WormholeTimespan.STABLE)
      self.assertEqual(info[6], WormholeMassspan.STABLE)

  def test_size_falls_back_to_system_pair_when_code_unknown(self):
    count, solar_map, _ = self._augment([_signature()])
    self.assertEqual(count, 1)
    info = solar_map.add_connection.call_args.args[3]
    self.assertEqual(info[4], WormholeSize.LARGE)


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
    self.assertGreaterEqual(
      Wanderer._time_elapsed('2026-01-01T00:00:00Z'), 0.0
    )

  def test_missing_or_malformed_returns_zero(self):
    self.assertEqual(Wanderer._time_elapsed(None), 0.0)
    self.assertEqual(Wanderer._time_elapsed('yesterday-ish'), 0.0)


if __name__ == '__main__':
  unittest.main()
