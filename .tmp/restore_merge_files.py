from pathlib import Path
import subprocess

files = [
    "core/company.py", "core/economy.py", "modes/dashboard.py", "modes/office.py",
    "modes/ui.py", "systems/time_system.py", "tests/simulate.py", "tests/smoke_ui.py",
]
for name in files:
    current = Path(name).read_text(encoding="utf-8")
    if not any(line.startswith("<<<<<<<") for line in current.splitlines()):
        raise SystemExit(f"Expected merge markers in {name}")
    result = subprocess.run(["git", "show", f"171c480:{name}"], check=True, capture_output=True)
    restored = result.stdout
    if b"<<<<<<<" in restored or b"=======" in restored or b">>>>>>>" in restored:
        raise SystemExit(f"First-parent file still contains merge markers: {name}")
    Path(name).write_bytes(restored)
    print(f"Restored {name} from the translation commit")
