# TODO - Short Circuit Future Enhancements

## Mapper System

### Connection Deduplication

Currently, if two mappers provide the same connection, it's added twice to the solar map. Future enhancement could:

- Track connection source in metadata
- Deduplicate based on (source_system, dest_system, sig_ids)
- Show "confidence" level based on multiple sources confirming the same connection
- Allow users to see which mappers reported each connection

### Multiple Mapper Instance Management

The architecture supports multiple instances of the same mapper type (e.g., multiple Tripwire servers), but the UI currently only supports configuring one instance of each type.

To fully support multiple instances:

1. **UI Enhancement**: Create a table window interface for managing mapper configurations
   - Add/remove/edit mapper instances
   - Enable/disable individual instances
   - Test connectivity for each instance

2. **Configuration Storage**: Update QSettings to store list of mapper configurations
   - Each configuration includes: type, name, URL, credentials, enabled state
   - Support multiple instances of same mapper type

3. **Status Bar Improvement**: Rethink status bar to dynamically show all active mappers
   - Current implementation hardcodes Tripwire and Eve Scout
   - Should iterate over all registered sources

## UI/UX Improvements

### Dynamic Mapper Status Display

Current status bar shows hardcoded Tripwire and Eve Scout connection counts. Should be refactored to:
- Dynamically display all active mapper sources
- Show connection count per source
- Indicate errors per source
- Update automatically when mappers are added/removed

### Configuration Validation

Current validation happens at mapper instantiation time. Consider:
- Validate configuration in UI before saving
- URL validation (format, reachability)
- Credential validation (test login)
- Provide immediate feedback to users

## Performance

### Parallel Mapper Fetching

Currently mappers are called sequentially. Consider:
- Fetch from all mappers in parallel (ThreadPoolExecutor)
- Timeout per mapper to prevent one slow source blocking others
- Cancel all on user request

### Caching

- Cache mapper responses to reduce API calls
- Respect cache headers from APIs
- Allow manual refresh to bypass cache
- Show age of cached data

## Code Quality

### Mapper Interface Refinement

- Consider removing `validate_config()` from mapper interface
- Move validation closer to UI/QSettings
- Simplify mapper interface to only what's essential

### Testing

- Add integration tests for mapper interactions
- Mock HTTP responses for deterministic testing
- Test error scenarios (network failures, auth failures, invalid data)
- Performance testing with large connection datasets
