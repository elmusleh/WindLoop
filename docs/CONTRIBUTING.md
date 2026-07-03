# Contributing

## Development Setup

```bash
cd ~/Desktop/cascade-loop
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Before Committing

Run the syntax gate:

```bash
./scripts/check.sh
```

This checks:
- Python syntax (`py_compile`)
- Bash script linting (`shellcheck`, if installed)
- YAML validity
- All `tests/test_*.py` automated tests

### Git Pre-Commit Hook (Optional)

Install hooks so checks run automatically on every commit:

```bash
./scripts/install-hooks.sh
```

This sets `core.hooksPath` to `.githooks/`. To uninstall:

```bash
git config --unset core.hooksPath
```

## Testing

### Automated Tests
```bash
python3 tests/test_simulate_watch.py
python3 tests/test_config_loading.py
python3 tests/test_hot_reload.py
```

### Dry-Run Test
```bash
cascade-loop --dry-run
```
Focuses Windsurf and types a test prompt without submitting.

### Focus Test
```bash
python3 tests/test_focus.py
```
Verifies window detection and typing work on your DE.

### Watch Mode Test
```bash
# In terminal 1, start the loop
cascade-loop --start

# In terminal 2, monitor progress
cascade-loop --watch
```

### Simulate Mode Test (No Windsurf Needed)
```bash
cascade-loop --simulate
cascade-loop --watch
```

### Profile Test
```bash
cascade-loop --list-profiles
cascade-loop --simulate --profile quick-test
```

## Code Style

- Python: PEP 8, type hints where practical
- Bash: `shellcheck` clean
- YAML: 2-space indent

## Adding Features

1. Edit `src/cascade_loop.py`
2. Update `config/config.yaml` if new config keys are needed
3. Add tests in `tests/`
4. Update relevant docs
5. Run `./scripts/check.sh`
6. Update `CHANGELOG.md`

## PR Conventions

- One feature per PR
- Update docs with the code
- Add a line to CHANGELOG.md
- Run `./scripts/check.sh` and ensure it passes
