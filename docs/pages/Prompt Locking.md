# Prompt Locking

Prompt integrity locking helps you detect prompt tampering before prompt content is sent to the LLM.

### Why this exists

Prompt files can be edited accidentally or maliciously. This feature gives you a deterministic check that says:
- "These are the prompt files we trust."
- "These are the exact hashes we expect."

### Mental model

1. `prompts.toml` is the manifest (what to track).
2. `prompts.lock.json` is the lock (path -> sha256 hash).
3. Preflight verification checks all tracked prompt files against the lock at execute start.
4. Include-time verification checks included prompt bytes before include content is parsed/used.

### Schema compatibility

- `prompts.toml` and `prompts.lock.json` carry internal version checks (`version = 1` in v1) so Lime can fail fast on incompatible schema changes.
- The lock also pins `algorithm = "sha256"` to keep hashing deterministic and prevent silent verification drift.

### One-time setup

If you are running from source (without globally installing the `lime` binary), use the Make targets:

```sh
make prompts-init
make prompts-lock
make prompts-check
```

If you are not using `make`, run the equivalent source commands directly:

```sh
uv run python src/main.py prompts init
uv run python src/main.py prompts lock
uv run python src/main.py prompts check
```

This creates:
- `prompts.toml`
- `prompts.lock.json`

### Day-to-day workflow (for contributors)

1. Edit a tracked prompt file under `prompts/` (`.mg` / `.md`).
2. Run `make prompts-check` (it should fail until lock is updated).
3. Run `make prompts-lock` to regenerate hashes.
4. Run `make prompts-check` again (should pass).
5. Commit both the prompt changes and `prompts.lock.json`.

### Runtime behavior

During `execute`, verification is auto-enabled when `prompts.toml` exists.

- No `prompts.toml`: execution continues (feature is opt-in).
- `prompts.toml` exists but lock missing: execution fails (fail-closed).
- Any tracked file hash mismatch: execution fails.
- Include outside trusted `prompts/` root:
  - blocked by default
  - allowed only with `--allow-unverified`
- Missing include file: execution fails.

When verification is enabled, Lime performs a preflight lock check at execute start and still verifies included prompt bytes before include content is parsed.

### Execute flag behavior

- `--verify-prompts`: force verification on (fails if `prompts.toml` or `prompts.lock.json` is invalid/missing).
- `--no-verify-prompts`: force verification off (skip manifest/lock checks for this run).
- `--allow-unverified`: only affects include paths outside trusted `prompts/` root; it permits those includes with a warning.

How they interact:
- Default (`execute` with no verify flag): auto mode, verify only when `prompts.toml` exists.
- `--allow-unverified` only matters when verification is enabled (auto-enabled or `--verify-prompts`).

### Security notes

- This is tamper-evident integrity and change control, not a complete security boundary.
- Trust in `prompts.lock.json` comes from your review process (PR review, protected branches, CI checks).
- Recommended CI gate: run `make prompts-check` (or equivalent direct command) on pull requests.
