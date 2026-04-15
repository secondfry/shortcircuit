# mapper_registry.py

from typing import Dict, List, Optional

from .logger import Logger
from .mapper_base import MapperSource
from .solarmap import SolarMap


class MapperRegistry:
  """
  Registry for managing multiple mapper data sources.
  
  This class allows Short Circuit to consume data from multiple mapper instances
  (e.g., multiple Tripwire servers, eve-whmapper instances, etc.) and combine
  them into a single solar map.
  """

  def __init__(self):
    self.sources: List[MapperSource] = []

  def register(self, source: MapperSource):
    """
    Register a new mapper source.
    
    Args:
      source: The mapper source to register
    """
    is_valid, error = source.validate_config()
    if not is_valid:
      Logger.warning(
        f"Mapper source {source.get_name()} has invalid config: {error}"
      )
    self.sources.append(source)
    Logger.info(f"Registered mapper source: {source.get_name()}")

  def unregister(self, source: MapperSource):
    """
    Unregister a mapper source.
    
    Args:
      source: The mapper source to unregister
    """
    if source in self.sources:
      self.sources.remove(source)
      Logger.info(f"Unregistered mapper source: {source.get_name()}")

  def clear(self):
    """
    Clear all registered mapper sources.
    """
    self.sources.clear()
    Logger.info("Cleared all mapper sources")

  def augment_map(self, solar_map: SolarMap) -> Dict[str, int]:
    """
    Augment the solar map with connections from all registered sources.
    
    Args:
      solar_map: The SolarMap to augment
      
    Returns:
      Dictionary mapping source names to connection counts.
      Returns -1 for sources that failed.
    """
    results = {}
    for source in self.sources:
      source_name = source.get_name()
      Logger.info(f"Augmenting map from source: {source_name}")
      try:
        connections = source.augment_map(solar_map)
        results[source_name] = connections
        if connections >= 0:
          Logger.info(
            f"Added {connections} connections from {source_name}"
          )
        else:
          Logger.error(f"Failed to get connections from {source_name}")
      except Exception as e:
        Logger.error(
          f"Exception while augmenting from {source_name}: {e}"
        )
        results[source_name] = -1

    return results

  def get_sources(self) -> List[MapperSource]:
    """
    Get all registered mapper sources.
    
    Returns:
      List of registered mapper sources
    """
    return self.sources.copy()

  def get_source_count(self) -> int:
    """
    Get the number of registered mapper sources.
    
    Returns:
      Number of registered sources
    """
    return len(self.sources)
