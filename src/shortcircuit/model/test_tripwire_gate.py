"""Test GATE wormhole support in Tripwire integration

This test verifies that GATE type wormholes from Tripwire are properly
recognized and added to the solar map for route calculations.
"""

from datetime import datetime
from unittest.mock import Mock, patch
from shortcircuit.model.tripwire import Tripwire
from shortcircuit.model.solarmap import SolarMap, ConnectionType
from shortcircuit.model.evedb import EveDb, WormholeSize, WormholeTimespan, WormholeMassspan


def test_gate_wormhole_is_processed():
    """Test that GATE type wormholes are not skipped and are processed as stable connections"""
    # Create a Tripwire instance and mock the login
    with patch('shortcircuit.model.tripwire.requests') as mock_requests:
        mock_session = Mock()
        mock_session.post.return_value.status_code = 200
        mock_requests.session.return_value = mock_session
        tripwire = Tripwire("test_user", "test_pass", "http://test.url")
    
    # Create a mock chain with a GATE type wormhole
    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    mock_chain = {
        'wormholes': {
            '1': {
                'type': 'GATE',
                'initialID': '100',
                'secondaryID': '200',
                'parent': None,
                'life': 'critical',  # GATE wormholes should ignore this
                'mass': 'critical'   # GATE wormholes should ignore this
            }
        },
        'signatures': {
            '100': {
                'systemID': '30000142',  # Jita
                'signatureID': 'ABC-123',
                'modifiedTime': current_time
            },
            '200': {
                'systemID': '30002187',  # Dodixie
                'signatureID': 'DEF-456',
                'modifiedTime': current_time
            }
        }
    }
    
    # Create a mock solar_map to track calls
    solar_map = Mock(spec=SolarMap)
    solar_map.add_connection = Mock()
    
    # Mock the eve_db methods
    tripwire.eve_db = Mock(spec=EveDb)
    tripwire.eve_db.get_whsize_by_code.return_value = WormholeSize.UNKNOWN
    tripwire.eve_db.get_whsize_by_system.return_value = WormholeSize.LARGE
    
    # Mock the get_chain method to return success and set the chain
    tripwire.chain = mock_chain
    with patch.object(tripwire, 'get_chain', return_value=True):
        # Call augment_map
        result = tripwire.augment_map(solar_map)
    
    # Verify the GATE wormhole was processed (not skipped)
    assert result == 1, f"Expected 1 connection to be added, got {result}"
    assert solar_map.add_connection.called, "add_connection should have been called"
    
    # Verify the connection parameters
    call_args = solar_map.add_connection.call_args[0]
    system_from = call_args[0]
    system_to = call_args[1]
    connection_type = call_args[2]
    wh_info = call_args[3]
    
    assert system_from == 30000142, "System from should be Jita"
    assert system_to == 30002187, "System to should be Dodixie"
    assert connection_type == ConnectionType.WORMHOLE, "Should be added as WORMHOLE type"
    
    # Check the wormhole info array
    [sig_in, code_in, sig_out, code_out, wh_size, wh_life, wh_mass, time_elapsed] = wh_info
    
    assert sig_in == 'ABC----', "Signature in should be formatted as ABC----"
    assert code_in == 'GATE', "Wormhole code should be GATE"
    assert sig_out == 'DEF----', "Signature out should be formatted as DEF----"
    assert code_out == 'GATE', "Wormhole code out should be GATE (both sides are GATE)"
    assert wh_life == WormholeTimespan.STABLE, "GATE wormholes should have STABLE timespan (permanent)"
    assert wh_mass == WormholeMassspan.STABLE, "GATE wormholes should have STABLE massspan (permanent)"
    assert wh_size == WormholeSize.UNKNOWN, "GATE wormholes should have UNKNOWN size (permanent connections don't have size restrictions)"


def test_regular_wormhole_respects_life_and_mass():
    """Test that regular wormholes still respect their life and mass properties"""
    with patch('shortcircuit.model.tripwire.requests') as mock_requests:
        mock_session = Mock()
        mock_session.post.return_value.status_code = 200
        mock_requests.session.return_value = mock_session
        tripwire = Tripwire("test_user", "test_pass", "http://test.url")
    
    # Create a mock chain with a regular critical wormhole
    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    mock_chain = {
        'wormholes': {
            '1': {
                'type': 'C140',
                'initialID': '100',
                'secondaryID': '200',
                'parent': None,
                'life': 'critical',
                'mass': 'destab'
            }
        },
        'signatures': {
            '100': {
                'systemID': '30000142',
                'signatureID': 'GHI-789',
                'modifiedTime': current_time
            },
            '200': {
                'systemID': '30002187',
                'signatureID': 'JKL-012',
                'modifiedTime': current_time
            }
        }
    }
    
    # Create a mock solar_map
    solar_map = Mock(spec=SolarMap)
    solar_map.add_connection = Mock()
    
    # Mock the eve_db methods
    tripwire.eve_db = Mock(spec=EveDb)
    tripwire.eve_db.get_whsize_by_code.return_value = WormholeSize.SMALL
    tripwire.eve_db.get_whsize_by_system.return_value = WormholeSize.LARGE
    
    # Mock the get_chain method to return success and set the chain
    tripwire.chain = mock_chain
    with patch.object(tripwire, 'get_chain', return_value=True):
        # Call augment_map
        result = tripwire.augment_map(solar_map)
    
    # Verify the regular wormhole was processed
    assert result == 1, f"Expected 1 connection, got {result}"
    
    # Check the wormhole info - should respect the life and mass from the wormhole data
    call_args = solar_map.add_connection.call_args[0]
    wh_info = call_args[3]
    [sig_in, code_in, sig_out, code_out, wh_size, wh_life, wh_mass, time_elapsed] = wh_info
    
    assert code_in == 'C140', "Wormhole type should be C140"
    assert code_out == 'K162', "Wormhole code out should be K162"
    assert wh_life == WormholeTimespan.CRITICAL, "Should have CRITICAL timespan from wormhole data"
    assert wh_mass == WormholeMassspan.DESTAB, "Should have DESTAB massspan from wormhole data"
    assert wh_size == WormholeSize.SMALL, "Size should be determined by wormhole code"


def test_gate_wormhole_in_route_calculation():
    """Test that GATE wormholes are usable in route calculations"""
    eve_db = EveDb()
    solar_map = SolarMap(eve_db)
    
    # Add a GATE wormhole connection (simulating what Tripwire would add)
    solar_map.add_connection(
        eve_db.name2id("Jita"),
        eve_db.name2id("Dodixie"),
        ConnectionType.WORMHOLE,
        [
            "ABC-123",
            "GATE",
            "DEF-456",
            "----",
            WormholeSize.LARGE,
            WormholeTimespan.STABLE,
            WormholeMassspan.STABLE,
            0.5,  # Updated 0.5 hours ago
        ],
    )
    
    # Calculate a route that should use the GATE wormhole
    from shortcircuit.model.evedb import SpaceType
    path = solar_map.shortest_path(
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
    
    # The path should use the GATE wormhole (direct connection)
    assert named_path == ["Jita", "Dodixie"], f"Expected direct path via GATE wormhole, got {named_path}"


def test_connection_failure_returns_negative_one():
    """Test that connection/auth failures return -1 for proper UI error display"""
    with patch('shortcircuit.model.tripwire.requests') as mock_requests:
        mock_session = Mock()
        mock_session.post.return_value.status_code = 200
        mock_requests.session.return_value = mock_session
        tripwire = Tripwire("test_user", "test_pass", "http://test.url")
    
    # Mock get_chain to return False (connection failure)
    solar_map = Mock(spec=SolarMap)
    
    with patch.object(tripwire, 'get_chain', return_value=False):
        result = tripwire.augment_map(solar_map)
    
    # Should return -1 on failure for UI error display
    assert result == -1, f"Expected -1 on connection failure, got {result}"
    assert not solar_map.add_connection.called, "No connections should be added on failure"


def test_connection_failure_preserves_existing_chain():
    """Test that connection failures preserve existing navigation data"""
    with patch('shortcircuit.model.tripwire.requests') as mock_requests:
        mock_session = Mock()
        mock_session.post.return_value.status_code = 200
        mock_requests.session.return_value = mock_session
        tripwire = Tripwire("test_user", "test_pass", "http://test.url")
    
    # Set up initial chain data
    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    initial_chain = {
        'esi': {},
        'sync': 'test',
        'signatures': {
            '100': {
                'systemID': '30000142',
                'signatureID': 'ABC-123',
                'modifiedTime': current_time
            }
        },
        'wormholes': {
            '1': {
                'type': 'C140',
                'initialID': '100',
                'secondaryID': '200',
                'parent': None,
                'life': 'stable',
                'mass': 'stable'
            }
        },
        'flares': {'flares': [], 'last_modified': ''},
        'proccessTime': '0.1',
        'discord_integration': False,
    }
    tripwire.chain = initial_chain
    
    # Mock fetch_api_refresh to return None (connection failure)
    with patch.object(tripwire, 'fetch_api_refresh', return_value=None):
        result = tripwire.get_chain()
    
    # Should return False on failure
    assert result is False, "get_chain should return False on connection failure"
    
    # Chain should be preserved (not replaced with empty chain)
    assert tripwire.chain == initial_chain, "Existing chain data should be preserved on connection failure"
    assert len(tripwire.chain['wormholes']) == 1, "Wormhole data should be preserved"
    assert tripwire.chain['sync'] == 'test', "Sync data should be preserved"
