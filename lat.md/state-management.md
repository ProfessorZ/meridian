# State Management

JSON file persistence for IP change detection. The [[polling-loop]] loads `IPState` from disk at each cycle start and saves after successful updates.

`IPState.has_changed()` compares cached vs current IPs to avoid redundant DNS updates. Default path: `/var/lib/meridian/state.json` (configurable via [[configuration]]).

## Load and Save

State operations in `meridian/updater/main.py` handle edge cases gracefully.

- `_load_state(path)` — reads JSON file, returns empty `IPState` if missing or corrupted
- `_save_state(path, state)` — creates parent directories if needed, writes indented JSON
