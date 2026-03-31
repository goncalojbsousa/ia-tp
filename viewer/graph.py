import time
from .base import BaseViewer
from .curses_compat import curses

# Delay limits and step (seconds)
_DELAY_MAX  = 1.0
_DELAY_STEP = 0.02
_DELAY_MIN  = 0.02
_DELAY_DEFAULT = 0.1

# Color pair IDs
_CP_WALL    = 1
_CP_FREE    = 2
_CP_PRIZE   = 3
_CP_AGENT1  = 4
_CP_AGENT2  = 5
_CP_BOTH    = 6
_CP_STATUS  = 7
_CP_TITLE   = 8
_CP_KEYS    = 9
_CP_GAMEOVER = 10


def _init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(_CP_WALL,   curses.COLOR_WHITE,   curses.COLOR_BLACK)
    curses.init_pair(_CP_FREE,   curses.COLOR_BLACK,   curses.COLOR_BLACK)
    curses.init_pair(_CP_PRIZE,  curses.COLOR_WHITE,   curses.COLOR_GREEN)
    curses.init_pair(_CP_AGENT1, curses.COLOR_WHITE,   curses.COLOR_MAGENTA)
    curses.init_pair(_CP_AGENT2, curses.COLOR_WHITE,   curses.COLOR_CYAN)
    curses.init_pair(_CP_BOTH,   curses.COLOR_WHITE,   curses.COLOR_RED)
    curses.init_pair(_CP_STATUS, curses.COLOR_YELLOW,  curses.COLOR_BLACK)
    curses.init_pair(_CP_TITLE,  curses.COLOR_CYAN,    curses.COLOR_BLACK)
    curses.init_pair(_CP_KEYS,   curses.COLOR_WHITE,   curses.COLOR_BLACK)
    curses.init_pair(_CP_GAMEOVER, curses.COLOR_RED,    curses.COLOR_BLACK)

class GraphViewer(BaseViewer):
    """
    Curses-based interactive viewer.

    Controls:
        S — start / resume
        P — pause
        N — next step (one turn, only when paused)
        Q — quit
        + — increase delay (slower)
        - — decrease delay (faster)
    """

    def __init__(self):
        self._stdscr  = None
        self._paused  = True   # start paused, wait for S
        self._delay   = _DELAY_DEFAULT
        self._running = True   # set to False on Q

        # State for partial updates
        self._initial_drawn = False  # True after first full draw
        self._prev_pos1     = None   # agent 1 position in previous turn
        self._prev_pos2     = None   # agent 2 position in previous turn
        self._status_col    = None   # column where the status panel starts

        # Initialise curses
        self._stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self._stdscr.keypad(True)
        curses.curs_set(0)
        _init_colors()

        # Draw the initial waiting screen
        self._stdscr.clear()
        h, w = self._stdscr.getmaxyx()
        msg = "Press S to start the game"
        try:
            self._stdscr.addstr(h // 2, max(0, (w - len(msg)) // 2), msg,
                                curses.color_pair(_CP_TITLE) | curses.A_BOLD)
        except curses.error:
            pass
        self._stdscr.refresh()

        # Block until S or Q
        while True:
            key = self._stdscr.getch()
            ch = chr(key).upper() if 0 <= key < 256 else ''
            if ch == 'S':
                self._paused = False
                break
            if ch == 'Q':
                self._running = False
                break

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _cell_render(self, maze, pos, pos1, pos2):
        """Returns (ch, attr) for a maze cell, taking agent positions into account."""
        r, c = pos
        cell = maze[r][c]
        if pos == pos1 == pos2:
            return 'WW', curses.color_pair(_CP_BOTH)
        elif pos == pos1:
            return 'XX', curses.color_pair(_CP_AGENT1) | curses.A_BOLD
        elif pos == pos2:
            return 'YY', curses.color_pair(_CP_AGENT2) | curses.A_BOLD
        elif cell == '#':
            return '██', curses.color_pair(_CP_WALL)
        elif cell == '.':
            return '  ', curses.color_pair(_CP_FREE)
        else:
            return f' {cell}', curses.color_pair(_CP_PRIZE) | curses.A_BOLD

    def _draw_cell(self, scr, maze, pos, pos1, pos2, h, w):
        """Draws a single maze cell to the screen."""
        r, c = pos
        x = c * 2
        if r >= h - 1 or x + 1 >= w:
            return
        ch, attr = self._cell_render(maze, pos, pos1, pos2)
        try:
            scr.addstr(r, x, ch, attr)
        except curses.error:
            pass

    def _draw_panel_border(self, scr, h, w, name1, name2):
        """
        Draws the full panel border and all static text (labels, agent names, key hints).
        Uses title_attr consistently for the entire border.
        """
        sc = self._status_col
        if sc is None or sc >= w:
            return

        title_attr = curses.color_pair(_CP_TITLE) | curses.A_BOLD
        keys_attr  = curses.color_pair(_CP_KEYS)

        def border(row, text):
            if row < h - 1:
                try:
                    scr.addstr(row, sc, text[:w - sc - 1], title_attr)
                except curses.error:
                    pass

        def label(row, dcol, text, attr):
            if row < h - 1 and sc + dcol < w:
                try:
                    scr.addstr(row, sc + dcol, text[:w - sc - dcol - 1], attr)
                except curses.error:
                    pass

        # Full border — title_attr used for every line including side │ characters
        border(0,  "┌─ MAZE GAME ────────────────────┐")
        border(1,  "│                                │")
        border(2,  "│                                │")
        border(3,  "│                                │")
        border(4,  "├────────────────────────────────┤")
        border(5,  "│                                │")
        border(6,  "│                                │")
        border(7,  "│                                │")
        border(8,  "│                                │")
        border(9,  "│                                │")
        border(10, "├────────────────────────────────┤")
        border(11, "│                                │")
        border(12, "│                                │")
        border(13, "│                                │")
        border(14, "│                                │")
        border(15, "│                                │")
        border(16, "└────────────────────────────────┘")

        # Static labels drawn on top of the border interior
        label(5,  3, f"XX {name1:<12}", keys_attr)
        label(8,  3, f"YY {name2:<12}", keys_attr)
        label(11, 3, "S  start / resume",    keys_attr)
        label(12, 3, "P  pause",             keys_attr)
        label(13, 3, "N  next step",         keys_attr)
        label(14, 3, "+  slower   -  faster", keys_attr)
        label(15, 3, "Q  quit",              keys_attr)

    def _draw_panel_values(self, state, scr=None, h=None, w=None):
        """
        Redraws only the dynamic values inside the panel:
        turn, delay, state, score1, move_time1, score2, move_time2.
        """
        if scr is None:
            scr = self._stdscr
        if h is None or w is None:
            h, w = scr.getmaxyx()

        sc = self._status_col
        if sc is None or sc >= w:
            return

        turn       = state['turn']
        score1     = state['score1']
        score2     = state['score2']
        move_time1 = state.get('move_time1', 0.0)
        move_time2 = state.get('move_time2', 0.0)

        status_attr = curses.color_pair(_CP_STATUS)
        paused_attr = curses.color_pair(_CP_AGENT1)
        run_attr    = curses.color_pair(_CP_PRIZE)

        def val(row, dcol, text, attr):
            if row < h - 1 and sc + dcol < w:
                try:
                    scr.addstr(row, sc + dcol, text[:w - sc - dcol - 1], attr)
                except curses.error:
                    pass

        val(1, 3, f"Turn   : {turn:>6}",            status_attr)
        val(2, 3, f"Delay  : {self._delay:4.2f} s",  status_attr)
        state_text = "PAUSED " if self._paused else "RUNNING"
        val(3, 3, f"State  : {state_text}", paused_attr if self._paused else run_attr)

        val(5, 18, f"{score1:>6} points", status_attr)
        val(6, 16, f"{move_time1 * 1000:12.5f} ms", status_attr)

        val(8, 18, f"{score2:>6} points", status_attr)
        val(9, 16, f"{move_time2 * 1000:12.5f} ms", status_attr)

    def _draw_initial(self, state):
        """
        Draws the full maze and the complete status panel (border + content).
        Called only once on the first turn.
        """
        maze  = state['maze']
        pos1  = state['pos1']
        pos2  = state['pos2']
        name1 = state['name1']
        name2 = state['name2']

        scr = self._stdscr
        scr.erase()
        h, w = scr.getmaxyx()

        maze_cols = len(maze[0]) if maze else 0
        self._status_col = maze_cols * 2 + 2

        # Draw full maze
        for r, row in enumerate(maze):
            for c in range(len(row)):
                self._draw_cell(scr, maze, (r, c), pos1, pos2, h, w)

        # Draw static panel structure (border + fixed labels)
        self._draw_panel_border(scr, h, w, name1, name2)

        # Draw dynamic panel values
        self._draw_panel_values(state, scr, h, w)

        scr.refresh()

    def _update(self, state):
        """
        Partial update: redraws only the cells that changed (previous and
        current agent positions) and refreshes the dynamic panel values.
        """
        maze = state['maze']
        pos1 = state['pos1']
        pos2 = state['pos2']

        scr  = self._stdscr
        h, w = scr.getmaxyx()

        # Cells to redraw: previous positions (to erase agents) + new positions
        cells_to_redraw = set()
        if self._prev_pos1 is not None:
            cells_to_redraw.add(self._prev_pos1)
        if self._prev_pos2 is not None:
            cells_to_redraw.add(self._prev_pos2)
        cells_to_redraw.add(pos1)
        cells_to_redraw.add(pos2)

        for pos in cells_to_redraw:
            self._draw_cell(scr, maze, pos, pos1, pos2, h, w)

        # Refresh dynamic panel values only
        self._draw_panel_values(state, scr, h, w)

        scr.refresh()

    def on_game_over(self, state):
        self._draw_panel_values(state)
        sc = self._status_col
        h, w = self._stdscr.getmaxyx()
        if sc is not None and sc < w and 3 < h:
            try:
                self._stdscr.addstr(3, sc + 3, "State  : GAME OVER",
                                    curses.color_pair(_CP_GAMEOVER) | curses.A_BOLD)
            except curses.error:
                pass
        self._stdscr.refresh()
        # Bloquear até Q
        self._stdscr.timeout(-1)
        while True:
            key = self._stdscr.getch()
            if 0 <= key < 256 and chr(key).upper() == 'Q':
                break
            
    # ------------------------------------------------------------------
    # Key handling — returns True if the game should terminate
    # ------------------------------------------------------------------

    def _handle_key(self, key):
        if key < 0:
            return False  # timeout, no key pressed
        ch = chr(key).upper() if 0 <= key < 256 else ''
        if ch == 'Q':
            self._running = False
            return True
        if ch == 'S':
            self._paused = False
        elif ch == 'P':
            self._paused = True
        elif ch in ('+', '='):
            self._delay = min(_DELAY_MAX, self._delay + _DELAY_STEP)
        elif ch == '-':
            self._delay = max(_DELAY_MIN, self._delay - _DELAY_STEP)
        return False

    # ------------------------------------------------------------------
    # BaseViewer interface
    # ------------------------------------------------------------------

    def on_turn(self, state) -> bool:
        if not self._running:
            return True

        if not self._initial_drawn:
            self._draw_initial(state)
            self._initial_drawn = True
        else:
            self._update(state)

        # Save positions for next partial update
        self._prev_pos1 = state['pos1']
        self._prev_pos2 = state['pos2']

        if self._paused:
            # Blocked: wait for S, N, Q, + or -
            self._stdscr.timeout(-1)  # blocking
            while self._paused and self._running:
                key = self._stdscr.getch()
                ch  = chr(key).upper() if 0 <= key < 256 else ''
                if ch == 'N':
                    # Advance exactly one step and stay paused
                    return False
                quit_requested = self._handle_key(key)
                if quit_requested:
                    return True
                # Redraw dynamic values to reflect delay/state changes
                self._draw_panel_values(state)
                self._stdscr.refresh()
        else:
            # Running: wait up to self._delay for a key
            self._stdscr.timeout(int(self._delay * 1000))
            key = self._stdscr.getch()
            if self._handle_key(key):
                return True

        return not self._running

    def close(self):
        if self._stdscr is not None:
            try:
                curses.nocbreak()
                self._stdscr.keypad(False)
                curses.echo()
                curses.endwin()
            except curses.error:
                pass