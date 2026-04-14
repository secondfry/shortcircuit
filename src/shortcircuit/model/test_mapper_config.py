# test_mapper_config.py

import json
import os
import tempfile
import unittest

from PySide2 import QtCore

from shortcircuit.model.mapper_config import (
  SETTINGS_KEY,
  TYPE_EVESCOUT,
  TYPE_TRIPWIRE,
  MapperConfig,
  default_configs,
  load_configs,
  migrate_legacy,
  save_configs,
)


def _fresh_settings() -> tuple[QtCore.QSettings, str]:
  fd, path = tempfile.mkstemp(suffix='.ini')
  os.close(fd)
  os.unlink(path)
  return QtCore.QSettings(path, QtCore.QSettings.IniFormat), path


class TestMapperConfigRoundTrip(unittest.TestCase):

  def tearDown(self):
    if hasattr(self, "_path") and os.path.exists(self._path):
      os.unlink(self._path)

  def test_empty_load_returns_empty_list(self):
    settings, self._path = _fresh_settings()
    self.assertEqual(load_configs(settings), [])

  def test_roundtrip_preserves_fields(self):
    settings, self._path = _fresh_settings()
    configs = [
      MapperConfig(
        type=TYPE_TRIPWIRE,
        name="Corp Tripwire",
        enabled=True,
        url="https://corp.example/tripwire",
        user="u",
        password="p",
      ),
      MapperConfig(type=TYPE_EVESCOUT, name="Eve Scout", enabled=False),
    ]
    save_configs(settings, configs)
    settings.sync()

    reloaded = load_configs(settings)
    self.assertEqual(reloaded, configs)

  def test_malformed_json_returns_empty(self):
    settings, self._path = _fresh_settings()
    settings.setValue(SETTINGS_KEY, "not-json")
    self.assertEqual(load_configs(settings), [])

  def test_non_list_top_level_returns_empty(self):
    settings, self._path = _fresh_settings()
    settings.setValue(SETTINGS_KEY, json.dumps({"nope": 1}))
    self.assertEqual(load_configs(settings), [])


class TestLegacyMigration(unittest.TestCase):

  def tearDown(self):
    if hasattr(self, "_path") and os.path.exists(self._path):
      os.unlink(self._path)

  def test_no_legacy_returns_none(self):
    settings, self._path = _fresh_settings()
    self.assertIsNone(migrate_legacy(settings))

  def test_grouped_layout_migrates(self):
    settings, self._path = _fresh_settings()
    settings.setValue('Tripwire/url', 'https://tw.example')
    settings.setValue('Tripwire/user', 'bob')
    settings.setValue('Tripwire/pass', 'hunter2')
    settings.setValue('Tripwire/evescout_enabled', 'true')

    migrated = migrate_legacy(settings)

    self.assertIsNotNone(migrated)
    self.assertEqual(len(migrated), 2)
    tw = migrated[0]
    self.assertEqual(tw.type, TYPE_TRIPWIRE)
    self.assertEqual(tw.url, 'https://tw.example')
    self.assertEqual(tw.user, 'bob')
    self.assertEqual(tw.password, 'hunter2')
    self.assertTrue(tw.enabled)

    es = migrated[1]
    self.assertEqual(es.type, TYPE_EVESCOUT)
    self.assertTrue(es.enabled)

    for key in ('Tripwire/url', 'Tripwire/user', 'Tripwire/pass', 'Tripwire/evescout_enabled'):
      self.assertFalse(settings.contains(key), f"{key} should be removed")

    settings.sync()
    reloaded = load_configs(settings)
    self.assertEqual(reloaded, migrated)

  def test_flat_layout_migrates(self):
    settings, self._path = _fresh_settings()
    settings.setValue('MainWindow/tripwire_url', 'https://tw.example')
    settings.setValue('MainWindow/tripwire_user', 'alice')
    settings.setValue('MainWindow/tripwire_pass', 'secret')
    settings.setValue('MainWindow/evescout_enable', 'false')

    migrated = migrate_legacy(settings)

    self.assertIsNotNone(migrated)
    self.assertEqual(migrated[0].user, 'alice')
    self.assertFalse(migrated[1].enabled)

  def test_migration_with_empty_url_keeps_only_evescout(self):
    settings, self._path = _fresh_settings()
    settings.setValue('Tripwire/evescout_enabled', 'true')
    settings.setValue('Tripwire/url', '')

    migrated = migrate_legacy(settings)
    self.assertIsNotNone(migrated)
    self.assertEqual(len(migrated), 1)
    self.assertEqual(migrated[0].type, TYPE_EVESCOUT)
    self.assertTrue(migrated[0].enabled)


class TestDefaults(unittest.TestCase):

  def test_default_configs_have_both_types(self):
    configs = default_configs()
    types = {c.type for c in configs}
    self.assertIn(TYPE_TRIPWIRE, types)
    self.assertIn(TYPE_EVESCOUT, types)


if __name__ == '__main__':
  unittest.main()
