# Modular Mapper Architecture

## Overview

Short Circuit now supports consuming wormhole connection data from multiple mapper sources simultaneously. This modular architecture allows you to:

- Use multiple Tripwire servers at once (e.g., corp/alliance + public)
- Combine data from different mapping tools
- Easily add support for new mapping tools as they develop APIs

## Architecture

The modular mapper system consists of three main components:

### 1. MapperSource (Base Class)

`mapper_base.py` defines the interface that all mapper sources must implement:

```python
class MapperSource(ABC):
    @abstractmethod
    def augment_map(self, solar_map: SolarMap) -> int:
        """Add connections to the map. Returns connection count or -1 on error."""
        
    @abstractmethod
    def get_name(self) -> str:
        """Return the mapper instance name."""
        
    @abstractmethod
    def get_config(self) -> Dict[str, str]:
        """Return configuration as a dictionary."""
        
    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate configuration. Returns (is_valid, error_message)."""
```

### 2. MapperRegistry

`mapper_registry.py` manages multiple mapper sources:

```python
registry = MapperRegistry()

# Register sources
registry.register(Tripwire("user1", "pass1", "https://tripwire1.com", "Corp Tripwire"))
registry.register(Tripwire("user2", "pass2", "https://tripwire2.com", "Alliance Tripwire"))
registry.register(EveScout())

# Augment map from all sources
results = registry.augment_map(solar_map)
# Returns: {"Corp Tripwire": 15, "Alliance Tripwire": 23, "Eve Scout": 8}
```

### 3. Mapper Implementations

Each mapper tool has its own implementation:

- **Tripwire** (`tripwire.py`): Supports multiple instances with different URLs/credentials
- **Eve Scout** (`evescout.py`): Public API for Thera connections
- **Template** (`mapper_template.py`): Guide for adding new mappers

## Supported Mappers

### Tripwire

**Status**: Fully supported with multiple instances

**Configuration**:
- URL: Tripwire server URL
- Username: Account username
- Password: Account password
- Name: Instance identifier (e.g., "Corp Tripwire")

**Example**:
```python
tripwire = Tripwire(
    username="your_username",
    password="your_password",
    url="https://tripwire.eve-apps.com",
    name="My Tripwire"
)
```

### Eve Scout

**Status**: Fully supported

**Configuration**:
- URL: API endpoint (default: https://api.eve-scout.com/v2/public/signatures)
- Name: Instance identifier

**Example**:
```python
evescout = EveScout(
    url="https://api.eve-scout.com/v2/public/signatures",
    name="Eve Scout Thera"
)
```

### eve-whmapper

**Status**: Not currently supported - no public API available

**Investigation**: The eve-whmapper project (https://github.com/pfh59/eve-whmapper) is a C# Blazor web application that does not currently expose a public REST API for external consumption. It is designed as a self-hosted web application with internal services but no documented endpoints for retrieving wormhole connection data.

**Future Support**: If eve-whmapper adds an API in the future, support can be easily added by:
1. Creating a new `WHMapper` class that inherits from `MapperSource`
2. Implementing the API client logic in `augment_map()`
3. Following the pattern in `mapper_template.py`

## Adding a New Mapper

To add support for a new wormhole mapping tool:

### Step 1: Create a new mapper class

Copy `mapper_template.py` to a new file (e.g., `mymapper.py`) and rename the class:

```python
from .mapper_base import MapperSource

class MyMapper(MapperSource):
    def __init__(self, url: str, api_key: str, name: str = "My Mapper"):
        self.url = url
        self.api_key = api_key
        self.name = name
        self.eve_db = EveDb()
```

### Step 2: Implement augment_map()

This is where you fetch data from the mapper's API and add connections:

```python
def augment_map(self, solar_map: SolarMap) -> int:
    try:
        # Fetch data from API
        response = requests.get(
            f"{self.url}/api/connections",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        if response.status_code != 200:
            return -1
            
        data = response.json()
        connections = 0
        
        for conn in data['connections']:
            # Extract connection details
            source = conn['source_system_id']
            dest = conn['dest_system_id']
            sig_source = conn['source_sig']
            sig_dest = conn['dest_sig']
            wh_type = conn['wh_type']
            
            # Determine wormhole properties
            wh_size = self.eve_db.get_whsize_by_code(wh_type)
            wh_life = WormholeTimespan.STABLE  # Parse from API
            wh_mass = WormholeMassspan.UNKNOWN  # Parse from API
            time_elapsed = 0.0  # Calculate from timestamp
            
            # Add to map
            solar_map.add_connection(
                source, dest, ConnectionType.WORMHOLE,
                [sig_source, wh_type, sig_dest, 'K162', 
                 wh_size, wh_life, wh_mass, time_elapsed]
            )
            connections += 1
            
        return connections
        
    except Exception as e:
        Logger.error(f"Error fetching from {self.name}: {e}")
        return -1
```

### Step 3: Implement interface methods

```python
def get_name(self) -> str:
    return self.name

def get_config(self) -> Dict[str, str]:
    return {
        'url': self.url,
        'name': self.name,
        'api_key': '***'  # Don't expose secrets
    }

def validate_config(self) -> tuple[bool, Optional[str]]:
    if not self.url:
        return False, "URL is required"
    if not self.api_key:
        return False, "API key is required"
    return True, None
```

### Step 4: Register and use

```python
# Create instance
my_mapper = MyMapper(
    url="https://api.mymapper.com",
    api_key="your_api_key",
    name="My Corp Mapper"
)

# Register with registry
registry = MapperRegistry()
registry.register(my_mapper)

# Augment map
results = registry.augment_map(solar_map)
```

## Configuration Format

Multiple mapper instances can be configured in the settings. Here's an example of the data structure:

```python
mappers = [
    {
        'type': 'tripwire',
        'name': 'Corp Tripwire',
        'url': 'https://tripwire.corp.com',
        'username': 'user1',
        'password': 'pass1',
        'enabled': True
    },
    {
        'type': 'tripwire',
        'name': 'Public Tripwire',
        'url': 'https://tripwire.eve-apps.com',
        'username': 'user2',
        'password': 'pass2',
        'enabled': True
    },
    {
        'type': 'evescout',
        'name': 'Eve Scout',
        'url': 'https://api.eve-scout.com/v2/public/signatures',
        'enabled': True
    }
]
```

## API Requirements for Mapper Tools

For a mapping tool to be compatible with Short Circuit, it needs to provide:

### Minimum Requirements

1. **Read-only API endpoint** that returns wormhole connections
2. **Connection data** including:
   - Source system ID
   - Destination system ID
   - Wormhole type (optional but recommended)
   - Signature IDs (optional but recommended)
   - Connection age/timestamp (optional)
   - Wormhole life status (optional)
   - Wormhole mass status (optional)

### Authentication

The API should support one of:
- Public unauthenticated access (like Eve Scout)
- Username/password authentication (like Tripwire)
- API key/token authentication
- OAuth2 authentication

### Response Format

Any format is acceptable (JSON, XML, etc.) as long as it can be parsed to extract the required connection data.

### Example API Response

```json
{
  "connections": [
    {
      "source_system_id": 30000142,
      "dest_system_id": 31000005,
      "source_signature": "ABC-123",
      "dest_signature": "XYZ-789",
      "wormhole_type": "N110",
      "life_status": "stable",
      "mass_status": "stable",
      "updated_at": "2026-02-14T12:00:00Z"
    }
  ]
}
```

## Benefits

### For Users

- **Aggregate data**: Combine connections from multiple sources for a complete picture
- **Redundancy**: If one mapper is down, others continue to work
- **Flexibility**: Use different mappers for different purposes (corp, alliance, public)
- **Community tools**: Easy to integrate new community mapping tools

### For Developers

- **Clear interface**: `MapperSource` defines exactly what needs to be implemented
- **Template available**: `mapper_template.py` provides a starting point
- **Well-documented**: Extensive documentation and examples
- **Tested pattern**: Tripwire and Eve Scout serve as reference implementations

## Testing

When adding a new mapper, create unit tests following the pattern in:
- `test_tripwire.py`: Tests for Tripwire implementation
- `test_tripwire_gate.py`: Integration tests

Example test structure:

```python
import unittest
from shortcircuit.model.mymapper import MyMapper
from shortcircuit.model.solarmap import SolarMap

class TestMyMapper(unittest.TestCase):
    def test_augment_map(self):
        mapper = MyMapper(url="...", api_key="...")
        solar_map = SolarMap(eve_db)
        
        result = mapper.augment_map(solar_map)
        
        self.assertGreaterEqual(result, 0)
        
    def test_get_name(self):
        mapper = MyMapper(url="...", api_key="...", name="Test")
        self.assertEqual(mapper.get_name(), "Test")
```

## Future Enhancements

Potential improvements to the modular mapper system:

1. **UI for managing multiple sources**: GUI for adding/removing/configuring mappers
2. **Connection deduplication**: Detect and merge duplicate connections from different sources
3. **Source prioritization**: Prefer data from certain sources when conflicts occur
4. **Connection metadata**: Track which source provided each connection
5. **Performance optimization**: Parallel fetching from multiple sources
6. **Rate limiting**: Respect API rate limits for each source
7. **Caching**: Cache mapper responses to reduce API calls

## Questions?

For questions or to propose adding support for a new mapper tool, please:
1. Check if the mapping tool has a public API
2. Review the documentation in this file
3. Look at `mapper_template.py` for implementation guidance
4. Open an issue on GitHub with details about the mapper tool
