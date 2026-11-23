# TODO - Short Circuit Future Enhancements

## Mapper System

### Connection Deduplication

- A confidence-style score across mappers is intentionally *not* planned — see WHY-OWNED-SERVICE.md for the rationale (and what would change if Short Circuit became a hosted service).
- `solarmap._merge_one_direction` lets a fresher report's unknown hole type or system-pair (guessed) size overwrite a known, scanned one from another mapper; a guess should not beat a scan.

### Wormhole Size Data

- Thera rows in `EveDb.SIZE_MATRIX` (C12) were left as they were and don't match EVE University: Thera↔high-sec holes (Q063, T458) are 62,000 t (Medium) while the table says Large; Thera↔null-sec are 1,000,000 t, but capitals can't enter Thera.
- Capital bans by destination (high-sec, Thera) should live in routing; then store B520, M164 and V898 (and the high-sec↔C6 and Thera `SIZE_MATRIX` cells) at CCP's X-Large.
- Per-system hole sizes aren't modelled: k-space↔C2–C4 is Large, though Turnur's J377 from C2–C4 is Medium (62,000 t).
- **Undecided:** whether Wanderer's connection `wormhole_type` should be accepted when Short Circuit doesn't recognise the code (the API's example value is "C2", a class, not a hole type) or only known hole codes.

### Multiple Mapper Instance Management

- Per-instance "Test Connection" button (reach out to the server and report auth/HTTP result before saving) — subsumes the credential-test piece of "Configuration Validation" below.
- Reordering / drag-and-drop in the Mappers table.
- Import / export of the mapper list (share configs with corp).

### HTTP Mappers

- Apply the global proxy setting to every HTTP mapper; only Tripwire uses it today (Eve Scout and Wanderer ignore it).
- Log non-200 response bodies: Wanderer returns distinct bodies for an inactive subscription and a bad key, which a bare status code hides.

## UI/UX Improvements

### Configuration Validation

Validation currently happens at mapper instantiation time, after save. Move it forward:
- Validate configuration in the dialog before accepting OK.
- URL format check (scheme, host), optional reachability probe.
- Wanderer API token: reject anything that isn't a UUID (e.g. a pasted instance URL); see the mogglemoss fork, commit 36d62b7.
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

### Stale Documentation

- `docs/MAPPER_MODULES.md` describes a `get_config()` method and a `mapper_template.py` that no longer exist; `AGENTS.md` (step 5 of the fetch pipeline) also lists `get_config` in the `MapperSource` interface, which `mapper_base.py` doesn't have.
- `docs/MODULE_ARCHITECTURE.md` still has legacy single-Tripwire text.
- README's feature list and "how it works" name only Tripwire as a mapper source.

### Testing

- Add integration tests for mapper interactions
- Mock HTTP responses for deterministic testing
- Test error scenarios (network failures, auth failures, invalid data)
- Performance testing with large connection datasets
