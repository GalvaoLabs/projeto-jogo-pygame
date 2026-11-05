import json
from pathlib import Path
files = [
    ".gitignore", "core/company.py", "core/economy.py", "modes/dashboard.py",
    "modes/office.py", "modes/ui.py", "requirements.txt", "systems/time_system.py",
    "tests/simulate.py", "tests/smoke_ui.py", "tests/test_ui_languages.py",
]
print(json.dumps({name: Path(name).read_text(encoding="utf-8").replace("\r\n", "\n") for name in files}, ensure_ascii=False))
