# esi.py

import base64
import hashlib
import json
import os
import time
import threading
import urllib.parse
import uuid
import webbrowser

import requests
from appdirs import AppDirs

from shortcircuit.model.logger import Logger
from shortcircuit import USER_AGENT, __appslug__

from .server import AuthHandler, StoppableHTTPServer

try:
  import keyring
  import keyring.errors as keyring_errors
except Exception:  # pragma: no cover - keyring is an optional backend
  keyring = None
  keyring_errors = None

# CCP recommends discovering SSO endpoints from the OAuth metadata document
# rather than hardcoding them. When they retire or move a route (as with the
# 24 March 2026 spring cleaning that removed /verify and the implicit flow) a
# deployed client that follows the metadata keeps working without a rebuild.
# The hardcoded ESI.ENDPOINT_EVE_* values below are only used if the metadata
# fetch fails.
# https://developers.eveonline.com/docs/services/sso/
ENDPOINT_EVE_METADATA = 'https://login.eveonline.com/.well-known/oauth-authorization-server'
_METADATA_CACHE_TTL_SECONDS = 3600

_metadata_cache_lock = threading.Lock()
_metadata_cache = {'fetched_at': 0.0, 'endpoints': None}


def discover_sso_endpoints(force_refresh=False):
  """
  Fetch and cache the EVE SSO OAuth metadata document.

  Returns a dict with at least ``authorization_endpoint`` and
  ``token_endpoint``. On network failure, returns the hardcoded fallback
  values so login still works (at least until CCP retires those routes).
  The cache is per-process, in-memory, and refreshes hourly.
  """
  now = time.monotonic()
  with _metadata_cache_lock:
    cached = _metadata_cache['endpoints']
    if (
      not force_refresh and cached is not None
      and now - _metadata_cache['fetched_at'] < _METADATA_CACHE_TTL_SECONDS
    ):
      return cached

  try:
    r = requests.get(
      ENDPOINT_EVE_METADATA,
      headers={'User-Agent': USER_AGENT},
      timeout=10.0,
    )
    r.raise_for_status()
    data = r.json()
    endpoints = {
      'authorization_endpoint': data['authorization_endpoint'],
      'token_endpoint': data['token_endpoint'],
    }
  except (requests.RequestException, KeyError, ValueError) as e:
    Logger.warning(
      'SSO metadata discovery failed ({}); falling back to hardcoded endpoints'.format(e)
    )
    endpoints = {
      'authorization_endpoint': ESI.ENDPOINT_EVE_AUTH,
      'token_endpoint': ESI.ENDPOINT_EVE_TOKEN,
    }

  with _metadata_cache_lock:
    _metadata_cache['fetched_at'] = now
    _metadata_cache['endpoints'] = endpoints
  return endpoints


class ESI:

  ENDPOINT_ESI_LOCATION_FORMAT = 'https://esi.evetech.net/latest/characters/{}/location/'
  ENDPOINT_ESI_UNIVERSE_NAMES = 'https://esi.evetech.net/latest/universe/names/'
  ENDPOINT_ESI_UI_WAYPOINT = 'https://esi.evetech.net/latest/ui/autopilot/waypoint/'

  ENDPOINT_EVE_AUTH = 'https://login.eveonline.com/v2/oauth/authorize'
  ENDPOINT_EVE_TOKEN = 'https://login.eveonline.com/v2/oauth/token'
  CLIENT_CALLBACK = 'http://127.0.0.1:7444/callback/'
  CLIENT_ID = 'd802bba44b7c4f6cbfa2944b0e5ea83f'
  CLIENT_SCOPES = [
    'esi-location.read_location.v1',
    'esi-ui.write_waypoint.v1',
  ]

  # Keyring service name for the persisted refresh token. Username is the
  # EVE character_id as a string, so a future multi-character feature can
  # store one entry per character without changing the schema.
  KEYRING_SERVICE = 'shortcircuit-esi'
  # Filename under appdirs.user_data_dir holding the most-recently-used
  # character_id. The id itself is public (it appears in killboards, zKill,
  # ESI URLs); the secret is the refresh token, which lives in the keyring.
  # Deliberately NOT version-scoped like the log dir: the persisted session
  # should survive app upgrades.
  CHAR_ID_META_FILENAME = 'esi_char_id'

  def __init__(self, login_callback, logout_callback):
    self.login_callback = login_callback
    self.logout_callback = logout_callback
    self.httpd = None
    self.state = None
    self._code_verifier = None

    self.token = None
    self.refresh_token = None
    self.char_id = None
    self.char_name = None
    self.sso_timer = None

  def _generate_pkce(self):
    verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode('ascii')
    digest = hashlib.sha256(verifier.encode('ascii')).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')
    return verifier, challenge

  def _decode_jwt(self, token):
    try:
      payload_b64 = token.split('.')[1]
      padding = 4 - len(payload_b64) % 4
      if padding != 4:
        payload_b64 += '=' * padding
      claims = json.loads(base64.urlsafe_b64decode(payload_b64))
    except Exception as e:
      Logger.warning('Failed to decode JWT: {}'.format(e))
      return None

    iss = claims.get('iss', '')
    if iss not in ('https://login.eveonline.com', 'login.eveonline.com'):
      Logger.warning('JWT issuer invalid: {}'.format(iss))
      return None

    aud = claims.get('aud', [])
    if isinstance(aud, str):
      aud = [aud]
    if ESI.CLIENT_ID not in aud or 'EVE Online' not in aud:
      Logger.warning('JWT audience invalid: {}'.format(aud))
      return None

    exp = claims.get('exp', 0)
    if exp <= int(time.time()):
      Logger.warning('JWT already expired')
      return None

    return claims

  def start_server(self):
    if not self.httpd:
      Logger.debug('Starting server')
      self.httpd = StoppableHTTPServer(
        server_address=('127.0.0.1', 7444),
        request_handler_class=AuthHandler,
        timeout_callback=self.timeout_server,
      )
      server_thread = threading.Thread(
        target=self.httpd.serve,
        args=(self.handle_login, ),
      )
      server_thread.setDaemon(True)
      server_thread.start()
      self.state = str(uuid.uuid4())
    else:
      self.httpd.tries = 0

    self._code_verifier, code_challenge = self._generate_pkce()
    scopes = ' '.join(ESI.CLIENT_SCOPES)
    params = {
      'response_type': 'code',
      'redirect_uri': ESI.CLIENT_CALLBACK,
      'client_id': ESI.CLIENT_ID,
      'scope': scopes,
      'state': self.state,
      'code_challenge': code_challenge,
      'code_challenge_method': 'S256',
    }
    endpoints = discover_sso_endpoints()
    endpoint_auth = endpoints['authorization_endpoint'] + '?' + urllib.parse.urlencode(params)
    return webbrowser.open(endpoint_auth)

  def timeout_server(self):
    self.httpd = None

  def stop_server(self):
    Logger.debug('Stopping server')
    if self.httpd:
      self.httpd.stop()
      self.httpd = None

  def handle_login(self, message):
    if not message:
      return

    if 'state' in message:
      if message['state'][0] != self.state:
        Logger.warning('OAUTH state mismatch')
        return

    if 'code' not in message:
      return

    code = message['code'][0]
    # Reuse the metadata cache warmed by start_server() so we post to the
    # same token endpoint CCP currently advertises.
    endpoints = discover_sso_endpoints()
    r = requests.post(
      endpoints['token_endpoint'],
      data={
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': ESI.CLIENT_ID,
        'code_verifier': self._code_verifier,
      },
      headers={'User-Agent': USER_AGENT},
    )

    if r.status_code != requests.codes.ok:
      Logger.warning('Token exchange failed: {} {}'.format(r.status_code, r.text))
      self.login_callback(False, None)
      self.stop_server()
      return

    token_data = r.json()
    self.token = token_data['access_token']
    self.refresh_token = token_data.get('refresh_token')
    expires_in = token_data.get('expires_in', 1200)
    self._schedule_refresh(expires_in)

    claims = self._decode_jwt(self.token)
    if claims:
      # sub format: "CHARACTER:EVE:<character_id>"
      sub = claims.get('sub', '')
      self.char_id = int(sub.split(':')[-1]) if sub.startswith('CHARACTER:EVE:') else None
      self.char_name = claims.get('name')
      if self.char_id is not None and self.refresh_token:
        ESI._store_refresh_token(self.char_id, self.refresh_token)
        ESI._save_persisted_char_id(self.char_id)
      self.login_callback(True, self.char_name)
    else:
      self._clear_tokens()
      self.login_callback(False, None)

    self.stop_server()

  def _schedule_refresh(self, expires_in):
    if self.sso_timer:
      self.sso_timer.cancel()
    delay = max(expires_in - 60, 60)
    self.sso_timer = threading.Timer(delay, self._refresh_access_token)
    self.sso_timer.setDaemon(True)
    self.sso_timer.start()

  def _refresh_access_token(self):
    """
    Exchange the stored refresh token for a fresh access token. Called at
    startup via try_silent_login() and from the background sso_timer before
    the current access token expires.

    CCP rotates the refresh token on every successful refresh, so the
    response carries a NEW refresh_token superseding the old one. Persisting
    the rotated value is mandatory — re-using the old token a second time
    fails with invalid_grant.

    Returns True iff the refresh succeeded and self.token is now valid; on
    failure _logout() has already run, which also purges the persisted
    session so a dead token is not retried on every startup.
    """
    if not self.refresh_token:
      self._logout()
      return False

    endpoints = discover_sso_endpoints()
    try:
      r = requests.post(
        endpoints['token_endpoint'],
        data={
          'grant_type': 'refresh_token',
          'refresh_token': self.refresh_token,
          'client_id': ESI.CLIENT_ID,
          'code_verifier': self._code_verifier,
        },
        headers={'User-Agent': USER_AGENT},
      )
    except requests.RequestException as e:
      # A network blip, not necessarily a dead token. Log out so the user
      # sees an honest disconnected state; they can click Login to retry.
      # Without this, an offline refresh kills the timer thread and leaves
      # the UI claiming to be connected with an expired token.
      Logger.warning('Token refresh request failed: {}'.format(e))
      self._logout()
      return False

    if r.status_code != requests.codes.ok:
      Logger.warning('Token refresh failed: {} {}'.format(r.status_code, r.text))
      self._logout()
      return False

    token_data = r.json()
    self.token = token_data['access_token']
    self.refresh_token = token_data.get('refresh_token', self.refresh_token)
    expires_in = token_data.get('expires_in', 1200)
    self._schedule_refresh(expires_in)

    if self.char_id is None or self.char_name is None:
      # Silent-login path: character identity comes from the fresh JWT.
      claims = self._decode_jwt(self.token)
      if not claims:
        self._logout()
        return False
      sub = claims.get('sub', '')
      self.char_id = int(sub.split(':')[-1]) if sub.startswith('CHARACTER:EVE:') else None
      self.char_name = claims.get('name')

    if self.char_id is not None and self.refresh_token:
      ESI._store_refresh_token(self.char_id, self.refresh_token)
      ESI._save_persisted_char_id(self.char_id)

    Logger.debug('ESI token refreshed for {}'.format(self.char_name))
    return True

  def try_silent_login(self):
    """
    Resume a previous session using a persisted refresh token, with no
    browser interaction. Intended to be called once at app startup. Fires
    login_callback on success so the UI can flip to its logged-in state.
    Returns True iff a session was resumed.
    """
    char_id = ESI._load_persisted_char_id()
    if char_id is None:
      return False
    refresh_token = ESI._load_refresh_token(char_id)
    if not refresh_token:
      # Stale meta file pointing at a character with no keyring entry —
      # clean it up so we don't keep checking on every startup.
      ESI._clear_persisted_char_id()
      return False

    self.refresh_token = refresh_token
    self.char_id = char_id

    if not self._refresh_access_token():
      return False

    self.login_callback(True, self.char_name)
    return True

  # The refresh token is functionally equivalent to a password — anyone
  # holding it can act as the user against ESI within the granted scopes
  # until it is revoked. It is therefore stored in the OS keychain (Keychain
  # on macOS, Credential Manager on Windows, Secret Service on Linux) via
  # the keyring library, never in a plaintext file. If no keyring backend is
  # available (eg. a headless Linux session without Secret Service) we
  # silently degrade to the old behaviour: the user re-auths each session,
  # but the secret is never written to disk in the clear.

  @staticmethod
  def _char_id_meta_path():
    app_dirs = AppDirs(__appslug__, 'secondfry')
    os.makedirs(app_dirs.user_data_dir, exist_ok=True)
    return os.path.join(app_dirs.user_data_dir, ESI.CHAR_ID_META_FILENAME)

  @staticmethod
  def _load_persisted_char_id():
    try:
      with open(ESI._char_id_meta_path(), 'r') as f:
        return int(f.read().strip())
    except (FileNotFoundError, ValueError, OSError):
      return None

  @staticmethod
  def _save_persisted_char_id(char_id):
    try:
      with open(ESI._char_id_meta_path(), 'w') as f:
        f.write(str(char_id))
    except OSError as e:
      Logger.warning('Failed to persist char_id: {}'.format(e))

  @staticmethod
  def _clear_persisted_char_id():
    try:
      os.remove(ESI._char_id_meta_path())
    except FileNotFoundError:
      pass
    except OSError as e:
      Logger.warning('Failed to clear persisted char_id: {}'.format(e))

  @staticmethod
  def _store_refresh_token(char_id, refresh_token):
    if keyring is None:
      Logger.warning(
        'keyring unavailable; skipping refresh-token persistence '
        '(user will need to re-auth next session)'
      )
      return False
    try:
      keyring.set_password(ESI.KEYRING_SERVICE, str(char_id), refresh_token)
      return True
    except Exception as e:
      Logger.warning('Could not store refresh token in keyring: {}'.format(e))
      return False

  @staticmethod
  def _load_refresh_token(char_id):
    if keyring is None:
      return None
    try:
      return keyring.get_password(ESI.KEYRING_SERVICE, str(char_id))
    except Exception as e:
      Logger.warning('Could not load refresh token from keyring: {}'.format(e))
      return None

  @staticmethod
  def _delete_refresh_token(char_id):
    if keyring is None:
      return
    try:
      keyring.delete_password(ESI.KEYRING_SERVICE, str(char_id))
    except Exception as e:
      # PasswordDeleteError when the entry doesn't exist is benign; other
      # errors are just logged — there is nothing the user can do.
      if keyring_errors and isinstance(e, keyring_errors.PasswordDeleteError):
        return
      Logger.warning('Could not delete refresh token from keyring: {}'.format(e))

  def _clear_tokens(self):
    self.token = None
    self.refresh_token = None
    self.sso_timer = None
    self.char_id = None
    self.char_name = None

  def _get_headers(self):
    return {
      'User-Agent': USER_AGENT,
      'Authorization': 'Bearer {}'.format(self.token),
    }

  def get_char_location(self):
    if not self.token:
      return None

    current_location_name = None
    current_location_id = None

    r = requests.get(
      ESI.ENDPOINT_ESI_LOCATION_FORMAT.format(self.char_id),
      headers=self._get_headers()
    )
    if r.status_code == requests.codes.ok:
      current_location_id = r.json()['solar_system_id']

    r = requests.post(
      ESI.ENDPOINT_ESI_UNIVERSE_NAMES, json=[str(current_location_id)]
    )
    if r.status_code == requests.codes.ok:
      current_location_name = r.json()[0]['name']

    return current_location_name

  def set_char_destination(self, sys_id):
    if not self.token:
      return False

    r = requests.post(
      '{}?add_to_beginning=false&clear_other_waypoints=true&destination_id={}'.format(
        ESI.ENDPOINT_ESI_UI_WAYPOINT,
        sys_id,
      ),
      headers=self._get_headers()
    )
    return r.status_code == 204

  def logout(self):
    if self.sso_timer:
      self.sso_timer.cancel()
    self._logout()

  def _logout(self):
    # Purge persisted credentials so a restart doesn't silently resume a
    # session the user (or the server) just ended. Both operations are
    # no-ops when the entries don't exist.
    if self.char_id is not None:
      ESI._delete_refresh_token(self.char_id)
    ESI._clear_persisted_char_id()
    self._clear_tokens()
    self._code_verifier = None
    self.logout_callback()
