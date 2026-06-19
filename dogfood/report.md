# AutoShip-CLI Dogfooding Report

Python: 3.14.4

## Scenarios

### simple_script (单文件 Python 脚本)

| Command | Exit Code | Notes |
|---------|-----------|-------|
| `init` | 0 | OK |
| `clean` | 0 | OK<br><small>reformatted /tmp/tmpuztttm9o/hello.py

All done! ✨ 🍰 ✨
1 file reformatted.</small> |
| `plugin_list` | 0 | OK |
| `commit` | 0 | OK |
| `verify` | 0 | OK |

### flask_app (Flask Web 项目)

| Command | Exit Code | Notes |
|---------|-----------|-------|
| `init` | 0 | OK |
| `clean` | 0 | OK<br><small>reformatted /tmp/tmpjsa13f1c/app.py

All done! ✨ 🍰 ✨
1 file reformatted.</small> |
| `plugin_list` | 0 | OK |

### data_science (数据科学项目（numpy）)

| Command | Exit Code | Notes |
|---------|-----------|-------|
| `init` | 0 | OK |
| `clean` | 0 | OK<br><small>reformatted /tmp/tmpooci1_i7/analysis.py

All done! ✨ 🍰 ✨
1 file reformatted.</small> |

### monorepo (Monorepo 多包项目)

| Command | Exit Code | Notes |
|---------|-----------|-------|
| `init` | 0 | OK |
| `clean` | 0 | OK<br><small>reformatted /tmp/tmpouxf0p1q/packages/pkg_b/__init__.py

All done! ✨ 🍰 ✨
1 file reformatted, 1 file left unchanged.</small> |

## Known Limitations / Issues Found

- No unexpected failures in non-AI commands.
- `commit` and `verify` require a configured model backend; failures without one are expected.

## Recommendations

- Continue dogfooding with a running local model (Ollama/LM Studio) for `commit`/`verify` paths.
- `autoship doctor` has been implemented and now diagnoses missing model/toolchain dependencies.
