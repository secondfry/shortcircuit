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


def test_system_type_pochven_and_zarzakh_weigh_as_nullsec():
  eve_db = EveDb()
  assert eve_db.system_type(eve_db.name2id("Kino")) == SpaceType.NS
  assert eve_db.system_type(eve_db.name2id("Zarzakh")) == SpaceType.NS


def test_gates_only_lead_to_classes_system_type_expects():
  # system_type() lumps every class it doesn't name in with null-sec. If an
  # SDE update adds gates into some new kind of space, decide its weight
  # there instead of letting it silently count as null-sec.
  eve_db = EveDb()
  classes = {eve_db.system_desc[dest]['class'] for _, dest in eve_db.gates}
  assert classes == {'HS', 'LS', 'NS', '▲', 'Z'}
