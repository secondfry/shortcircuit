# test_esi.py

import unittest
from unittest import mock

import requests

from shortcircuit.model.esi import esi as esi_module
from shortcircuit.model.esi.esi import ESI, discover_sso_endpoints


def _reset_metadata_cache():
  with esi_module._metadata_cache_lock:
    esi_module._metadata_cache['fetched_at'] = 0.0
    esi_module._metadata_cache['endpoints'] = None


class _FakeResponse:

  def __init__(self, payload=None, error=None):
    self._payload = payload
    self._error = error

  def raise_for_status(self):
    if self._error:
      raise self._error

  def json(self):
    return self._payload


class TestDiscoverSsoEndpoints(unittest.TestCase):

  def setUp(self):
    _reset_metadata_cache()

  def tearDown(self):
    _reset_metadata_cache()

  def test_success_returns_advertised_endpoints(self):
    payload = {
      'authorization_endpoint': 'https://login.eveonline.com/v3/oauth/authorize',
      'token_endpoint': 'https://login.eveonline.com/v3/oauth/token',
      'issuer': 'https://login.eveonline.com',
    }
    with mock.patch.object(
      esi_module.requests, 'get', return_value=_FakeResponse(payload)
    ) as fake_get:
      endpoints = discover_sso_endpoints()

    fake_get.assert_called_once()
    self.assertEqual(
      endpoints['authorization_endpoint'],
      'https://login.eveonline.com/v3/oauth/authorize',
    )
    self.assertEqual(
      endpoints['token_endpoint'],
      'https://login.eveonline.com/v3/oauth/token',
    )

  def test_result_is_cached(self):
    payload = {
      'authorization_endpoint': 'https://a.example',
      'token_endpoint': 'https://t.example',
    }
    with mock.patch.object(
      esi_module.requests, 'get', return_value=_FakeResponse(payload)
    ) as fake_get:
      discover_sso_endpoints()
      discover_sso_endpoints()

    self.assertEqual(fake_get.call_count, 1)

  def test_force_refresh_bypasses_cache(self):
    payload = {
      'authorization_endpoint': 'https://a.example',
      'token_endpoint': 'https://t.example',
    }
    with mock.patch.object(
      esi_module.requests, 'get', return_value=_FakeResponse(payload)
    ) as fake_get:
      discover_sso_endpoints()
      discover_sso_endpoints(force_refresh=True)

    self.assertEqual(fake_get.call_count, 2)

  def test_network_failure_falls_back_to_hardcoded(self):
    with mock.patch.object(
      esi_module.requests,
      'get',
      return_value=_FakeResponse(error=requests.ConnectionError('boom')),
    ):
      endpoints = discover_sso_endpoints()

    self.assertEqual(endpoints['authorization_endpoint'], ESI.ENDPOINT_EVE_AUTH)
    self.assertEqual(endpoints['token_endpoint'], ESI.ENDPOINT_EVE_TOKEN)

  def test_missing_keys_fall_back_to_hardcoded(self):
    with mock.patch.object(
      esi_module.requests,
      'get',
      return_value=_FakeResponse({'issuer': 'https://login.eveonline.com'}),
    ):
      endpoints = discover_sso_endpoints()

    self.assertEqual(endpoints['authorization_endpoint'], ESI.ENDPOINT_EVE_AUTH)
    self.assertEqual(endpoints['token_endpoint'], ESI.ENDPOINT_EVE_TOKEN)


if __name__ == '__main__':
  unittest.main()
