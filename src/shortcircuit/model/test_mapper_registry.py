# test_mapper_registry.py

import unittest
from typing import Dict, Optional
from unittest.mock import Mock

from shortcircuit.model.mapper_base import MapperSource
from shortcircuit.model.mapper_registry import MapperRegistry


class MockSolarMap:
  """Mock solar map for testing."""
  pass


class MockMapperSource(MapperSource):
  """Mock mapper source for testing."""

  def __init__(self, name: str, connections_to_return: int = 5):
    self.name = name
    self.connections_to_return = connections_to_return
    self.augment_called = False

  def augment_map(self, solar_map) -> int:
    self.augment_called = True
    return self.connections_to_return

  def get_name(self) -> str:
    return self.name

  def get_config(self) -> Dict[str, str]:
    return {"name": self.name}

  def validate_config(self) -> tuple[bool, Optional[str]]:
    return True, None


class TestMapperRegistry(unittest.TestCase):
  """Test cases for MapperRegistry."""

  def setUp(self):
    """Set up test fixtures."""
    self.registry = MapperRegistry()
    self.solar_map = MockSolarMap()

  def test_register_source(self):
    """Test registering a mapper source."""
    source = MockMapperSource("Test Mapper")
    self.registry.register(source)
    
    self.assertEqual(self.registry.get_source_count(), 1)
    self.assertIn(source, self.registry.get_sources())

  def test_register_multiple_sources(self):
    """Test registering multiple mapper sources."""
    source1 = MockMapperSource("Mapper 1")
    source2 = MockMapperSource("Mapper 2")
    source3 = MockMapperSource("Mapper 3")
    
    self.registry.register(source1)
    self.registry.register(source2)
    self.registry.register(source3)
    
    self.assertEqual(self.registry.get_source_count(), 3)

  def test_unregister_source(self):
    """Test unregistering a mapper source."""
    source1 = MockMapperSource("Mapper 1")
    source2 = MockMapperSource("Mapper 2")
    
    self.registry.register(source1)
    self.registry.register(source2)
    self.assertEqual(self.registry.get_source_count(), 2)
    
    self.registry.unregister(source1)
    self.assertEqual(self.registry.get_source_count(), 1)
    self.assertNotIn(source1, self.registry.get_sources())
    self.assertIn(source2, self.registry.get_sources())

  def test_clear_sources(self):
    """Test clearing all mapper sources."""
    source1 = MockMapperSource("Mapper 1")
    source2 = MockMapperSource("Mapper 2")
    
    self.registry.register(source1)
    self.registry.register(source2)
    self.assertEqual(self.registry.get_source_count(), 2)
    
    self.registry.clear()
    self.assertEqual(self.registry.get_source_count(), 0)

  def test_augment_map_single_source(self):
    """Test augmenting map from a single source."""
    source = MockMapperSource("Test Mapper", connections_to_return=10)
    self.registry.register(source)
    
    results = self.registry.augment_map(self.solar_map)
    
    self.assertTrue(source.augment_called)
    self.assertEqual(results["Test Mapper"], 10)

  def test_augment_map_multiple_sources(self):
    """Test augmenting map from multiple sources."""
    source1 = MockMapperSource("Mapper 1", connections_to_return=5)
    source2 = MockMapperSource("Mapper 2", connections_to_return=8)
    source3 = MockMapperSource("Mapper 3", connections_to_return=12)
    
    self.registry.register(source1)
    self.registry.register(source2)
    self.registry.register(source3)
    
    results = self.registry.augment_map(self.solar_map)
    
    self.assertTrue(source1.augment_called)
    self.assertTrue(source2.augment_called)
    self.assertTrue(source3.augment_called)
    
    self.assertEqual(results["Mapper 1"], 5)
    self.assertEqual(results["Mapper 2"], 8)
    self.assertEqual(results["Mapper 3"], 12)

  def test_augment_map_with_failure(self):
    """Test augmenting map when a source fails."""
    source1 = MockMapperSource("Good Mapper", connections_to_return=5)
    source2 = MockMapperSource("Bad Mapper", connections_to_return=-1)
    source3 = MockMapperSource("Another Good Mapper", connections_to_return=8)
    
    self.registry.register(source1)
    self.registry.register(source2)
    self.registry.register(source3)
    
    results = self.registry.augment_map(self.solar_map)
    
    self.assertEqual(results["Good Mapper"], 5)
    self.assertEqual(results["Bad Mapper"], -1)
    self.assertEqual(results["Another Good Mapper"], 8)

  def test_augment_map_with_exception(self):
    """Test augmenting map when a source raises an exception."""
    class FailingMapperSource(MapperSource):
      def augment_map(self, solar_map) -> int:
        raise RuntimeError("Test exception")
      
      def get_name(self) -> str:
        return "Failing Mapper"
      
      def get_config(self) -> Dict[str, str]:
        return {}
    
    good_source = MockMapperSource("Good Mapper", connections_to_return=5)
    failing_source = FailingMapperSource()
    
    self.registry.register(good_source)
    self.registry.register(failing_source)
    
    results = self.registry.augment_map(self.solar_map)
    
    self.assertEqual(results["Good Mapper"], 5)
    self.assertEqual(results["Failing Mapper"], -1)

  def test_get_sources_returns_copy(self):
    """Test that get_sources returns a copy of the sources list."""
    source = MockMapperSource("Test Mapper")
    self.registry.register(source)
    
    sources = self.registry.get_sources()
    sources.clear()
    
    # Original registry should still have the source
    self.assertEqual(self.registry.get_source_count(), 1)

  def test_empty_registry(self):
    """Test operations on an empty registry."""
    results = self.registry.augment_map(self.solar_map)
    
    self.assertEqual(results, {})
    self.assertEqual(self.registry.get_source_count(), 0)
    self.assertEqual(self.registry.get_sources(), [])


if __name__ == '__main__':
  unittest.main()

