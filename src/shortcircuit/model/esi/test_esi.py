# test_esi.py

import base64
import json
import os
import tempfile
import time
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


class _FakeKeyring:
  """In-memory stand-in for the keyring module; tests must never touch the
  real OS keychain (it can prompt interactively on macOS)."""

  def __init__(self):
    self.store = {}

  def set_password(self, service, username, password):
    self.store[(service, username)] = password

  def get_password(self, service, username):
    return self.store.get((service, username))

  def delete_password(self, service, username):
    try:
      del self.store[(service, username)]
    except KeyError:
      raise Exception('no such entry')


def _make_jwt(char_id=92000001, name='Test Pilot'):
  payload = {
    'iss': 'https://login.eveonline.com',
    'aud': [ESI.CLIENT_ID, 'EVE Online'],
    'exp': int(time.time()) + 1200,
    'sub': 'CHARACTER:EVE:{}'.format(char_id),
    'name': name,
  }
  body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b'=').decode()
  return 'header.{}.signature'.format(body)


class _PersistenceCase(unittest.TestCase):
  """Common fixture: fake keyring, temp char_id meta file, no real timers."""

  def setUp(self):
    _reset_metadata_cache()
    self.fake_keyring = _FakeKeyring()
    self.meta_path = os.path.join(tempfile.mkdtemp(), 'esi_char_id')

    patchers = [
      mock.patch.object(esi_module, 'keyring', self.fake_keyring),
      mock.patch.object(esi_module, 'keyring_errors', None),
      mock.patch.object(ESI, '_char_id_meta_path', staticmethod(lambda: self.meta_path)),
      mock.patch.object(ESI, '_schedule_refresh', lambda self_, expires_in: None),
    ]
    for p in patchers:
      p.start()
      self.addCleanup(p.stop)

    self.login_calls = []
    self.logout_calls = []
    self.esi = ESI(
      lambda is_ok, char_name: self.login_calls.append((is_ok, char_name)),
      lambda: self.logout_calls.append(True),
    )

  def _persist_session(self, char_id=92000001, refresh_token='rt-old'):
    self.fake_keyring.set_password(ESI.KEYRING_SERVICE, str(char_id), refresh_token)
    with open(self.meta_path, 'w') as f:
      f.write(str(char_id))


class TestRefreshTokenStorage(_PersistenceCase):

  def test_store_load_delete_roundtrip(self):
    self.assertTrue(ESI._store_refresh_token(92000001, 'rt-secret'))
    self.assertEqual(ESI._load_refresh_token(92000001), 'rt-secret')
    ESI._delete_refresh_token(92000001)
    self.assertIsNone(ESI._load_refresh_token(92000001))

  def test_char_id_meta_roundtrip(self):
    ESI._save_persisted_char_id(92000001)
    self.assertEqual(ESI._load_persisted_char_id(), 92000001)
    ESI._clear_persisted_char_id()
    self.assertIsNone(ESI._load_persisted_char_id())

  def test_keyring_unavailable_degrades_gracefully(self):
    with mock.patch.object(esi_module, 'keyring', None):
      self.assertFalse(ESI._store_refresh_token(92000001, 'rt-secret'))
      self.assertIsNone(ESI._load_refresh_token(92000001))
      ESI._delete_refresh_token(92000001)  # must not raise


class TestSilentLogin(_PersistenceCase):

  def test_no_persisted_session_returns_false(self):
    with mock.patch.object(esi_module.requests, 'post') as fake_post:
      self.assertFalse(self.esi.try_silent_login())
    fake_post.assert_not_called()
    self.assertEqual(self.login_calls, [])

  def test_stale_meta_without_keyring_entry_is_cleaned_up(self):
    with open(self.meta_path, 'w') as f:
      f.write('92000001')
    with mock.patch.object(esi_module.requests, 'post') as fake_post:
      self.assertFalse(self.esi.try_silent_login())
    fake_post.assert_not_called()
    self.assertFalse(os.path.exists(self.meta_path))

  def test_resumes_session_and_persists_rotated_token(self):
    self._persist_session(refresh_token='rt-old')
    response = mock.Mock(
      status_code=200,
      json=lambda: {
        'access_token': _make_jwt(),
        'refresh_token': 'rt-rotated',
        'expires_in': 1200,
      },
    )
    with mock.patch.object(esi_module.requests, 'post', return_value=response) as fake_post:
      self.assertTrue(self.esi.try_silent_login())

    sent = fake_post.call_args.kwargs['data']
    self.assertEqual(sent['grant_type'], 'refresh_token')
    self.assertEqual(sent['refresh_token'], 'rt-old')
    self.assertEqual(self.login_calls, [(True, 'Test Pilot')])
    self.assertEqual(self.esi.char_id, 92000001)
    # CCP rotates the refresh token; the rotated value must be persisted or
    # the NEXT silent login would present a single-use token twice.
    self.assertEqual(ESI._load_refresh_token(92000001), 'rt-rotated')
    self.assertEqual(ESI._load_persisted_char_id(), 92000001)

  def test_dead_token_is_purged_and_logs_out(self):
    self._persist_session()
    response = mock.Mock(status_code=400, text='invalid_grant')
    with mock.patch.object(esi_module.requests, 'post', return_value=response):
      self.assertFalse(self.esi.try_silent_login())

    self.assertEqual(self.login_calls, [])
    self.assertEqual(self.logout_calls, [True])
    self.assertIsNone(ESI._load_refresh_token(92000001))
    self.assertIsNone(ESI._load_persisted_char_id())

  def test_network_failure_logs_out_without_crashing(self):
    self._persist_session()
    with mock.patch.object(
      esi_module.requests, 'post', side_effect=requests.ConnectionError('offline')
    ):
      self.assertFalse(self.esi.try_silent_login())
    self.assertEqual(self.logout_calls, [True])


class TestLogoutPurgesSession(_PersistenceCase):

  def test_logout_removes_keyring_entry_and_meta(self):
    self._persist_session()
    self.esi.char_id = 92000001
    self.esi.refresh_token = 'rt-old'
    self.esi.token = 'at'

    self.esi.logout()

    self.assertEqual(self.logout_calls, [True])
    self.assertIsNone(ESI._load_refresh_token(92000001))
    self.assertIsNone(ESI._load_persisted_char_id())


if __name__ == '__main__':
  unittest.main()
