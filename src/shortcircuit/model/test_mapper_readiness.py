# test_mapper_readiness.py
"""Mappers missing their credentials are never fetched.

A fresh install's default config enables Tripwire with no account. Without
this guard the startup fetch would send a blank-credential login to the
Tripwire server (Tripwire logs in from its constructor) and greet every new
user with an error.
"""

import os

# The suite is headless: select the Qt platform plugin before Qt is imported.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest import mock

import pytest

from shortcircuit.model.mapper_config import (
  TYPE_EVESCOUT,
  TYPE_TRIPWIRE,
  MapperConfig,
  default_configs,
  is_configured,
)


@pytest.mark.parametrize("cfg,expected", [
  (MapperConfig(type=TYPE_TRIPWIRE, name="t", url="https://tw"), False),
  (MapperConfig(type=TYPE_TRIPWIRE, name="t", url="https://tw", user="u"), False),
  (MapperConfig(type=TYPE_TRIPWIRE, name="t", user="u", password="p"), False),
  (MapperConfig(type=TYPE_TRIPWIRE, name="t", url="https://tw", user="u", password="p"), True),
  (MapperConfig(type=TYPE_EVESCOUT, name="e"), True),
  (MapperConfig(type="mystery", name="m", url="x", user="u", password="p"), False),
])
def test_is_configured(cfg, expected):
  assert is_configured(cfg) is expected


def test_fresh_install_defaults_have_nothing_ready():
  # The default Tripwire is enabled but has no account; Eve Scout is off.
  assert not any(c.enabled and is_configured(c) for c in default_configs())


def test_setup_mappers_never_builds_an_unconfigured_mapper():
  from shortcircuit.model import navigation
  from shortcircuit.model.navigation import Navigation

  app_obj = mock.Mock()
  app_obj.mapper_configs = [
    MapperConfig(type=TYPE_TRIPWIRE, name="Blank Tripwire", url="https://tw"),
    MapperConfig(type=TYPE_EVESCOUT, name="Eve Scout", enabled=True),
  ]
  nav = Navigation.__new__(Navigation)
  nav.app_obj = app_obj
  nav.mapper_registry = navigation.MapperRegistry()

  built = []
  builders = {
    TYPE_TRIPWIRE: lambda cfg: built.append(cfg.name) or pytest.fail("built a blank Tripwire"),
    TYPE_EVESCOUT: lambda cfg: built.append(cfg.name) or mock.Mock(
      validate_config=lambda: (True, None), get_name=lambda: cfg.name),
  }
  with mock.patch.dict(navigation.MAPPER_BUILDERS, builders, clear=True):
    nav.setup_mappers()

  assert built == ["Eve Scout"]
  assert nav.mapper_registry.get_source_count() == 1
