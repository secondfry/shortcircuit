from shortcircuit.model.evedb import EveDb, SpaceType


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
