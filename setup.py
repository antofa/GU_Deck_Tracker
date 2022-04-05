import sys
from cx_Freeze import setup, Executable

from version import VERSION

# Dependencies are automatically detected, but it might need fine tuning.
# "packages": ["os"] is used as example only
# build_exe_options = {"packages": ["os"], "excludes": ["tkinter"]}
build_exe_options = {}

# base="Win32GUI" should be used only for Windows GUI app
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="GU_Deck_Tracker",
    version="0.1",
    description="GU_Deck_Tracker",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base)],
)
