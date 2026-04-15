# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Short Circuit (formerly Pathfinder) is a PySide2 desktop application that finds the shortest path between Eve Online solar systems, including wormhole connections fetched from third-party mappers (Tripwire, Eve Scout). Python 3.10, packaged with PyInstaller.

## Common Commands

Environment setup (the project uses Pipenv with a local `.venv`):
```bash
pip install pipenv
mkdir .venv
pipenv install --dev
pipenv shell
```

Run the application:
```bash
cd src
python main.py
```

Regenerate Qt UI and resource modules after editing files under `resources/ui/` or `resources/resources.qrc`:
```bash
./generate_gui.sh      # or generate_gui.bat on Windows
```
This runs `pyside2-uic` / `pyside2-rcc` and writes to `src/shortcircuit/view/gui_*.py` and `resources_rc.py`. Do not edit those generated files by hand — edit the `.ui` / `.qrc` source and regenerate.

Run tests (pytest, collocated with source under `src/shortcircuit/model/test_*.py`):
```bash
pipenv run pytest src/shortcircuit/model
pipenv run pytest src/shortcircuit/model/test_tripwire.py          # single file
pipenv run pytest src/shortcircuit/model/test_tripwire.py::TestX   # single test
```

Build standalone binaries:
```bash
./build_win_installer.bat   # Windows, PyInstaller --onefile
./build_mac_installer.sh    # macOS
```

## Architecture

The app follows a three-layer split under `src/shortcircuit/`: `view/` (Qt widgets, mostly generated from `.ui` files), `model/` (domain logic, networking, graph algorithms), and `app.py` as the `MainWindow` glue. Entry point is `src/main.py`.

### Wormhole data fetch pipeline

The control flow from a button click to an updated solar map spans several modules — understanding this chain is important before modifying any piece:

1. `app.py` (`MainWindow`) handles the button click and starts a Qt `worker_thread` so the UI stays responsive.
2. `navprocessor.py` (`NavProcessor`, runs on that worker thread) coordinates the workflow and emits a `finished` signal back to the main thread.
3. `navigation.py` (`Navigation`) owns the `SolarMap`, calls `setup_mappers()` to read config from `app_obj` (the `MainWindow`), and delegates fetching to the registry.
4. `mapper_registry.py` (`MapperRegistry`) iterates over registered `MapperSource` instances, calls `augment_map(solar_map)` on each, aggregates counts, and isolates failures so one broken mapper doesn't kill the others.
5. `mapper_base.py` defines the abstract `MapperSource` interface: `augment_map`, `get_name`, `get_config`, `validate_config`. Every mapper implementation inherits from it.
6. Concrete mappers (`tripwire.py`, `evescout.py`) authenticate if needed, fetch JSON, and call `solar_map.add_connection(...)` for each wormhole.
7. `solarmap.py` (`SolarMap`) is the graph itself — holds systems/connections, runs Dijkstra with weights influenced by security prioritization, wormhole size/life/mass restrictions, and the avoidance list.

The detailed flow and diagrams live in `docs/MODULE_ARCHITECTURE.md`; adding a new mapper is documented in `docs/MAPPER_MODULES.md`.

### Threading rules

UI code runs on the main thread; anything that blocks on network I/O (mappers, ESI calls) must run on a worker thread and communicate back via signals. Do not call mapper or ESI methods directly from UI event handlers.

### ESI and configuration

`model/esi/` wraps the optional Eve Online ESI integration (implicit OAuth flow, 20-minute sessions, used for reading player location and setting in-game destination). Configuration (Tripwire credentials, Eve Scout toggle, proxy, restrictions, avoid list) is persisted via Qt's `QSettings`, loaded in `MainWindow.read_settings()`, and accessed by `Navigation` through its `app_obj` reference.

### Static data

Eve SDE CSVs (`mapSolarSystems.csv`, `mapSolarSystemJumps.csv`, `mapLocationWormholeClasses.csv`) live in `src/database/` and are loaded by `evedb.py`. Refresh them from https://www.fuzzwork.co.uk/dump/latest/ when the SDE updates — see README.

## Conventions

- Python 3.10, 2-space indentation (see existing files).
- Qt-generated files under `view/` are regenerated artifacts — never edit directly.
- Tests live next to the code they test (`test_*.py` in `src/shortcircuit/model/`), not in a separate top-level tests directory.
- Known follow-ups and intentionally deferred work are tracked in `TODO.md` (connection deduplication, multi-instance mapper UI, parallel fetching, caching). Prefer aligning with what's listed there over introducing a parallel plan.

## Commit Message Guidelines

### Focus on the "Why", Not Just the "What"

When writing commit messages, **always explain why the change was made**, not just what was changed. The diff already shows what changed - the commit message should provide context and reasoning.

### The Importance of "Why"

The "why" is often harder to infer than the "what", and it requires proper documentation. Without it, future developers (including your future self) will struggle to understand:

- **Contextual Background**: Why was this change necessary? What problem or feature was being addressed?
- **Decision-Making Process**: What options were considered? Why was this particular solution chosen?
- **Implications and Considerations**: What are the potential impacts or limitations of this change? Were there any trade-offs?

### How NOT to Write Commit Messages

❌ **Bad**: Summarizing the changes
```
Update authentication logic
```

❌ **Bad**: Only linking to a ticket
```
Fix #123
```

The problem: These messages don't explain why the change was necessary. The diff shows what changed - you need to provide the context and reasoning.

✅ **Good**: Explaining the reasoning
```
Fix race condition in authentication flow

Users were occasionally getting logged out unexpectedly during page
navigation. This was caused by the auth token refresh happening
simultaneously with route changes, leading to a race condition where
the old token would sometimes override the refreshed one.

This change ensures token refresh completes before allowing navigation
to proceed, preventing the race condition.
```

### Guidelines

- Don't just link to tickets - that puts all the work on the reader to understand context
- Explain the problem being solved and why this solution was chosen
- Include relevant trade-offs or limitations if applicable
- Write for your future self and other engineers who may need to maintain this code

## Pull Request Description Guidelines

PR descriptions follow the same principles as commit messages: **focus on the "why", not just the "what"**.

### What to Include

1. **Summary**: A concise overview of what the PR accomplishes and why it's needed
2. **Context**: Background information about the problem being solved or feature being added
3. **Approach**: Explanation of the solution chosen and why (especially if there were alternatives)
4. **Trade-offs**: Any known limitations, compromises, or technical debt introduced
5. **Testing**: How the changes were tested and what scenarios were covered
6. **Risks**: Any potential impacts on existing functionality or deployment considerations

### Example

```
Fix race condition in authentication flow

## Summary
Users were occasionally getting logged out unexpectedly during page navigation.
This PR fixes the race condition by ensuring token refresh completes before
navigation proceeds.

## Context
The issue occurred when the auth token refresh was triggered simultaneously
with route changes. The old token would sometimes override the refreshed one,
causing unexpected logouts.

## Approach
Added a mutex to ensure token refresh operations are atomic. Considered using
a queue-based approach but opted for the mutex solution due to its simplicity
and lower overhead.

## Testing
- Added unit tests for concurrent token refresh scenarios
- Manually tested rapid page navigation while token refresh was occurring
- Verified no performance regression with load testing

## Risks
Low risk - the mutex is only held briefly during token operations.
```
