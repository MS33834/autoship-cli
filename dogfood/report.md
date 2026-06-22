# AutoShip-CLI Dogfooding Report

Python: 3.14.4
CI: True

## Scenarios

### simple_script (单文件 Python 脚本) — PASS

| Command | Exit Code | Expected | Result |
|---------|-----------|----------|--------|
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship init --yes` | 0 | success | PASS |
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship --yes clean` | 0 | success | PASS |
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship plugin list` | 0 | success | PASS |
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship doctor --json` | 0 | success | PASS |
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship verify python --version` | 0 | success | PASS |
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship --dry-run --yes upload --target pypi` | 0 | success | PASS |

### flask_app (Flask Web 项目) — PASS

| Command | Exit Code | Expected | Result |
|---------|-----------|----------|--------|
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship init --yes` | 0 | success | PASS |
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship --yes clean` | 0 | success | PASS |
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship plugin list` | 0 | success | PASS |
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship doctor --json` | 0 | success | PASS |
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship verify python --version` | 0 | success | PASS |
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship --dry-run --yes upload --target pypi` | 0 | success | PASS |

### data_science (数据科学项目（numpy）) — PASS

| Command | Exit Code | Expected | Result |
|---------|-----------|----------|--------|
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship init --yes` | 0 | success | PASS |
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship --yes clean` | 0 | success | PASS |
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship plugin list` | 0 | success | PASS |
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship doctor --json` | 0 | success | PASS |
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship verify python --version` | 0 | success | PASS |
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship --dry-run --yes upload --target pypi` | 0 | success | PASS |

### monorepo (Monorepo 多包项目) — PASS

| Command | Exit Code | Expected | Result |
|---------|-----------|----------|--------|
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship init --yes` | 0 | success | PASS |
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship --yes clean` | 0 | success | PASS |
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship plugin list` | 0 | success | PASS |
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship doctor --json` | 0 | success | PASS |
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship verify python --version` | 0 | success | PASS |
| `/workspace/autoship-cli/.venv/bin/python3 -m autoship --dry-run --yes upload --target pypi` | 0 | success | PASS |

## Summary

- Steps passed: 24 / 24
- Scenarios passed: 4 / 4

## Failures

No unexpected failures.
