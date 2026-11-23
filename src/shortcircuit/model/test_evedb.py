from shortcircuit.model.evedb import EveDb, SpaceType, WormholeSize


def test_dodixie():
  eve_db = EveDb()
  assert eve_db.name2id("Dodixie") == 30002659


def test_jita():
  eve_db = EveDb()
  assert eve_db.name2id("Jita") == 30000142


def test_tama():
  eve_db = EveDb()
  assert eve_db.name2id("Tama") == 30002813


def test_sentinel():
  eve_db = EveDb()
  assert eve_db.name2id("J055520 [Sentinel]") == 31000001


def test_system_type_known_space():
  eve_db = EveDb()
  assert eve_db.system_type(eve_db.name2id("Jita")) == SpaceType.HS
  assert eve_db.system_type(eve_db.name2id("Tama")) == SpaceType.LS
  assert eve_db.system_type(eve_db.name2id("1DQ1-A")) == SpaceType.NS


def test_system_type_pochven_and_zarzakh_are_nullsec():
  eve_db = EveDb()
  assert eve_db.system_type(eve_db.name2id("Kino")) == SpaceType.NS
  assert eve_db.system_type(eve_db.name2id("Zarzakh")) == SpaceType.NS


def test_system_type_wormhole_space():
  eve_db = EveDb()
  assert eve_db.system_type(eve_db.name2id("Thera")) == SpaceType.WH
  assert eve_db.system_type(eve_db.name2id("J055520 [Sentinel]")) == SpaceType.WH
  anoikis = [
    sid for sid, desc in eve_db.system_desc.items()
    if desc['class'].startswith('C')
  ]
  assert anoikis
  assert all(eve_db.system_type(sid) == SpaceType.WH for sid in anoikis)


def test_system_type_every_gate_destination_has_one():
  # SolarMap asks for the space type of every system a gate leads to, and
  # system_type() raises for classes it has no answer for. If an SDE update
  # adds gates into some new kind of space, this fails before routing does.
  eve_db = EveDb()
  for _, dest in eve_db.gates:
    eve_db.system_type(dest)


def _size(a, b):
  eve_db = EveDb()
  return eve_db.get_whsize_by_system(eve_db.name2id(a), eve_db.name2id(b))


C2 = "J164417"
C5 = "J152820"
C6 = "J104859"


def test_whsize_nullsec_highsec_pairs():
  assert _size("HED-GP", "Amarr") == WormholeSize.XLARGE
  assert _size("Amarr", "HED-GP") == WormholeSize.XLARGE


def test_whsize_pochven_is_at_most_large():
  assert _size("Kino", "HED-GP") == WormholeSize.LARGE
  assert _size("HED-GP", "Kino") == WormholeSize.LARGE
  assert _size("Kino", "Jita") == WormholeSize.LARGE
  assert _size("Kino", C6) == WormholeSize.LARGE
  assert _size("Kino", "Ala") == WormholeSize.MEDIUM


def test_whsize_highsec_to_c5_c6_is_ccp_xlarge():
  # The table holds CCP's sizes; the capital ban is applied by cap_whsize_for_capital_bans.
  assert _size("Jita", C6) == WormholeSize.XLARGE
  assert _size(C6, "Jita") == WormholeSize.XLARGE
  assert _size("Jita", C5) == WormholeSize.XLARGE
  assert _size("HED-GP", C6) == WormholeSize.XLARGE


def _cap(a, b, size):
  eve_db = EveDb()
  return eve_db.cap_whsize_for_capital_bans(eve_db.name2id(a), eve_db.name2id(b), size)


def test_cap_xlarge_touching_highsec_or_thera():
  for a, b in (("Jita", C5), (C5, "Jita"), ("Thera", "HED-GP"), ("HED-GP", "Thera")):
    assert _cap(a, b, WormholeSize.XLARGE) == WormholeSize.LARGE, (a, b)


def test_cap_leaves_other_holes_alone():
  assert _cap("HED-GP", C5, WormholeSize.XLARGE) == WormholeSize.XLARGE
  assert _cap("Tama", "HED-GP", WormholeSize.XLARGE) == WormholeSize.XLARGE
  for size in (WormholeSize.UNKNOWN, WormholeSize.SMALL, WormholeSize.MEDIUM, WormholeSize.LARGE):
    assert _cap("Jita", "Thera", size) == size


def test_whsize_lowsec_to_c1_c6_is_medium():
  # J492 (62,000 t) links C1-C6 to low-sec, so the smallest regular hole is Medium.
  for wh in (C2, C5, C6):
    assert _size("Tama", wh) == WormholeSize.MEDIUM, wh
    assert _size(wh, "Tama") == WormholeSize.MEDIUM, wh


def test_whsize_nullsec_to_c2_c5_unchanged():
  assert _size("HED-GP", C5) == WormholeSize.XLARGE
  assert _size(C5, "HED-GP") == WormholeSize.XLARGE
  assert _size("HED-GP", C2) == WormholeSize.LARGE
  assert _size(C2, "HED-GP") == WormholeSize.LARGE


def test_whsize_unknown_class_is_unknown():
  eve_db = EveDb()
  missing = 1
  assert eve_db.get_whsize_by_system(missing, eve_db.name2id("Jita")) == WormholeSize.UNKNOWN


def test_whsize_by_code_matches_ccp_jump_mass():
  # Max jump mass (attribute 1385) per CCP's SDE/ESI.
  eve_db = EveDb()
  for code in ("K329", "N290", "O753", "R327"):
    assert eve_db.get_whsize_by_code(code) == WormholeSize.LARGE, code
  for code in ("I078", "J492", "L687", "O546"):
    assert eve_db.get_whsize_by_code(code) == WormholeSize.MEDIUM, code
  for code in ("B041", "B520", "L031", "M164", "V898"):
    assert eve_db.get_whsize_by_code(code) == WormholeSize.XLARGE, code
