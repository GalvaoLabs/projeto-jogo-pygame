
import os, site, sys

# First, drop system-sites related paths.
original_sys_path = sys.path[:]
known_paths = set()
for path in {'c:\\users\\migue\\onedrive\\desktop\\projetos de programação\\jogo-py-game\\startup-tycoon\\.venv\\lib\\site-packages', 'c:\\users\\migue\\onedrive\\desktop\\projetos de programação\\jogo-py-game\\startup-tycoon\\.venv'}:
    site.addsitedir(path, known_paths=known_paths)
system_paths = set(
    os.path.normcase(path)
    for path in sys.path[len(original_sys_path):]
)
original_sys_path = [
    path for path in original_sys_path
    if os.path.normcase(path) not in system_paths
]
sys.path = original_sys_path

# Second, add lib directories.
# ensuring .pth file are processed.
for path in ['C:\\Users\\migue\\OneDrive\\Desktop\\Projetos de Programação\\jogo-py-game\\STARTUP-TYCOON\\.tmp\\pip-build-env-muo7emn3\\overlay\\Lib\\site-packages', 'C:\\Users\\migue\\OneDrive\\Desktop\\Projetos de Programação\\jogo-py-game\\STARTUP-TYCOON\\.tmp\\pip-build-env-muo7emn3\\normal\\Lib\\site-packages']:
    assert not path in sys.path
    site.addsitedir(path)
