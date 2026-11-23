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


C1 = "J105443"
C2 = "J164417"
C3 = "J160650"
C5 = "J152820"
C6 = "J104859"
C13 = "J000895"
DRIFTER = "J055520 [Sentinel]"


def test_whsize_nullsec_highsec_pairs():
  assert _size("HED-GP", "Amarr") == WormholeSize.XLARGE
  assert _size("Amarr", "HED-GP") == WormholeSize.XLARGE


def test_whsize_pochven_is_at_most_large():
  assert _size("Kino", "HED-GP") == WormholeSize.LARGE
  assert _size("HED-GP", "Kino") == WormholeSize.LARGE
  assert _size("Kino", "Jita") == WormholeSize.LARGE
  assert _size("Kino", C6) == WormholeSize.LARGE
  assert _size("Kino", "Ala") == WormholeSize.MEDIUM


def test_whsize_highsec_to_c5_c6_is_freighter_xlarge():
  # D792, M555, B041, B520: 1,000,000,000 kg, so freighters fit but capitals don't.
  assert _size("Jita", C6) == WormholeSize.XLARGE
  assert _size(C6, "Jita") == WormholeSize.XLARGE
  assert _size("Jita", C5) == WormholeSize.XLARGE


def test_whsize_capital_pairs():
  # N944, S199, H296, V753, V911, W237: 2,000,000,000 kg.
  for a, b in (("Tama", "Turnur"), ("Tama", "HED-GP"), ("HED-GP", "LZ-6SU"), (C5, C5), (C5, C6), (C6, C6)):
    assert _size(a, b) == WormholeSize.CAPITAL, (a, b)
    assert _size(b, a) == WormholeSize.CAPITAL, (a, b)


def test_whsize_thera_pairs():
  # Q063/T458 (Medium) to high-sec; M164, V898, L031, E587 (1,000,000,000 kg) to low/null-sec.
  assert _size("Thera", "Jita") == WormholeSize.MEDIUM
  assert _size("Thera", "Tama") == WormholeSize.XLARGE
  assert _size("HED-GP", "Thera") == WormholeSize.XLARGE


def test_whsize_pairs_without_a_regular_hole_are_unknown():
  pairs = (
    (C1, "Kino"), ("Thera", "Kino"), ("Thera", "Thera"), ("Thera", DRIFTER),
    (DRIFTER, DRIFTER), (DRIFTER, "Kino"),
    (C13, "Jita"), (C13, "Tama"), (C13, DRIFTER), (C13, "Kino"),
  )
  for a, b in pairs:
    assert _size(a, b) == WormholeSize.UNKNOWN, (a, b)
    assert _size(b, a) == WormholeSize.UNKNOWN, (a, b)


def test_whsize_lowsec_to_c1_c6_is_medium():
  # J492 (62,000 t) links C1-C6 to low-sec, so the smallest regular hole is Medium.
  for wh in (C2, C5, C6):
    assert _size("Tama", wh) == WormholeSize.MEDIUM, wh
    assert _size(wh, "Tama") == WormholeSize.MEDIUM, wh


def test_whsize_nullsec_to_c3_c5_c6_is_medium():
  # O883, L614, S804 (62,000 t) spawn in null-sec per Tripwire and Wanderer.
  for wh in (C3, C5, C6):
    assert _size("HED-GP", wh) == WormholeSize.MEDIUM, wh
    assert _size(wh, "HED-GP") == WormholeSize.MEDIUM, wh


def test_whsize_nullsec_to_c2_is_large():
  assert _size("HED-GP", C2) == WormholeSize.LARGE
  assert _size(C2, "HED-GP") == WormholeSize.LARGE


def test_size_matrix_is_symmetric():
  matrix = EveDb.SIZE_MATRIX
  for a, row in matrix.items():
    for b, size in row.items():
      assert matrix[b].get(a) == size, (a, b)


ABYSSAL = 32000001  # AD001: in the SDE, but off the map


def test_is_routable():
  eve_db = EveDb()
  assert eve_db.is_routable(eve_db.name2id("Jita"))
  assert not eve_db.is_routable(1)
  assert not eve_db.is_routable(ABYSSAL)


def test_whsize_unroutable_system_is_unknown():
  eve_db = EveDb()
  for odd in (1, ABYSSAL):
    assert eve_db.get_whsize_by_system(odd, eve_db.name2id("Jita")) == WormholeSize.UNKNOWN


def test_whsize_by_code_matches_ccp_jump_mass():
  # Max jump mass (attribute 1385) per CCP's SDE/ESI.
  eve_db = EveDb()
  for code in ("K329", "N290", "O753", "R327"):
    assert eve_db.get_whsize_by_code(code) == WormholeSize.LARGE, code
  for code in ("I078", "J492", "L687", "O546"):
    assert eve_db.get_whsize_by_code(code) == WormholeSize.MEDIUM, code
  for code in ("A641", "B041", "B449", "B520", "D792", "E587", "L031", "M164", "M555", "R051", "V283", "V898"):
    assert eve_db.get_whsize_by_code(code) == WormholeSize.XLARGE, code
  for code in ("C140", "C248", "C391", "H296", "N432", "N944", "S199", "U319", "V753", "V911", "W237", "Z142"):
    assert eve_db.get_whsize_by_code(code) == WormholeSize.CAPITAL, code
