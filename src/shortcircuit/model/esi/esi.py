# esi.py

import threading
import uuid
import webbrowser

import requests
from shortcircuit.model.logger import Logger
from shortcircuit import USER_AGENT

from .server import AuthHandler, StoppableHTTPServer


class ESI:
  '''
  ESI

  We are bad boys here.
  What should have been done is proxy auth server with code request, storage and all that stuff.
  Instead we just follow implicit flow and ask to relogin every time.
  From Russia with love.
  '''

  ENDPOINT_ESI_VERIFY = 'https://esi.evetech.net/verify'
  ENDPOINT_ESI_LOCATION_FORMAT = 'https://esi.evetech.net/latest/characters/{}/location/'
  ENDPOINT_ESI_UNIVERSE_NAMES = 'https://esi.evetech.net/latest/universe/names/'
  ENDPOINT_ESI_UI_WAYPOINT = 'https://esi.evetech.net/latest/ui/autopilot/waypoint/'

  ENDPOINT_EVE_AUTH_FORMAT = 'https://login.eveonline.com/v2/oauth/authorize' \
                             '?response_type=token&redirect_uri={}&client_id={}&scope={}&state={}'
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

    self.token = None
    self.char_id = None
    self.char_name = None
    self.sso_timer = None

  def start_server(self):
    if not self.httpd:
      # Server not running - restart it
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
      # Server already running - reset timeout counter
      self.httpd.tries = 0

    scopes = ' '.join(ESI.CLIENT_SCOPES)
    endpoint_auth = ESI.ENDPOINT_EVE_AUTH_FORMAT.format(
      ESI.CLIENT_CALLBACK, ESI.CLIENT_ID, scopes, self.state
    )
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

    if 'access_token' in message:
      self.token = message['access_token'][0]
      self.sso_timer = threading.Timer(
        int(message['expires_in'][0]), self._logout
      )
      self.sso_timer.setDaemon(True)
      self.sso_timer.start()

      r = requests.get(ESI.ENDPOINT_ESI_VERIFY, headers=self._get_headers())
      if r.status_code == requests.codes.ok:
        data = r.json()
        self.char_id = data['CharacterID']
        self.char_name = data['CharacterName']

        self.login_callback(True, self.char_name)
      else:
        self.token = None
        self.sso_timer = None
        self.char_id = None
        self.char_name = None

        self.login_callback(False, None)

    self.stop_server()

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

    success = False
    r = requests.post(
      '{}?add_to_beginning=false&clear_other_waypoints=true&destination_id={}'.
      format(
        ESI.ENDPOINT_ESI_UI_WAYPOINT,
        sys_id,
      ),
      headers=self._get_headers()
    )
    if r.status_code == 204:
      success = True

    return success

  def logout(self):
    if self.sso_timer:
      self.sso_timer.cancel()
    self._logout()

  def _logout(self):
    self.token = None
    self.char_id = None
    self.char_name = None
    self.logout_callback()


def login_cb(char_name):
  print('Welcome, {}'.format(char_name))


def logout_cb():
  print('Session expired')


def main():
  import code

  implicit = True
  client_id = ''
  client_secret = ''

  esi = ESI(login_cb, logout_cb)
  print(esi.start_server())
  gvars = globals().copy()
  gvars.update(locals())
  shell = code.InteractiveConsole(gvars)
  shell.interact()


if __name__ == '__main__':
  main()
