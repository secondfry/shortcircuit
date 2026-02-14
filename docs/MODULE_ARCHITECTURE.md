# Module Architecture

## Overview

This document describes how the different modules in Short Circuit work together to fetch wormhole connections from external mappers and calculate routes.

## Control Flow for Fetching Wormhole Data

### 1. User Interaction
```
User clicks "Get Tripwire" button in GUI
  ↓
app.py: btn_trip_get_clicked()
```

### 2. Thread Initialization
```
app.py starts worker_thread (separate thread to avoid blocking UI)
  ↓
NavProcessor.process() executes in worker thread
```

### 3. Map Setup
```
NavProcessor.process()
  ↓
navigation.reset_chain() - creates fresh SolarMap
  ↓
navigation.setup_mappers() - configures mapper sources
```

### 4. Mapper Configuration
```
Navigation.setup_mappers()
  ↓
Reads config from app_obj (MainWindow):
  - tripwire_url, tripwire_user, tripwire_password
  - state_evescout["enabled"]
  ↓
Creates mapper instances:
  - Tripwire(user, pass, url, name="Tripwire")
  - EveScout(name="Eve Scout") if enabled
  ↓
Registers each mapper with MapperRegistry
```

### 5. Data Fetching
```
Navigation.augment_map(solar_map)
  ↓
MapperRegistry.augment_map(solar_map)
  ↓
For each registered mapper:
  - Calls mapper.augment_map(solar_map)
  - Tripwire: Logs in, fetches /refresh.php, parses JSON
  - EveScout: Fetches public API, parses JSON
  - Each adds connections to solar_map
  ↓
Returns dict: {"Tripwire": 15, "Eve Scout": 8}
```

### 6. Result Processing
```
NavProcessor receives results
  ↓
Calculates total_connections from all sources
  ↓
If total_connections > 0:
  navigation.solar_map = solar_map (updates the map)
  ↓
Emits finished signal with (tripwire_count, evescout_count)
```

### 7. UI Update
```
app.py receives finished signal
  ↓
worker_thread_done() handler updates:
  - state_tripwire["connections"]
  - state_evescout["connections"]
  - Status bar displays
  - Enables buttons again
```

## Module Responsibilities

### app.py (MainWindow)
- **Role**: Main GUI application window
- **Responsibilities**:
  - User interface and event handling
  - Configuration storage (QSettings)
  - Thread management for background tasks
  - Status display updates
- **Key State**:
  - `tripwire_url`, `tripwire_user`, `tripwire_pass`
  - `state_evescout["enabled"]`
  - `state_tripwire`, `state_evescout` (connection counts, errors)

### navigation.py (Navigation)
- **Role**: Orchestrates wormhole data fetching and pathfinding
- **Responsibilities**:
  - Manages SolarMap instance
  - Configures and manages MapperRegistry
  - Provides pathfinding interface
  - Route formatting and instructions
- **Key Methods**:
  - `setup_mappers()`: Configures mappers from app config
  - `augment_map()`: Fetches from all registered mappers
  - `route()`: Calculates shortest path between systems

### navprocessor.py (NavProcessor)
- **Role**: Worker thread processor for background tasks
- **Responsibilities**:
  - Runs in separate thread to avoid blocking UI
  - Coordinates map fetching workflow
  - Aggregates results from multiple sources
  - Signals completion to main thread
- **Threading**: Runs in `worker_thread`, emits `finished` signal

### mapper_registry.py (MapperRegistry)
- **Role**: Registry for managing multiple mapper sources
- **Responsibilities**:
  - Registers/unregisters mapper sources
  - Iterates through all sources to fetch data
  - Aggregates results from multiple mappers
  - Handles individual source failures gracefully
- **Key Feature**: Allows combining data from multiple Tripwire servers, Eve Scout, etc.

### mapper_base.py (MapperSource)
- **Role**: Abstract base class for mapper implementations
- **Interface**:
  - `augment_map(solar_map)`: Add connections to map, return count
  - `get_name()`: Return human-readable name
  - `validate_config()`: Check if configuration is valid

### tripwire.py (Tripwire)
- **Role**: Tripwire mapper implementation
- **Responsibilities**:
  - Authenticate with Tripwire server
  - Fetch wormhole connection data via /refresh.php
  - Parse Tripwire JSON format
  - Add connections to SolarMap
- **Authentication**: Session-based (POST to /login.php)
- **API**: /refresh.php with system_id parameter

### evescout.py (EveScout)
- **Role**: Eve Scout Thera connections implementation
- **Responsibilities**:
  - Fetch public Thera connection data
  - Parse Eve Scout JSON format
  - Add Thera connections to SolarMap
- **Authentication**: None (public API)
- **API**: https://api.eve-scout.com/v2/public/signatures

### solarmap.py (SolarMap)
- **Role**: Graph representation of Eve solar system map
- **Responsibilities**:
  - Stores systems and connections (gates + wormholes)
  - Implements shortest path algorithm (Dijkstra)
  - Handles connection weights based on security, wormhole size, etc.
  - Applies restrictions (avoid lists, size limits, etc.)

## Data Flow Diagram

```
┌─────────────┐
│   app.py    │  User clicks "Get Tripwire"
│ (MainWindow)│
└──────┬──────┘
       │ starts
       ↓
┌─────────────────┐
│  NavProcessor   │  Worker Thread
│  (QThread)      │
└──────┬──────────┘
       │ calls
       ↓
┌─────────────────┐
│   Navigation    │  Orchestrator
└──────┬──────────┘
       │ uses
       ↓
┌─────────────────┐
│ MapperRegistry  │  Manages sources
└──────┬──────────┘
       │ iterates
       ↓
┌──────────────────────┐
│  MapperSource        │  Interface
│  ├─ Tripwire         │  Implementations
│  └─ EveScout         │
└──────┬───────────────┘
       │ augments
       ↓
┌─────────────────┐
│   SolarMap      │  Graph structure
└─────────────────┘
```

## Configuration Storage

Short Circuit uses QSettings (Qt's configuration system) to store:

- **Tripwire credentials**: `tripwire_url`, `tripwire_user`, `tripwire_pass`
- **Eve Scout enabled**: `evescout_enabled` (boolean)
- **Other settings**: Proxy, restrictions, avoidance lists, etc.

Configuration is:
1. Loaded from QSettings in `app.py.__init__()` → `read_settings()`
2. Stored in MainWindow instance variables
3. Accessed by Navigation through `self.app_obj` reference
4. Saved back to QSettings when changed

## Adding a New Mapper

To add support for a new wormhole mapping tool:

1. **Create mapper class** inheriting from `MapperSource`:
   ```python
   class NewMapper(MapperSource):
       def __init__(self, url, api_key, name="New Mapper"):
           self.url = url
           self.api_key = api_key
           self.name = name
           
       def augment_map(self, solar_map: SolarMap) -> int:
           # Fetch data from API
           # Parse and add connections to solar_map
           # Return connection count or -1 on error
           
       def get_name(self) -> str:
           return self.name
   ```

2. **Update Navigation.setup_mappers()**:
   ```python
   def setup_mappers(self):
       # ... existing code ...
       
       # Add new mapper if configured
       if self.app_obj.newmapper_api_key:
           newmapper = NewMapper(
               url="https://api.newmapper.com",
               api_key=self.app_obj.newmapper_api_key,
               name="New Mapper"
           )
           self.mapper_registry.register(newmapper)
   ```

3. **Add configuration UI** in app.py for the new mapper's settings

4. **Update status display** to show connection count for the new mapper

## Threading Model

- **Main Thread**: UI (app.py, MainWindow)
  - Handles user interaction
  - Updates display
  - Cannot be blocked

- **Worker Thread**: Data fetching (NavProcessor)
  - Runs `NavProcessor.process()`
  - Calls mappers (can block on network I/O)
  - Emits signal when done

This separation ensures the UI remains responsive while fetching data from external mappers.

## Error Handling

- **Individual mapper failures**: MapperRegistry continues with other sources
- **Network errors**: Each mapper returns -1 on failure
- **Authentication errors**: Logged and reported in UI status
- **Invalid data**: Gracefully skipped, logged for debugging

## Future Considerations

### Multiple Tripwire Instances

To support multiple Tripwire servers simultaneously:

1. Store list of Tripwire configurations in QSettings
2. Update Navigation.setup_mappers() to loop through configurations
3. Register multiple Tripwire instances with different names:
   - `Tripwire(user1, pass1, url1, name="Corp Tripwire")`
   - `Tripwire(user2, pass2, url2, name="Alliance Tripwire")`
4. UI would need to manage multiple Tripwire configurations

### Connection Deduplication

Currently, if two mappers provide the same connection, it's added twice. Future enhancement could:
- Track connection source in metadata
- Deduplicate based on (source_system, dest_system, sig_ids)
- Show "confidence" based on multiple sources confirming same connection
