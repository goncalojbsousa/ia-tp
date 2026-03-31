"""
Compatibility layer for curses on Windows.

The curses library is not natively available on Windows, but there is a third-party package called windows-curses that provides a compatible implementation. This module attempts to import curses and falls back to windows-curses if the import fails.

IN WINDOWS, MAKE SURE TO INSTALL THE WINDOWS-CURSES PACKAGE:
    python -m pip install windows-curses
"""
try:
    import curses
    _ = curses.initscr  # force a real check
except (ImportError, ModuleNotFoundError):
    import windows_curses as curses