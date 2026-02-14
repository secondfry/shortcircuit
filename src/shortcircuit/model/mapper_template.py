# mapper_template.py

"""
Template for implementing a new mapper source for Short Circuit.

This file serves as a guide for adding support for new wormhole mapping tools
like eve-whmapper or other community mappers.

To add a new mapper:
1. Copy this template to a new file (e.g., whmapper.py)
2. Rename the class to match your mapper (e.g., WHMapper)
3. Implement all abstract methods from MapperSource
4. Add authentication/API logic in __init__ and augment_map
5. Process the mapper's API response to extract connection data
6. Use solar_map.add_connection() to add each wormhole connection

For reference, see tripwire.py and evescout.py for complete examples.
"""

from typing import Dict, Optional

from .evedb import EveDb, WormholeSize, WormholeMassspan, WormholeTimespan
from .logger import Logger
from .mapper_base import MapperSource
from .solarmap import ConnectionType, SolarMap


class MapperTemplate(MapperSource):
  """
  Template for a new mapper source implementation.
  
  Replace this with your mapper's name and description.
  """

  def __init__(
    self,
    url: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    api_key: Optional[str] = None,
    name: str = "Custom Mapper",
  ):
    """
    Initialize the mapper source.
    
    Args:
      url: Base URL of the mapper API
      username: Username for authentication (if needed)
      password: Password for authentication (if needed)
      api_key: API key for authentication (if needed)
      name: Human-readable name for this instance
    """
    self.eve_db = EveDb()
    self.url = url
    self.username = username
    self.password = password
    self.api_key = api_key
    self.name = name
    
    # TODO: Add authentication logic here
    # For example:
    # self.session = self._authenticate()

  def augment_map(self, solar_map: SolarMap) -> int:
    """
    Augment the solar map with connections from this mapper.
    
    This is the main method that fetches data from your mapper's API
    and adds connections to the solar map.
    
    Args:
      solar_map: The SolarMap to augment with connections
      
    Returns:
      Number of connections added on success, -1 on failure
    """
    # TODO: Implement API call to fetch wormhole connections
    # Example:
    # try:
    #   response = requests.get(f"{self.url}/api/connections")
    #   if response.status_code != 200:
    #     Logger.error(f"Failed to fetch from {self.name}")
    #     return -1
    #   
    #   data = response.json()
    #   connections = 0
    #   
    #   for connection in data['connections']:
    #     # Extract connection details
    #     source_system = connection['source_system_id']
    #     dest_system = connection['dest_system_id']
    #     sig_source = connection['source_signature']
    #     sig_dest = connection['dest_signature']
    #     wh_type = connection['wormhole_type']
    #     
    #     # Determine wormhole size
    #     wh_size = self.eve_db.get_whsize_by_code(wh_type)
    #     if not WormholeSize.valid(wh_size):
    #       wh_size = self.eve_db.get_whsize_by_system(source_system, dest_system)
    #     
    #     # Determine wormhole life and mass
    #     wh_life = WormholeTimespan.STABLE  # Parse from API
    #     wh_mass = WormholeMassspan.UNKNOWN  # Parse from API
    #     
    #     # Calculate time elapsed
    #     time_elapsed = 0.0  # Parse from API timestamp
    #     
    #     # Add connection to map
    #     solar_map.add_connection(
    #       source_system,
    #       dest_system,
    #       ConnectionType.WORMHOLE,
    #       [
    #         sig_source,
    #         wh_type,
    #         sig_dest,
    #         'K162',  # Return wormhole type
    #         wh_size,
    #         wh_life,
    #         wh_mass,
    #         time_elapsed,
    #       ],
    #     )
    #     connections += 1
    #   
    #   return connections
    #   
    # except Exception as e:
    #   Logger.error(f"Error fetching from {self.name}: {e}")
    #   return -1
    
    Logger.error("MapperTemplate.augment_map is not implemented")
    return -1

  def get_name(self) -> str:
    """
    Get the name of this mapper instance.
    
    Returns:
      The name of this mapper source
    """
    return self.name

  def get_config(self) -> Dict[str, str]:
    """
    Get the current configuration of this mapper instance.
    
    Returns:
      Dictionary of configuration parameters
    """
    config = {
      'url': self.url,
      'name': self.name,
    }
    if self.username:
      config['username'] = self.username
    if self.api_key:
      config['api_key'] = '***'  # Don't expose the actual key
    return config

  def validate_config(self) -> tuple[bool, Optional[str]]:
    """
    Validate the configuration.
    
    Returns:
      Tuple of (is_valid, error_message)
    """
    if not self.url:
      return False, "URL is required"
    
    # Add additional validation as needed
    # For example:
    # if not self.api_key and not (self.username and self.password):
    #   return False, "Either API key or username/password is required"
    
    return True, None
