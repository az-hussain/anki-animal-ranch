# data/ — Persistence

## save_manager.py — Save/Load
- **Save format version**: v2.
- **What is saved**: `Farm` dict only. `TimeSystem` is NEVER saved.
- **On load**: deserialize `Farm`, then reconstruct `TimeSystem(farm)` from `farm.statistics.total_cards_answered`.
- **Atomic writes**: save writes to a `.tmp` file, then renames to prevent corruption.
- **Backup**: a `.bak` copy of the previous save is kept alongside the main file.

### Migrations
When bumping `SAVE_VERSION`, add a new branch in `_migrate()`:
```python
elif from_version == 2:
    # transform data dict from v2 → v3 format
    data["new_field"] = default_value
    from_version = 3
```
Migrations run sequentially, chaining from the file's version up to `SAVE_VERSION`. Never modify earlier branches.

## account_manager.py — Account & Friends
Manages two separate JSON files (not part of the game save):
- `account.json` — local player profile and credentials.
- `friends_list.json` — cached friends list.

These are read/written independently of `save_manager.py`. Do not mix them with game save data.

## Cloud Sync
Cloud sync is triggered inside `save_game()` after a successful local write. It is fire-and-forget:
- Failures are logged as warnings, not errors.
- No retry logic.
- If latency becomes a problem, move the cloud call to a background thread.
