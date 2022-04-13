import sys
from cx_Freeze import setup, Executable

from version import VERSION

# Dependencies are automatically detected, but it might need fine tuning.
# "packages": ["os"] is used as example only
# build_exe_options = {"packages": ["os"], "excludes": ["lib2to3", "logging", "test", "tkinter", "unittest", "xml", "tkinter"]}
excludes = ["tkinter"]
include_files = [('data/data.json', 'data/data.json'), ('data/opponent.json', 'data/opponent.json'), ('media/logo.ico', 'media/logo.ico'), 'config.txt']
options = {
    'build_exe': {
        'include_msvcr': True,
        'excludes': excludes,
        'include_files': include_files,
    }}

# base="Win32GUI" should be used only for Windows GUI app
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="GU_Deck_Tracker",
    version=VERSION[1:],
    description="GU_Deck_Tracker",
    options=options,
    executables=[Executable('main.py', base=base, icon='./media/logo.ico', targetName=f'GU_Deck_Tracker_{VERSION}.exe')],
)
