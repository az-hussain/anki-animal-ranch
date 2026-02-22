# network/ — Cloud Sync

## supabase_client.py
REST calls to Supabase via `urllib` (no third-party HTTP libraries).

### Key Design Decisions
- **Anon key is hardcoded intentionally.** The Supabase publishable anon key is safe to expose in source — it is a public key with row-level security enforced server-side.
- **All functions return `SyncResult`.** Never raise exceptions for network errors — catch them internally and return a failure `SyncResult`.
- **Calls are synchronous/blocking.** This is acceptable because sync is called from `save_game()`, which is infrequent (triggered by card answers, not on a tight loop).
- **If latency becomes an issue**: move the call to a `QThread` or `threading.Thread` in `save_manager.py`. The function signatures do not need to change.

### SyncResult
```python
@dataclass
class SyncResult:
    success: bool
    error: str | None = None
```
Callers check `result.success` and log `result.error` as a warning on failure. Do not surface network errors to the user.

### Adding a New Endpoint
1. Add a function to `supabase_client.py` that returns `SyncResult`.
2. Catch all exceptions inside the function — never let network errors propagate.
3. Call from `save_manager.py` or `account_manager.py` as appropriate.
