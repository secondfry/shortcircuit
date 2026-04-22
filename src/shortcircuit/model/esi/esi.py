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
from shortcircuit.model.logger import Logger
from shortcircuit import USER_AGENT

from .server import AuthHandler, StoppableHTTPServer


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
    endpoint_auth = ESI.ENDPOINT_EVE_AUTH + '?' + urllib.parse.urlencode(params)
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
    r = requests.post(
      ESI.ENDPOINT_EVE_TOKEN,
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
    if not self.refresh_token:
      self._logout()
      return

    r = requests.post(
      ESI.ENDPOINT_EVE_TOKEN,
      data={
        'grant_type': 'refresh_token',
        'refresh_token': self.refresh_token,
        'client_id': ESI.CLIENT_ID,
        'code_verifier': self._code_verifier,
      },
      headers={'User-Agent': USER_AGENT},
    )

    if r.status_code == requests.codes.ok:
      token_data = r.json()
      self.token = token_data['access_token']
      self.refresh_token = token_data.get('refresh_token', self.refresh_token)
      expires_in = token_data.get('expires_in', 1200)
      self._schedule_refresh(expires_in)
      Logger.debug('ESI token refreshed for {}'.format(self.char_name))
    else:
      Logger.warning('Token refresh failed: {} {}'.format(r.status_code, r.text))
      self._logout()

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
    self._clear_tokens()
    self._code_verifier = None
    self.logout_callback()
