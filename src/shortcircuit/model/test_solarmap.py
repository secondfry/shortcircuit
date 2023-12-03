from shortcircuit.model.evedb import EveDb, SpaceType, WormholeSize, WormholeMassspan, WormholeTimespan
from shortcircuit.model.solarmap import ConnectionType, SolarMap


def test_dodixie_jita():
  eve_db = EveDb()
  map = SolarMap(eve_db)
  path = map.shortest_path(
    eve_db.name2id("Dodixie"),
    eve_db.name2id("Jita"),
    {
      "avoidance_list": [],
      "security_prio": {
        SpaceType.HS: 1,
        SpaceType.LS: 1,
        SpaceType.NS: 1,
        SpaceType.WH: 1,
      }
    },
  )

  # FIXME(secondfry): why is it unstable?
  named_path = [eve_db.id2name(x) for x in path]
  assert named_path == [
    'Dodixie',
    'Botane',
    'Ourapheh',
    'Chantrousse',
    'Tierijev',
    'Tannolen',
    'Onatoh',
    'Sujarento',
    'Tama',
    'Nourvukaiken',
    'Tunttaras',
    'Ikuchi',
    'Jita',
  ] or named_path == [
    'Dodixie',
    'Botane',
    'Ourapheh',
    'Chantrousse',
    'Tierijev',
    'Tannolen',
    'Onatoh',
    'Sujarento',
    'Tama',
    'Nourvukaiken',
    'Tunttaras',
    'Niyabainen',
    'Jita',
  ]


def test_dodixie_jita_but_avoid_tama():
  eve_db = EveDb()
  map = SolarMap(eve_db)
  path = map.shortest_path(
    eve_db.name2id("Dodixie"),
    eve_db.name2id("Jita"),
    {
      "avoidance_list": [
        eve_db.name2id("Tama"),
      ],
      "security_prio": {
        SpaceType.HS: 1,
        SpaceType.LS: 1,
        SpaceType.NS: 1,
        SpaceType.WH: 1,
      }
    },
  )

  # FIXME(secondfry): why is it unstable?
  named_path = [eve_db.id2name(x) for x in path]
  assert named_path == [
    'Dodixie',
    'Botane',
    'Ourapheh',
    'Manarq',
    'Tar',
    'Tekaima',
    'Tarta',
    'Vecamia',
    'Cleyd',
    'Lor',
    'Ahbazon',
    'Hykkota',
    'Ansila',
    'Ikuchi',
    'Jita',
  ] or named_path == [
    'Dodixie',
    'Vylade',
    'Balle',
    'Du Annes',
    'Pettinck',
    'Auberulle',
    'Unel',
    'Chainelant',
    'Dodenvale',
    'Olettiers',
    'Ambeke',
    'Faurent',
    'Iyen-Oursta',
    'Perimeter',
    'Jita',
  ]


def test_dodixie_jita_but_avoid_hs():
  eve_db = EveDb()
  map = SolarMap(eve_db)
  path = map.shortest_path(
    eve_db.name2id("Dodixie"),
    eve_db.name2id("Jita"),
    {
      "avoidance_list": [],
      "security_prio": {
        SpaceType.HS: 100,
        SpaceType.LS: 1,
        SpaceType.NS: 1,
        SpaceType.WH: 1,
      }
    },
  )

  # FIXME(secondfry): why is it unstable?
  named_path = [eve_db.id2name(x) for x in path]
  assert named_path == [
    'Dodixie',
    'Botane',
    'Erme',
    'Villore',
    'Old Man Star',
    'Heydieles',
    'Fliet',
    'Deven',
    'Nagamanen',
    'Sujarento',
    'Tama',
    'Nourvukaiken',
    'Tunttaras',
    'Ikuchi',
    'Jita',
  ] or named_path == [
    'Dodixie',
    'Botane',
    'Erme',
    'Villore',
    'Old Man Star',
    'Heydieles',
    'Fliet',
    'Deven',
    'Nagamanen',
    'Sujarento',
    'Tama',
    'Nourvukaiken',
    'Tunttaras',
    'Niyabainen',
    'Jita',
  ]


def test_wh_botane_ikuchi():
  eve_db = EveDb()
  map = SolarMap(eve_db)
  map.add_connection(
    eve_db.name2id("Botane"),
    eve_db.name2id("Ikuchi"),
    ConnectionType.WORMHOLE,
    [
      "ABC-123",
      None,
      "DEF-456",
      None,
      WormholeSize.SMALL,
      WormholeTimespan.CRITICAL,
      WormholeMassspan.CRITICAL,
      42.21,
    ],
  )
  path = map.shortest_path(
    eve_db.name2id("Dodixie"),
    eve_db.name2id("Jita"),
    {
      "size_restriction": {
        WormholeSize.SMALL: False,
        WormholeSize.MEDIUM: False,
        WormholeSize.LARGE: False,
        WormholeSize.XLARGE: False,
      },
      "avoidance_list": [],
      "security_prio": {
        SpaceType.HS: 1,
        SpaceType.LS: 1,
        SpaceType.NS: 1,
        SpaceType.WH: 1,
      },
      "ignore_eol": False,
      "ignore_masscrit": False,
      "age_threshold": float('inf'),
    },
  )
  assert [eve_db.id2name(x) for x in path] == [
    'Dodixie',
    'Botane',
    'Ikuchi',
    'Jita',
  ]


def test_wh_botane_ikuchi_but_medium():
  eve_db = EveDb()
  map = SolarMap(eve_db)
  map.add_connection(
    eve_db.name2id("Botane"),
    eve_db.name2id("Ikuchi"),
    ConnectionType.WORMHOLE,
    [
      "ABC-123",
      "Q063",
      "DEF-456",
      "K162",
      WormholeSize.SMALL,
      WormholeTimespan.CRITICAL,
      WormholeMassspan.CRITICAL,
      42.21,
    ],
  )
  path = map.shortest_path(
    eve_db.name2id("Dodixie"),
    eve_db.name2id("Jita"),
    {
      "size_restriction": {
        WormholeSize.SMALL: True,
        WormholeSize.MEDIUM: False,
        WormholeSize.LARGE: False,
        WormholeSize.XLARGE: False,
      },
      "avoidance_list": [],
      "security_prio": {
        SpaceType.HS: 1,
        SpaceType.LS: 1,
        SpaceType.NS: 1,
        SpaceType.WH: 1,
      },
      "ignore_eol": False,
      "ignore_masscrit": False,
      "age_threshold": float('inf'),
    },
  )
  assert [eve_db.id2name(x) for x in path] == [
    'Dodixie',
    'Botane',
    'Ourapheh',
    'Chantrousse',
    'Tierijev',
    'Tannolen',
    'Onatoh',
    'Sujarento',
    'Tama',
    'Nourvukaiken',
    'Tunttaras',
    'Ikuchi',
    'Jita',
  ]


def test_wh_botane_ikuchi_but_not_eol():
  eve_db = EveDb()
  map = SolarMap(eve_db)
  map.add_connection(
    eve_db.name2id("Botane"),
    eve_db.name2id("Ikuchi"),
    ConnectionType.WORMHOLE,
    [
      "ABC-123",
      None,
      "DEF-456",
      None,
      WormholeSize.SMALL,
      WormholeTimespan.CRITICAL,
      WormholeMassspan.CRITICAL,
      42.21,
    ],
  )
  path = map.shortest_path(
    eve_db.name2id("Dodixie"),
    eve_db.name2id("Jita"),
    {
      "size_restriction": {
        WormholeSize.SMALL: False,
        WormholeSize.MEDIUM: False,
        WormholeSize.LARGE: False,
        WormholeSize.XLARGE: False,
      },
      "avoidance_list": [],
      "security_prio": {
        SpaceType.HS: 1,
        SpaceType.LS: 1,
        SpaceType.NS: 1,
        SpaceType.WH: 1,
      },
      "ignore_eol": True,
      "ignore_masscrit": False,
      "age_threshold": float('inf'),
    },
  )
  assert [eve_db.id2name(x) for x in path] == [
    'Dodixie',
    'Botane',
    'Ourapheh',
    'Chantrousse',
    'Tierijev',
    'Tannolen',
    'Onatoh',
    'Sujarento',
    'Tama',
    'Nourvukaiken',
    'Tunttaras',
    'Ikuchi',
    'Jita',
  ]


# FIXME pathing is not stable
# Route should be from Dodixie to Jita.
# That test run fine locally, but fails in GitHub CI.
def test_wh_botane_ikuchi_but_not_crit():
  eve_db = EveDb()
  map = SolarMap(eve_db)
  map.add_connection(
    eve_db.name2id("Botane"),
    eve_db.name2id("Ikuchi"),
    ConnectionType.WORMHOLE,
    [
      "ABC-123",
      None,
      "DEF-456",
      None,
      WormholeSize.SMALL,
      WormholeTimespan.CRITICAL,
      WormholeMassspan.CRITICAL,
      42.21,
    ],
  )
  path = map.shortest_path(
    eve_db.name2id("Dodixie"),
    eve_db.name2id("Ikuchi"),
    {
      "size_restriction": {
        WormholeSize.SMALL: False,
        WormholeSize.MEDIUM: False,
        WormholeSize.LARGE: False,
        WormholeSize.XLARGE: False,
      },
      "avoidance_list": [],
      "security_prio": {
        SpaceType.HS: 1,
        SpaceType.LS: 1,
        SpaceType.NS: 1,
        SpaceType.WH: 1,
      },
      "ignore_eol": False,
      "ignore_masscrit": True,
      "age_threshold": float('inf'),
    },
  )
  assert [eve_db.id2name(x) for x in path] == [
    'Dodixie',
    'Botane',
    'Ourapheh',
    'Chantrousse',
    'Tierijev',
    'Tannolen',
    'Onatoh',
    'Sujarento',
    'Tama',
    'Nourvukaiken',
    'Tunttaras',
    'Ikuchi',
  ]


def test_wh_botane_ikuchi_but_not_stale():
  eve_db = EveDb()
  map = SolarMap(eve_db)
  map.add_connection(
    eve_db.name2id("Botane"),
    eve_db.name2id("Ikuchi"),
    ConnectionType.WORMHOLE,
    [
      "ABC-123",
      None,
      "DEF-456",
      None,
      WormholeSize.SMALL,
      WormholeTimespan.CRITICAL,
      WormholeMassspan.CRITICAL,
      42.21,
    ],
  )
  path = map.shortest_path(
    eve_db.name2id("Dodixie"),
    eve_db.name2id("Jita"),
    {
      "size_restriction": {
        WormholeSize.SMALL: False,
        WormholeSize.MEDIUM: False,
        WormholeSize.LARGE: False,
        WormholeSize.XLARGE: False,
      },
      "avoidance_list": [],
      "security_prio": {
        SpaceType.HS: 1,
        SpaceType.LS: 1,
        SpaceType.NS: 1,
        SpaceType.WH: 1,
      },
      "ignore_eol": False,
      "ignore_masscrit": False,
      "age_threshold": 16,
    },
  )

  # FIXME(secondfry): why is it unstable?
  named_path = [eve_db.id2name(x) for x in path]
  assert named_path == [
    'Dodixie',
    'Botane',
    'Ourapheh',
    'Chantrousse',
    'Tierijev',
    'Tannolen',
    'Onatoh',
    'Sujarento',
    'Tama',
    'Nourvukaiken',
    'Tunttaras',
    'Ikuchi',
    'Jita',
  ] or named_path == [
    'Dodixie',
    'Botane',
    'Ourapheh',
    'Chantrousse',
    'Tierijev',
    'Tannolen',
    'Onatoh',
    'Sujarento',
    'Tama',
    'Nourvukaiken',
    'Tunttaras',
    'Niyabainen',
    'Jita',
  ]


def test_jita_tama_but_avoid_tama():
  eve_db = EveDb()
  map = SolarMap(eve_db)
  path = map.shortest_path(
    eve_db.name2id("Jita"),
    eve_db.name2id("Tama"),
    {
      "avoidance_list": [
        eve_db.name2id("Tama"),
      ],
      "security_prio": {
        SpaceType.HS: 1,
        SpaceType.LS: 1,
        SpaceType.NS: 1,
        SpaceType.WH: 1,
      },
    },
  )

  # FIXME(secondfry): why is it unstable?
  named_path = [eve_db.id2name(x) for x in path]
  assert named_path == [
    'Jita',
    'Ikuchi',
    'Tunttaras',
    'Nourvukaiken',
    'Tama',
  ] or named_path == [
    'Jita',
    'Niyabainen',
    'Tunttaras',
    'Nourvukaiken',
    'Tama',
  ]
