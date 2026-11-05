from pathlib import Path
p = Path("tests/test_ui_languages.py")
s = p.read_text(encoding="utf-8")
old = '            g = H.new_game(path=p)\n            g.toggle_fullscreen()\n'
new = ('            g = H.new_game(path=p)\n'
       '            # This test checks persistence; avoid changing the real SDL window in headless runs.\n'
       '            g.apply_display = lambda: None\n'
       '            g.toggle_fullscreen()\n')
if s.count(old) != 1:
    raise SystemExit(f"Expected one fullscreen test setup, found {s.count(old)}")
p.write_text(s.replace(old, new), encoding="utf-8", newline="")
