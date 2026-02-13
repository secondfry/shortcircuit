"""Comprehensive tests for Tripwire API integration

Tests the core functionality of Tripwire integration including:
- TypedDict structure validation
- Signature formatting
- Parent/sibling key determination
- Wormhole properties calculation
- Edge cases and validation
"""

from datetime import datetime
from unittest.mock import Mock, patch
import pytest

from shortcircuit.model.tripwire import (
    Tripwire,
    TripwireWormhole,
    TripwireSignature,
    convert_to_int,
)
from shortcircuit.model.solarmap import SolarMap, ConnectionType
from shortcircuit.model.evedb import EveDb, WormholeSize, WormholeTimespan, WormholeMassspan


class TestSignatureFormatting:
    """Test signature ID formatting logic"""
    
    def test_format_null_signature(self):
        """Test that null/None signatures return unknown"""
        assert Tripwire.format_tripwire_signature(None) == Tripwire.SIG_UNKNOWN
    
    def test_format_empty_signature(self):
        """Test that empty string signatures return unknown"""
        assert Tripwire.format_tripwire_signature('') == Tripwire.SIG_UNKNOWN
    
    def test_format_question_marks(self):
        """Test that ??? signatures return unknown"""
        assert Tripwire.format_tripwire_signature('???') == Tripwire.SIG_UNKNOWN
    
    def test_format_normal_signature(self):
        """Test formatting of normal signature like ABC-123"""
        assert Tripwire.format_tripwire_signature('ABC123') == 'ABC-123'
    
    def test_format_lowercase_signature(self):
        """Test that lowercase letters are uppercased"""
        assert Tripwire.format_tripwire_signature('abc123') == 'ABC-123'
    
    def test_format_numeric_prefix_with_letters(self):
        """Test that numeric prefix with letters swaps them (user error correction)"""
        assert Tripwire.format_tripwire_signature('123abc') == 'ABC-123'
    
    def test_format_numeric_only(self):
        """Test that numbers only returns dashes for letters"""
        assert Tripwire.format_tripwire_signature('123') == '----123'
    
    def test_format_partial_signature_letters_only(self):
        """Test signature with only letters (no numbers)"""
        assert Tripwire.format_tripwire_signature('ABC') == 'ABC----'
    
    def test_format_partial_signature_with_non_numeric(self):
        """Test signature with non-numeric suffix"""
        assert Tripwire.format_tripwire_signature('ABCxyz') == 'ABC----'


class TestParentSiblingKeys:
    """Test parent/sibling key determination for wormhole direction"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('shortcircuit.model.tripwire.requests') as mock_requests:
            mock_session = Mock()
            mock_session.post.return_value.status_code = 200
            mock_requests.session.return_value = mock_session
            self.tripwire = Tripwire("test", "test", "http://test.url")
    
    def test_parent_initial(self):
        """Test parent='initial' returns correct keys"""
        wormhole: TripwireWormhole = {
            'id': '1',
            'initialID': '100',
            'secondaryID': '200',
            'type': 'C140',
            'parent': 'initial',
            'life': 'stable',
            'mass': 'stable',
            'maskID': '1'
        }
        parent, sibling = self.tripwire._get_parent_sibling_keys(wormhole)
        assert parent == 'initialID'
        assert sibling == 'secondaryID'
    
    def test_parent_secondary(self):
        """Test parent='secondary' returns swapped keys"""
        wormhole: TripwireWormhole = {
            'id': '1',
            'initialID': '100',
            'secondaryID': '200',
            'type': 'C140',
            'parent': 'secondary',
            'life': 'stable',
            'mass': 'stable',
            'maskID': '1'
        }
        parent, sibling = self.tripwire._get_parent_sibling_keys(wormhole)
        assert parent == 'secondaryID'
        assert sibling == 'initialID'
    
    def test_parent_null(self):
        """Test parent=None defaults to initial"""
        wormhole: TripwireWormhole = {
            'id': '1',
            'initialID': '100',
            'secondaryID': '200',
            'type': 'C140',
            'parent': None,
            'life': 'stable',
            'mass': 'stable',
            'maskID': '1'
        }
        parent, sibling = self.tripwire._get_parent_sibling_keys(wormhole)
        assert parent == 'initialID'
        assert sibling == 'secondaryID'
    
    def test_parent_empty_string(self):
        """Test parent='' defaults to initial"""
        wormhole: TripwireWormhole = {
            'id': '1',
            'initialID': '100',
            'secondaryID': '200',
            'type': 'C140',
            'parent': '',
            'life': 'stable',
            'mass': 'stable',
            'maskID': '1'
        }
        parent, sibling = self.tripwire._get_parent_sibling_keys(wormhole)
        assert parent == 'initialID'
        assert sibling == 'secondaryID'


class TestWormholeProperties:
    """Test wormhole property determination (GATE vs regular)"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('shortcircuit.model.tripwire.requests') as mock_requests:
            mock_session = Mock()
            mock_session.post.return_value.status_code = 200
            mock_requests.session.return_value = mock_session
            self.tripwire = Tripwire("test", "test", "http://test.url")
            self.tripwire.eve_db = Mock(spec=EveDb)
    
    def test_gate_properties(self):
        """Test GATE type returns stable properties"""
        wormhole: TripwireWormhole = {
            'id': '1',
            'initialID': '100',
            'secondaryID': '200',
            'type': 'GATE',
            'parent': None,
            'life': 'critical',  # Should be ignored
            'mass': 'critical',  # Should be ignored
            'maskID': '1'
        }
        
        wh_type_in, wh_type_out, wh_life, wh_mass, wh_size = self.tripwire._get_wormhole_properties(
            wormhole, 30000142, 30002187
        )
        
        assert wh_type_in == 'GATE'
        assert wh_type_out == 'GATE'
        assert wh_life == WormholeTimespan.STABLE
        assert wh_mass == WormholeMassspan.STABLE
        assert wh_size == WormholeSize.UNKNOWN
    
    def test_regular_wormhole_with_type(self):
        """Test regular wormhole with known type"""
        wormhole: TripwireWormhole = {
            'id': '1',
            'initialID': '100',
            'secondaryID': '200',
            'type': 'C140',
            'parent': None,
            'life': 'critical',
            'mass': 'destab',
            'maskID': '1'
        }
        
        self.tripwire.eve_db.get_whsize_by_code.return_value = WormholeSize.SMALL
        
        wh_type_in, wh_type_out, wh_life, wh_mass, wh_size = self.tripwire._get_wormhole_properties(
            wormhole, 30000142, 30002187
        )
        
        assert wh_type_in == 'C140'
        assert wh_type_out == 'K162'
        assert wh_life == WormholeTimespan.CRITICAL
        assert wh_mass == WormholeMassspan.DESTAB
        assert wh_size == WormholeSize.SMALL
    
    def test_regular_wormhole_without_type(self):
        """Test regular wormhole with empty/null type"""
        wormhole: TripwireWormhole = {
            'id': '1',
            'initialID': '100',
            'secondaryID': '200',
            'type': None,
            'parent': None,
            'life': 'stable',
            'mass': 'stable',
            'maskID': '1'
        }
        
        self.tripwire.eve_db.get_whsize_by_code.return_value = WormholeSize.UNKNOWN
        self.tripwire.eve_db.get_whsize_by_system.return_value = WormholeSize.LARGE
        
        wh_type_in, wh_type_out, wh_life, wh_mass, wh_size = self.tripwire._get_wormhole_properties(
            wormhole, 30000142, 31000005
        )
        
        assert wh_type_in == Tripwire.WTYPE_UNKNOWN
        assert wh_type_out == Tripwire.WTYPE_UNKNOWN
        assert wh_life == WormholeTimespan.STABLE
        assert wh_mass == WormholeMassspan.STABLE
        assert wh_size == WormholeSize.LARGE  # From get_whsize_by_system fallback
    
    def test_wormhole_size_fallback(self):
        """Test that invalid size triggers system-based calculation"""
        wormhole: TripwireWormhole = {
            'id': '1',
            'initialID': '100',
            'secondaryID': '200',
            'type': 'UNKNOWN_CODE',
            'parent': None,
            'life': 'stable',
            'mass': 'stable',
            'maskID': '1'
        }
        
        self.tripwire.eve_db.get_whsize_by_code.return_value = WormholeSize.UNKNOWN
        self.tripwire.eve_db.get_whsize_by_system.return_value = WormholeSize.XLARGE
        
        _, _, _, _, wh_size = self.tripwire._get_wormhole_properties(
            wormhole, 30000142, 30002187
        )
        
        assert wh_size == WormholeSize.XLARGE
        self.tripwire.eve_db.get_whsize_by_system.assert_called_once_with(30000142, 30002187)


class TestProcessWormhole:
    """Test the main wormhole processing logic"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('shortcircuit.model.tripwire.requests') as mock_requests:
            mock_session = Mock()
            mock_session.post.return_value.status_code = 200
            mock_requests.session.return_value = mock_session
            self.tripwire = Tripwire("test", "test", "http://test.url")
            self.tripwire.eve_db = Mock(spec=EveDb)
            self.solar_map = Mock(spec=SolarMap)
    
    def test_rejects_empty_signatures_list(self):
        """Test that empty signatures list is rejected"""
        self.tripwire.chain = {
            'signatures': [],  # Empty list instead of dict
            'wormholes': {}
        }
        
        wormhole: TripwireWormhole = {
            'id': '1',
            'initialID': '100',
            'secondaryID': '200',
            'type': 'C140',
            'parent': None,
            'life': 'stable',
            'mass': 'stable',
            'maskID': '1'
        }
        
        result = self.tripwire._process_wormhole(wormhole, self.solar_map)
        assert result is False
    
    def test_rejects_missing_initial_signature(self):
        """Test that missing initial signature is rejected"""
        self.tripwire.chain = {
            'signatures': {
                '200': {'systemID': '30002187', 'signatureID': 'DEF-456', 'modifiedTime': '2026-02-14 12:00:00'}
            },
            'wormholes': {}
        }
        
        wormhole: TripwireWormhole = {
            'id': '1',
            'initialID': '100',  # Missing from signatures
            'secondaryID': '200',
            'type': 'C140',
            'parent': None,
            'life': 'stable',
            'mass': 'stable',
            'maskID': '1'
        }
        
        result = self.tripwire._process_wormhole(wormhole, self.solar_map)
        assert result is False
    
    def test_rejects_missing_secondary_signature(self):
        """Test that missing secondary signature is rejected"""
        self.tripwire.chain = {
            'signatures': {
                '100': {'systemID': '30000142', 'signatureID': 'ABC-123', 'modifiedTime': '2026-02-14 12:00:00'}
            },
            'wormholes': {}
        }
        
        wormhole: TripwireWormhole = {
            'id': '1',
            'initialID': '100',
            'secondaryID': '200',  # Missing from signatures
            'type': 'C140',
            'parent': None,
            'life': 'stable',
            'mass': 'stable',
            'maskID': '1'
        }
        
        result = self.tripwire._process_wormhole(wormhole, self.solar_map)
        assert result is False
    
    def test_rejects_invalid_system_id_zero(self):
        """Test that system ID of 0 is rejected"""
        self.tripwire.chain = {
            'signatures': {
                '100': {'systemID': '0', 'signatureID': 'ABC-123', 'modifiedTime': '2026-02-14 12:00:00'},
                '200': {'systemID': '30002187', 'signatureID': 'DEF-456', 'modifiedTime': '2026-02-14 12:00:00'}
            },
            'wormholes': {}
        }
        
        wormhole: TripwireWormhole = {
            'id': '1',
            'initialID': '100',
            'secondaryID': '200',
            'type': 'C140',
            'parent': None,
            'life': 'stable',
            'mass': 'stable',
            'maskID': '1'
        }
        
        result = self.tripwire._process_wormhole(wormhole, self.solar_map)
        assert result is False
    
    def test_rejects_invalid_system_id_too_low(self):
        """Test that system ID < 10000 is rejected"""
        self.tripwire.chain = {
            'signatures': {
                '100': {'systemID': '1', 'signatureID': 'ABC-123', 'modifiedTime': '2026-02-14 12:00:00'},
                '200': {'systemID': '30002187', 'signatureID': 'DEF-456', 'modifiedTime': '2026-02-14 12:00:00'}
            },
            'wormholes': {}
        }
        
        wormhole: TripwireWormhole = {
            'id': '1',
            'initialID': '100',
            'secondaryID': '200',
            'type': 'C140',
            'parent': None,
            'life': 'stable',
            'mass': 'stable',
            'maskID': '1'
        }
        
        result = self.tripwire._process_wormhole(wormhole, self.solar_map)
        assert result is False
    
    def test_processes_valid_wormhole(self):
        """Test that valid wormhole is processed and added to map"""
        current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.tripwire.chain = {
            'signatures': {
                '100': {'systemID': '30000142', 'signatureID': 'ABC-123', 'modifiedTime': current_time},
                '200': {'systemID': '30002187', 'signatureID': 'DEF-456', 'modifiedTime': current_time}
            },
            'wormholes': {}
        }
        
        wormhole: TripwireWormhole = {
            'id': '1',
            'initialID': '100',
            'secondaryID': '200',
            'type': 'C140',
            'parent': None,
            'life': 'stable',
            'mass': 'stable',
            'maskID': '1'
        }
        
        self.tripwire.eve_db.get_whsize_by_code.return_value = WormholeSize.SMALL
        
        result = self.tripwire._process_wormhole(wormhole, self.solar_map)
        
        assert result is True
        assert self.solar_map.add_connection.called


class TestConvertToInt:
    """Test the convert_to_int utility function"""
    
    def test_valid_string(self):
        """Test conversion of valid numeric string"""
        assert convert_to_int('12345') == 12345
    
    def test_invalid_string(self):
        """Test that invalid string returns 0"""
        assert convert_to_int('abc') == 0
    
    def test_empty_string(self):
        """Test that empty string returns 0"""
        assert convert_to_int('') == 0
    
    def test_none(self):
        """Test that None returns 0"""
        assert convert_to_int(None) == 0
    
    def test_negative_number(self):
        """Test conversion of negative number string"""
        assert convert_to_int('-123') == -123


class TestEmptyChainHandling:
    """Test handling of empty Tripwire responses"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('shortcircuit.model.tripwire.requests') as mock_requests:
            mock_session = Mock()
            mock_session.post.return_value.status_code = 200
            mock_requests.session.return_value = mock_session
            self.tripwire = Tripwire("test", "test", "http://test.url")
    
    def test_empty_wormholes_list(self):
        """Test that empty wormholes list returns 0 connections"""
        self.tripwire.chain = {
            'signatures': [],
            'wormholes': []  # Empty list when no connections
        }
        
        with patch.object(self.tripwire, 'get_chain', return_value=True):
            solar_map = Mock(spec=SolarMap)
            result = self.tripwire.augment_map(solar_map)
        
        assert result == 0
        assert not solar_map.add_connection.called
    
    def test_empty_chain(self):
        """Test that empty normalized chain returns 0"""
        empty_chain = {
            'esi': {},
            'sync': '',
            'signatures': {},
            'wormholes': {},
            'flares': {'flares': [], 'last_modified': ''},
            'proccessTime': '',
            'discord_integration': False,
        }
        self.tripwire.chain = empty_chain

        with patch.object(self.tripwire, 'get_chain', return_value=True):
            solar_map = Mock(spec=SolarMap)
            result = self.tripwire.augment_map(solar_map)

        assert result == 0
