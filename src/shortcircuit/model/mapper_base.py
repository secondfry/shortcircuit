# mapper_base.py

from abc import ABC, abstractmethod
from typing import Optional

from .solarmap import SolarMap


class MapperSource(ABC):
  """
  Abstract base class for wormhole mapper data sources.
  
  This class defines the interface that all mapper sources (Tripwire, Eve Scout, etc.)
  must implement to integrate with Short Circuit. The primary method is augment_map(),
  which adds wormhole connections from the external mapper to the solar map.
  """

  @abstractmethod
  def augment_map(self, solar_map: SolarMap) -> int:
    """
    Augment the solar map with wormhole connections from this mapper source.
    
    Args:
      solar_map: The SolarMap to augment with connections
      
    Returns:
      Number of connections added on success, -1 on failure
    """
    pass

  @abstractmethod
  def get_name(self) -> str:
    """
    Get the human-readable name of this mapper source.
    
    Returns:
      The name of the mapper source (e.g., "Tripwire", "Eve Scout")
    """
    pass

  def validate_config(self) -> tuple[bool, Optional[str]]:
    """
    Validate the configuration of this mapper source.
    
    Returns:
      Tuple of (is_valid, error_message). If valid, error_message is None.
    """
    return True, None

