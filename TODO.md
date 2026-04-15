# TODO - Short Circuit Future Enhancements

## Mapper System

### Connection Deduplication

Currently, if two mappers provide the same connection, it's added twice to the solar map. Future enhancement could:

- Track connection source in metadata
- Deduplicate based on (source_system, dest_system, sig_ids)
- Show "confidence" level based on multiple sources confirming the same connection
- Allow users to see which mappers reported each connection

### Multiple Mapper Instance Management — remaining enhancements

Shipped in the Mappers dialog: add/remove/edit and enable/disable of an arbitrary number of instances, list-based QSettings (JSON blob under `MapperConfigs`), dynamic status-bar summary aggregating all enabled mappers. Still missing:

- Per-instance "Test Connection" button (reach out to the server and report auth/HTTP result before saving) — subsumes the credential-test piece of "Configuration Validation" below.
- Reordering / drag-and-drop in the Mappers table.
- Import / export of the mapper list (share configs with corp).

## UI/UX Improvements

### Configuration Validation

Validation currently happens at mapper instantiation time, after save. Move it forward:
- Validate configuration in the dialog before accepting OK.
- URL format check (scheme, host), optional reachability probe.
- Provide immediate inline feedback rather than silent acceptance + later error in the status bar.

(Live credential testing is tracked as the "Test Connection" bullet under Multiple Mapper Instance Management.)

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
