from shortcircuit.model.evedb import EveDb


def test_dodixie():
  eve_db = EveDb()
  assert eve_db.name2id("Dodixie") == 30002659

def test_jita():
  eve_db = EveDb()
  assert eve_db.name2id("Jita") == 30000142

def test_tama():
  eve_db = EveDb()
  assert eve_db.name2id("Tama") == 30002813
