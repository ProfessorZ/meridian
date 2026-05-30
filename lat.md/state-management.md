# State Management

JSON file persistence for IP change detection. The [[polling-loop]] loads [[meridian/updater/models.py#IPState]] from disk at each cycle start and saves after successful updates.

`IPState.has_changed()` compares cached vs current IPs to avoid redundant DNS updates. Enhanced with `last_checked` (timestamp of last poll) and `last_error` (for operational visibility). Default path: `/var/lib/meridian/state.json` (configurable via [[configuration#Environment Variables]]).

## Load and Save

State operations in `meridian/updater/main.py` handle edge cases gracefully and follow a **clean-batch** persistence policy:

- [[meridian/updater/main.py#_load_state]] — reads JSON file, returns empty `IPState` if missing or corrupted
- [[meridian/updater/main.py#_save_state]] — creates parent directories if needed, writes indented JSON via `model_dump_json()`

After an IP change is detected, the new state is only written when every `update_record` call for the affected hosts succeeded. Any `ProviderError` leaves the previous state on disk so the failed records will be retried on the next cycle (even without a new public IP change). This is the behavior specified in [[tests#State Management#Persists state only after clean update batch]].
