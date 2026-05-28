# State Management

JSON file persistence for IP change detection. The [[polling-loop]] loads [[meridian/updater/models.py#IPState]] from disk at each cycle start and saves after successful updates.

`IPState.has_changed()` compares cached vs current IPs to avoid redundant DNS updates. Default path: `/var/lib/meridian/state.json` (configurable via [[configuration#Environment Variables]]).

## Load and Save

State operations in `meridian/updater/main.py` handle edge cases gracefully.

- [[meridian/updater/main.py#_load_state]] — reads JSON file, returns empty `IPState` if missing or corrupted
- [[meridian/updater/main.py#_save_state]] — creates parent directories if needed, writes indented JSON via `model_dump_json()`
