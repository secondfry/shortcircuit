# example_multiple_mappers.py

"""
Example demonstrating how to use multiple mapper sources with Short Circuit.

This example shows how to:
1. Register multiple Tripwire instances
2. Register Eve Scout
3. Combine data from all sources
4. Handle results from each source
"""

from shortcircuit.model.evedb import EveDb
from shortcircuit.model.evescout import EveScout
from shortcircuit.model.mapper_registry import MapperRegistry
from shortcircuit.model.solarmap import SolarMap
from shortcircuit.model.tripwire import Tripwire


def main():
  """
  Example usage of MapperRegistry with multiple sources.
  """
  # Initialize Eve database and solar map
  eve_db = EveDb()
  solar_map = SolarMap(eve_db)
  
  # Create mapper registry
  registry = MapperRegistry()
  
  # Register multiple Tripwire instances
  # Example 1: Corporate Tripwire
  corp_tripwire = Tripwire(
    username="corp_user",
    password="corp_pass",
    url="https://tripwire.corp.example.com",
    name="Corp Tripwire"
  )
  registry.register(corp_tripwire)
  
  # Example 2: Alliance Tripwire
  alliance_tripwire = Tripwire(
    username="alliance_user",
    password="alliance_pass",
    url="https://tripwire.alliance.example.com",
    name="Alliance Tripwire"
  )
  registry.register(alliance_tripwire)
  
  # Example 3: Public Tripwire
  public_tripwire = Tripwire(
    username="public_user",
    password="public_pass",
    url="https://tripwire.eve-apps.com",
    name="Public Tripwire"
  )
  registry.register(public_tripwire)
  
  # Register Eve Scout for Thera connections
  evescout = EveScout(
    url="https://api.eve-scout.com/v2/public/signatures",
    name="Eve Scout Thera"
  )
  registry.register(evescout)
  
  # Augment the map from all registered sources
  print(f"Registered {registry.get_source_count()} mapper sources:")
  for source in registry.get_sources():
    print(f"  - {source.get_name()}")
  
  print("\nFetching connections from all sources...")
  results = registry.augment_map(solar_map)
  
  # Display results
  print("\nResults:")
  total_connections = 0
  for source_name, connection_count in results.items():
    if connection_count >= 0:
      print(f"  {source_name}: {connection_count} connections")
      total_connections += connection_count
    else:
      print(f"  {source_name}: Failed to fetch connections")
  
  print(f"\nTotal connections: {total_connections}")
  
  # The solar map now contains all connections from all sources
  # You can use it for pathfinding as normal


def example_with_error_handling():
  """
  Example showing error handling for mapper sources.
  """
  eve_db = EveDb()
  solar_map = SolarMap(eve_db)
  registry = MapperRegistry()
  
  # Register sources with validation
  sources_to_register = [
    Tripwire("user1", "pass1", "https://tripwire1.com", "Tripwire 1"),
    Tripwire("user2", "pass2", "https://tripwire2.com", "Tripwire 2"),
    EveScout(),
  ]
  
  for source in sources_to_register:
    is_valid, error = source.validate_config()
    if is_valid:
      registry.register(source)
      print(f"Registered: {source.get_name()}")
    else:
      print(f"Skipped {source.get_name()}: {error}")
  
  # Fetch from all registered sources
  results = registry.augment_map(solar_map)
  
  # Check for failures
  failed_sources = [name for name, count in results.items() if count < 0]
  if failed_sources:
    print(f"\nWarning: Failed to fetch from: {', '.join(failed_sources)}")
  
  # Continue with successful sources
  successful_count = sum(count for count in results.values() if count >= 0)
  print(f"Successfully fetched {successful_count} total connections")


def example_dynamic_sources():
  """
  Example showing how to dynamically add/remove sources.
  """
  registry = MapperRegistry()
  
  # Start with one source
  source1 = Tripwire("user1", "pass1", "https://tripwire1.com", "Source 1")
  registry.register(source1)
  print(f"Sources: {registry.get_source_count()}")  # Output: 1
  
  # Add more sources
  source2 = EveScout(name="Source 2")
  registry.register(source2)
  print(f"Sources: {registry.get_source_count()}")  # Output: 2
  
  # Remove a source
  registry.unregister(source1)
  print(f"Sources: {registry.get_source_count()}")  # Output: 1
  
  # Clear all sources
  registry.clear()
  print(f"Sources: {registry.get_source_count()}")  # Output: 0


def example_configuration_inspection():
  """
  Example showing how to inspect mapper configurations.
  """
  registry = MapperRegistry()
  
  # Register sources
  registry.register(Tripwire("user", "pass", "https://tripwire.com", "My Tripwire"))
  registry.register(EveScout())
  
  # Inspect all sources
  for source in registry.get_sources():
    print(f"\nMapper: {source.get_name()}")
    config = source.get_config()
    for key, value in config.items():
      print(f"  {key}: {value}")


if __name__ == '__main__':
  print("=" * 60)
  print("Example: Multiple Mapper Sources")
  print("=" * 60)
  # Uncomment to run examples:
  # main()
  # example_with_error_handling()
  # example_dynamic_sources()
  # example_configuration_inspection()
  
  print("\nNote: This is a demonstration file.")
  print("Update credentials and URLs before running.")
