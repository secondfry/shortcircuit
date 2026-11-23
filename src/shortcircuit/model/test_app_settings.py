# test_app_settings.py
"""The "Wormhole size at least" combo: its saved index and the sizes it blocks."""

from shortcircuit.app import (
  LEGACY_WHSIZE_KEY,
  WHSIZE_KEY,
  read_whsize_index,
  size_restriction_for_index,
)
from shortcircuit.model.evedb import WormholeSize

FREIGHTER, CAPITAL, IGNORE_WORMHOLES = 3, 4, 5


def _allowed(combo_index):
  return {size for size, blocked in size_restriction_for_index(combo_index).items() if not blocked}


def test_freighter_allows_xlarge_and_capital_holes():
  assert _allowed(FREIGHTER) == {WormholeSize.XLARGE, WormholeSize.CAPITAL}


def test_capital_allows_only_capital_holes():
  assert _allowed(CAPITAL) == {WormholeSize.CAPITAL}


def test_ignore_wormholes_blocks_every_size():
  assert _allowed(IGNORE_WORMHOLES) == set()
  assert len(_allowed(0)) == 5


def test_legacy_ignore_wormholes_is_kept(make_settings):
  assert read_whsize_index(make_settings(**{LEGACY_WHSIZE_KEY: 4})) == IGNORE_WORMHOLES


def test_legacy_xlarge_becomes_freighter(make_settings):
  assert read_whsize_index(make_settings(**{LEGACY_WHSIZE_KEY: 3})) == FREIGHTER


def test_new_key_wins_over_legacy(make_settings):
  settings = make_settings(**{LEGACY_WHSIZE_KEY: 4, WHSIZE_KEY: CAPITAL})
  assert read_whsize_index(settings) == CAPITAL


def test_no_saved_index_is_small(make_settings):
  assert read_whsize_index(make_settings()) == 0
