from shortcircuit.model.evedb import EveDb, SpaceType, WormholeSize, WormholeMassspan, WormholeTimespan
from shortcircuit.model.solarmap import ConnectionType, SolarMap

# FIXME(secondfry): why is `shortest_path` unstable?
# All tests here should have Jita as destination, not Ikuchi.


def test_dodixie_jita():
  eve_db = EveDb()
  map = SolarMap(eve_db)
  path, _ = map.shortest_path(
    eve_db.name2id("Dodixie"),
    eve_db.name2id("Ikuchi"),
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
  ]


def test_dodixie_jita_but_avoid_tama():
  eve_db = EveDb()
  map = SolarMap(eve_db)
  path, _ = map.shortest_path(
    eve_db.name2id("Dodixie"),
    eve_db.name2id("Ikuchi"),
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
  ]


def test_dodixie_jita_but_avoid_hs():
  eve_db = EveDb()
  map = SolarMap(eve_db)
  path, _ = map.shortest_path(
    eve_db.name2id("Dodixie"),
    eve_db.name2id("Sujarento"),
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
  path, _ = map.shortest_path(
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

  named_path = [eve_db.id2name(x) for x in path]
  assert named_path == [
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
  path, _ = map.shortest_path(
    eve_db.name2id("Dodixie"),
    eve_db.name2id("Ikuchi"),
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
  path, _ = map.shortest_path(
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
      "ignore_eol": True,
      "ignore_masscrit": False,
      "age_threshold": float('inf'),
    },
  )

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
  ]


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
  path, _ = map.shortest_path(
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
  path, _ = map.shortest_path(
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
      "ignore_masscrit": False,
      "age_threshold": 16,
    },
  )

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
  ]


def test_jita_tama_but_avoid_tama():
  eve_db = EveDb()
  map = SolarMap(eve_db)
  path, _ = map.shortest_path(
    eve_db.name2id("Ikuchi"),
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

  named_path = [eve_db.id2name(x) for x in path]
  assert named_path == [
    'Ikuchi',
    'Tunttaras',
    'Nourvukaiken',
    'Tama',
  ]


def test_zarzakh_avoided_as_transit():
  """
  Test that Zarzakh is automatically excluded from routes where it would be
  an intermediate waypoint. Zarzakh has emanation locks that prevent transit.
  See: https://github.com/secondfry/shortcircuit/issues/30
  """
  eve_db = EveDb()
  map = SolarMap(eve_db)
  
  # Create wormhole connections that would make Zarzakh an attractive transit point
  # Jita -> G-0Q86 (wormhole) -> Zarzakh (gate) -> H-PA29 (gate) -> Dodixie (wormhole)
  # Without the Zarzakh exclusion, this would be the shortest path
  map.add_connection(
    eve_db.name2id("Jita"),
    eve_db.name2id("G-0Q86"),
    ConnectionType.WORMHOLE,
    [
      "ABC-123",
      None,
      "DEF-456",
      None,
      WormholeSize.LARGE,
      WormholeTimespan.STABLE,
      WormholeMassspan.STABLE,
      1.0,
    ],
  )
  map.add_connection(
    eve_db.name2id("H-PA29"),
    eve_db.name2id("Dodixie"),
    ConnectionType.WORMHOLE,
    [
      "GHI-789",
      None,
      "JKL-012",
      None,
      WormholeSize.LARGE,
      WormholeTimespan.STABLE,
      WormholeMassspan.STABLE,
      1.0,
    ],
  )
  
  path, _ = map.shortest_path(
    eve_db.name2id("Jita"),
    eve_db.name2id("Dodixie"),
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

  named_path = [eve_db.id2name(x) for x in path]
  # Verify Zarzakh is not in the path as an intermediate system
  assert "Zarzakh" not in named_path


def test_zarzakh_as_destination():
  """
  Test that Zarzakh can be used as a destination system.
  Even though it's excluded from transit, players should be able to route TO it.
  See: https://github.com/secondfry/shortcircuit/issues/30
  """
  eve_db = EveDb()
  map = SolarMap(eve_db)
  
  # Add wormhole connection from Ikuchi to G-0Q86
  # This creates a fast path: Ikuchi -> G-0Q86 -> Zarzakh
  map.add_connection(
    eve_db.name2id("Ikuchi"),
    eve_db.name2id("G-0Q86"),
    ConnectionType.WORMHOLE,
    [
      "ABC-123",
      None,
      "DEF-456",
      None,
      WormholeSize.LARGE,
      WormholeTimespan.STABLE,
      WormholeMassspan.STABLE,
      1.0,
    ],
  )
  
  # Route from Ikuchi to Zarzakh
  path, _ = map.shortest_path(
    eve_db.name2id("Ikuchi"),
    eve_db.name2id("Zarzakh"),
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

  named_path = [eve_db.id2name(x) for x in path]
  # Verify the exact path: Ikuchi -> G-0Q86 -> Zarzakh
  assert named_path == ["Ikuchi", "G-0Q86", "Zarzakh"]


def test_zarzakh_as_source():
  """
  Test that Zarzakh can be used as a source system.
  Even though it's excluded from transit, players should be able to route FROM it.
  See: https://github.com/secondfry/shortcircuit/issues/30
  """
  eve_db = EveDb()
  map = SolarMap(eve_db)
  
  # Add wormhole connection from Turnur to Perimeter
  # This creates a fast path: Zarzakh -> Turnur -> Perimeter
  map.add_connection(
    eve_db.name2id("Turnur"),
    eve_db.name2id("Perimeter"),
    ConnectionType.WORMHOLE,
    [
      "ABC-123",
      None,
      "DEF-456",
      None,
      WormholeSize.LARGE,
      WormholeTimespan.STABLE,
      WormholeMassspan.STABLE,
      1.0,
    ],
  )
  
  # Route from Zarzakh to Perimeter
  path, _ = map.shortest_path(
    eve_db.name2id("Zarzakh"),
    eve_db.name2id("Perimeter"),
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

  named_path = [eve_db.id2name(x) for x in path]
  # Verify the exact path: Zarzakh -> Turnur -> Perimeter
  assert named_path == ["Zarzakh", "Turnur", "Perimeter"]


def _wormhole_payload(sig_in="ABC-123", sig_out="DEF-456", time_elapsed=1.0,
                      wh_size=WormholeSize.LARGE, wh_life=WormholeTimespan.STABLE,
                      wh_mass=WormholeMassspan.STABLE):
  return [
    sig_in,
    None,
    sig_out,
    None,
    wh_size,
    wh_life,
    wh_mass,
    time_elapsed,
  ]


def _wormhole_edges(map, a, b):
  """Return the parallel edges on the A→B side of the graph."""
  return map.get_system(a).get_edges(map.get_system(b))


def test_dedup_same_sigs_merges_into_single_edge():
  """
  When two mappers report the same wormhole (matching sig pair on both
  sides), the graph should hold one edge whose sources list is the union of
  both reporters.
  """
  eve_db = EveDb()
  map = SolarMap(eve_db)
  a = eve_db.name2id("Botane")
  b = eve_db.name2id("Ikuchi")

  map.add_connection(a, b, ConnectionType.WORMHOLE, _wormhole_payload(), source_name="Tripwire")
  map.add_connection(a, b, ConnectionType.WORMHOLE, _wormhole_payload(), source_name="Eve Scout")

  edges_fwd = _wormhole_edges(map, a, b)
  edges_back = _wormhole_edges(map, b, a)
  assert len(edges_fwd) == 1
  assert len(edges_back) == 1
  assert edges_fwd[0][1][6] == ["Tripwire", "Eve Scout"]
  assert edges_back[0][1][6] == ["Tripwire", "Eve Scout"]


def test_dedup_same_sigs_fresher_wins_sig_code_size_life_mass():
  """
  When the same wormhole is reported by two mappers with different
  freshness, fresher wins for the time-sensitive fields. Sigs are equal so
  nothing to pick there.
  """
  eve_db = EveDb()
  map = SolarMap(eve_db)
  a = eve_db.name2id("Botane")
  b = eve_db.name2id("Ikuchi")

  map.add_connection(
    a, b, ConnectionType.WORMHOLE,
    _wormhole_payload(time_elapsed=10.0, wh_life=WormholeTimespan.CRITICAL),
    source_name="Stale",
  )
  map.add_connection(
    a, b, ConnectionType.WORMHOLE,
    _wormhole_payload(time_elapsed=1.0, wh_life=WormholeTimespan.STABLE),
    source_name="Fresh",
  )

  edges = _wormhole_edges(map, a, b)
  assert len(edges) == 1
  info = edges[0][1]
  assert info[3] == WormholeTimespan.STABLE  # life from fresher report
  assert info[5] == 1.0
  assert info[6] == ["Stale", "Fresh"]


def test_dedup_different_sigs_creates_parallel_edges():
  """
  Two reports with concrete-but-different sig IDs on both sides are two
  distinct wormholes between the same pair; the graph must hold both as
  parallel edges.
  """
  eve_db = EveDb()
  map = SolarMap(eve_db)
  a = eve_db.name2id("Botane")
  b = eve_db.name2id("Ikuchi")

  map.add_connection(
    a, b, ConnectionType.WORMHOLE,
    _wormhole_payload(sig_in="AAA-111", sig_out="BBB-222", time_elapsed=2.0),
    source_name="Mapper A",
  )
  map.add_connection(
    a, b, ConnectionType.WORMHOLE,
    _wormhole_payload(sig_in="CCC-333", sig_out="DDD-444", time_elapsed=1.0),
    source_name="Mapper B",
  )

  edges_fwd = _wormhole_edges(map, a, b)
  edges_back = _wormhole_edges(map, b, a)
  assert len(edges_fwd) == 2
  assert len(edges_back) == 2
  sigs_fwd = {edge[1][0] for edge in edges_fwd}
  sigs_back = {edge[1][0] for edge in edges_back}
  assert sigs_fwd == {"AAA-111", "CCC-333"}
  assert sigs_back == {"BBB-222", "DDD-444"}
  # each parallel edge lists only its own reporter
  sources_by_sig = {edge[1][0]: edge[1][6] for edge in edges_fwd}
  assert sources_by_sig["AAA-111"] == ["Mapper A"]
  assert sources_by_sig["CCC-333"] == ["Mapper B"]


def test_dedup_one_sided_match_merges_same_wormhole():
  """
  Sigs are unique per system, so a concrete match on *either* side means
  the reports refer to the same wormhole. The other-side disagreement is
  treated as a scan error, fresher wins, and a warning is logged.
  """
  import logging
  eve_db = EveDb()
  map = SolarMap(eve_db)
  a = eve_db.name2id("Botane")
  b = eve_db.name2id("Ikuchi")

  map.add_connection(
    a, b, ConnectionType.WORMHOLE,
    _wormhole_payload(sig_in="ABC-123", sig_out="DEF-456", time_elapsed=2.0),
    source_name="Mapper A",
  )
  with caplog_context(logging.WARNING) as cap:
    map.add_connection(
      a, b, ConnectionType.WORMHOLE,
      _wormhole_payload(sig_in="ABC-123", sig_out="XYZ-999", time_elapsed=1.0),
      source_name="Mapper B",
    )

  edges_fwd = _wormhole_edges(map, a, b)
  assert len(edges_fwd) == 1
  # fresher report wins the disagreeing side
  assert _wormhole_edges(map, b, a)[0][1][0] == "XYZ-999"
  assert edges_fwd[0][1][6] == ["Mapper A", "Mapper B"]
  assert any("disagreeing sigs" in rec.message for rec in cap.records)


def test_dedup_placeholder_sig_upgraded_on_merge():
  """
  When one report has a placeholder sig and another has a concrete value,
  the concrete value should end up stored in the edge regardless of which
  arrived first.
  """
  eve_db = EveDb()
  map = SolarMap(eve_db)
  a = eve_db.name2id("Botane")
  b = eve_db.name2id("Ikuchi")

  map.add_connection(
    a, b, ConnectionType.WORMHOLE,
    _wormhole_payload(sig_in="-------", sig_out="DEF-456", time_elapsed=1.0),
    source_name="Partial",
  )
  map.add_connection(
    a, b, ConnectionType.WORMHOLE,
    _wormhole_payload(sig_in="ABC-123", sig_out="DEF-456", time_elapsed=5.0),
    source_name="Full",
  )

  info = _wormhole_edges(map, a, b)[0][1]
  assert info[0] == "ABC-123"
  assert info[6] == ["Partial", "Full"]


def test_dedup_single_source_still_lists_itself():
  eve_db = EveDb()
  map = SolarMap(eve_db)
  a = eve_db.name2id("Botane")
  b = eve_db.name2id("Ikuchi")

  map.add_connection(a, b, ConnectionType.WORMHOLE, _wormhole_payload(), source_name="Tripwire")

  info = _wormhole_edges(map, a, b)[0][1]
  assert info[6] == ["Tripwire"]


def test_legacy_add_connection_without_source_name():
  eve_db = EveDb()
  map = SolarMap(eve_db)
  a = eve_db.name2id("Botane")
  b = eve_db.name2id("Ikuchi")

  map.add_connection(a, b, ConnectionType.WORMHOLE, _wormhole_payload())

  info = _wormhole_edges(map, a, b)[0][1]
  assert info[6] == []


def test_dijkstra_picks_traversable_parallel_edge():
  """
  When two parallel wormholes exist between the same pair but one is
  size-restricted out of the route, Dijkstra should still traverse via the
  other parallel edge rather than giving up.
  """
  eve_db = EveDb()
  map = SolarMap(eve_db)
  # Two parallel wormholes Botane <-> Ikuchi: one SMALL, one LARGE.
  map.add_connection(
    eve_db.name2id("Botane"), eve_db.name2id("Ikuchi"),
    ConnectionType.WORMHOLE,
    _wormhole_payload(sig_in="SML-111", sig_out="SML-222", wh_size=WormholeSize.SMALL),
    source_name="small mapper",
  )
  map.add_connection(
    eve_db.name2id("Botane"), eve_db.name2id("Ikuchi"),
    ConnectionType.WORMHOLE,
    _wormhole_payload(sig_in="BIG-111", sig_out="BIG-222", wh_size=WormholeSize.LARGE),
    source_name="large mapper",
  )
  # Restrict SMALL; the router must pick the LARGE parallel edge.
  path, edges = map.shortest_path(
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

  named_path = [eve_db.id2name(x) for x in path]
  assert named_path == ['Dodixie', 'Botane', 'Ikuchi', 'Jita']
  # Find the hop Botane → Ikuchi and verify the edge used is the LARGE one.
  botane_idx = named_path.index('Botane')
  fwd_edge, _ = edges[botane_idx]
  assert fwd_edge[1][0] == "BIG-111"


class caplog_context:
  """Tiny context-manager wrapper around pytest's caplog for tests that
  don't want to take caplog as a fixture argument purely for scoping."""
  def __init__(self, level):
    import logging
    self.level = level
    self.records = []
    self._handler = None

  def __enter__(self):
    import logging
    class _ListHandler(logging.Handler):
      def __init__(self, sink):
        super().__init__()
        self._sink = sink
      def emit(self, record):
        self._sink.append(record)
    self._handler = _ListHandler(self.records)
    self._handler.setLevel(self.level)
    logging.getLogger().addHandler(self._handler)
    return self

  def __exit__(self, exc_type, exc, tb):
    import logging
    logging.getLogger().removeHandler(self._handler)
    return False
