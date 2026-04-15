# mapper_config.py

import json
from dataclasses import asdict, dataclass, field
from typing import List, Optional

from PySide2 import QtCore

from .logger import Logger

SETTINGS_KEY = "MapperConfigs"

TYPE_TRIPWIRE = "tripwire"
TYPE_EVESCOUT = "evescout"


@dataclass
class MapperConfig:
  """
  Configuration for a single mapper instance persisted in QSettings.

  `type` is the dispatch key used by Navigation.setup_mappers() to decide
  which MapperSource subclass to instantiate; `name` is the user-facing
  label that also serves as the key in the `results` dict emitted by
  NavProcessor. `url`/`user`/`password` are mapper-agnostic config slots —
  Eve Scout ignores user/password.
  """
  type: str
  name: str
  enabled: bool = True
  url: str = ""
  user: str = ""
  password: str = ""

  def to_dict(self) -> dict:
    return asdict(self)

  @classmethod
  def from_dict(cls, data: dict) -> "MapperConfig":
    return cls(
      type=str(data.get("type", "")),
      name=str(data.get("name", "")),
      enabled=bool(data.get("enabled", True)),
      url=str(data.get("url", "") or ""),
      user=str(data.get("user", "") or ""),
      password=str(data.get("password", "") or ""),
    )


def load_configs(settings: QtCore.QSettings) -> List[MapperConfig]:
  raw = settings.value(SETTINGS_KEY)
  if not raw:
    return []
  try:
    decoded = json.loads(raw)
  except (TypeError, ValueError) as e:
    Logger.error(f"Could not parse {SETTINGS_KEY}: {e}")
    return []
  if not isinstance(decoded, list):
    Logger.error(f"{SETTINGS_KEY} is not a list, ignoring")
    return []
  return [MapperConfig.from_dict(entry) for entry in decoded if isinstance(entry, dict)]


def save_configs(settings: QtCore.QSettings, configs: List[MapperConfig]) -> None:
  payload = json.dumps([c.to_dict() for c in configs])
  settings.setValue(SETTINGS_KEY, payload)


def migrate_legacy(settings: QtCore.QSettings) -> Optional[List[MapperConfig]]:
  """
  One-shot migration from the legacy single-Tripwire + evescout_enabled keys
  to the new MapperConfigs list. Returns the new list when a migration
  happened (and removes the old keys), or None when there is nothing to
  migrate — caller can then fall through to an empty/default list.

  Handles both historic layouts:
    - flat: MainWindow/tripwire_url, MainWindow/tripwire_user, ...
    - grouped: Tripwire/url, Tripwire/user, Tripwire/pass, Tripwire/evescout_enabled
  Either of the two URL keys being present is taken as "there is a legacy
  config here, migrate it".
  """
  legacy_keys = (
    'MainWindow/tripwire_url',
    'MainWindow/tripwire_user',
    'MainWindow/tripwire_pass',
    'MainWindow/evescout_enable',
    'Tripwire/url',
    'Tripwire/user',
    'Tripwire/pass',
    'Tripwire/evescout_enabled',
  )
  if not any(settings.contains(k) for k in legacy_keys):
    return None

  flat_url = settings.value('MainWindow/tripwire_url') or ''
  grouped_url = settings.value('Tripwire/url') or ''

  if flat_url:
    url = str(flat_url)
    user = str(settings.value('MainWindow/tripwire_user') or '')
    password = str(settings.value('MainWindow/tripwire_pass') or '')
    evescout_enabled = settings.value('MainWindow/evescout_enable', 'false') == 'true'
  else:
    url = str(grouped_url)
    user = str(settings.value('Tripwire/user') or '')
    password = str(settings.value('Tripwire/pass') or '')
    raw_ev = settings.value('Tripwire/evescout_enabled', False)
    evescout_enabled = raw_ev is True or str(raw_ev).lower() == 'true'

  configs: List[MapperConfig] = []
  if url:
    configs.append(MapperConfig(
      type=TYPE_TRIPWIRE,
      name="Tripwire",
      enabled=True,
      url=url,
      user=user,
      password=password,
    ))
  configs.append(MapperConfig(
    type=TYPE_EVESCOUT,
    name="Eve Scout",
    enabled=evescout_enabled,
    url="https://api.eve-scout.com/v2/public/signatures",
  ))

  save_configs(settings, configs)

  for key in (
    'MainWindow/tripwire_url',
    'MainWindow/tripwire_user',
    'MainWindow/tripwire_pass',
    'MainWindow/evescout_enable',
    'Tripwire/url',
    'Tripwire/user',
    'Tripwire/pass',
    'Tripwire/evescout_enabled',
  ):
    settings.remove(key)

  Logger.info(f"Migrated legacy mapper settings into {SETTINGS_KEY} ({len(configs)} entries)")
  return configs


def default_configs() -> List[MapperConfig]:
  """Sensible defaults for a first-run install with no legacy settings."""
  return [
    MapperConfig(
      type=TYPE_TRIPWIRE,
      name="Tripwire",
      enabled=True,
      url="https://tripwire.eve-apps.com",
    ),
    MapperConfig(
      type=TYPE_EVESCOUT,
      name="Eve Scout",
      enabled=False,
      url="https://api.eve-scout.com/v2/public/signatures",
    ),
  ]
