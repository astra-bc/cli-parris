"""Allow running with `python -m cli_parris`."""

from cli_parris.game import main
import curses

curses.wrapper(main)
