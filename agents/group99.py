from move import Move


class Group99:

    def __init__(self, maze, prize_positions, agent_position, opponent_position, max_turns):
        """
        Called once at the start of the game.
        Use this method to initialize your agent and perform any pre-computation.

        Parameters:
            maze             : tuple[str, ...] - the maze layout as a tuple of strings.
                               Each string is a row, indexed from top (row 0) to bottom.
                               Each character is a column, indexed from left (col 0) to right.
                               Cell symbols:
                                   '#' - wall (impassable)
                                   '.' - free corridor
                                   '1'-'9', 'A'-'F' - prize with value 1-15
                                   'X' - Player 1 starting position
                                   'Y' - Player 2 starting position

            prize_positions  : dict[(int, int), int] - dictionary mapping (row, col) to prize value.
                               Example: {(1, 3): 4, (2, 7): 10, (5, 2): 4}
                               Prizes already collected are removed from this dictionary.

            agent_position   : (int, int) - your agent's current position as (row, col).
                               At the start of the game this corresponds to your initial position.

            opponent_position: (int, int) - opponent's current position as (row, col).

            max_turns        : int - maximum total number of turns in the game
                               (sum of both agents' turns).
        """
        pass

    def next_move(self, maze, prize_positions, agent_position, opponent_position):
        """
        Called once per turn. Must return one of the five Move enum values.

        Parameters:
            maze             : tuple[str, ...] - current maze state (collected prizes
                               appear as free corridors '.').

            prize_positions  : dict[(int, int), int] - prizes still available on the maze.

            agent_position   : (int, int) - your agent's current position as (row, col).

            opponent_position: (int, int) - opponent's current position as (row, col).

        Returns:
            Move - one of: Move.UP, Move.DOWN, Move.RIGHT, Move.LEFT, Move.STAY

        Notes:
            - Move.UP    decreases the row index by 1.
            - Move.DOWN  increases the row index by 1.
            - Move.RIGHT increases the column index by 1.
            - Move.LEFT  decreases the column index by 1.
            - Moving into a wall is invalid and treated as Move.STAY.
            - Returning None or an invalid value is treated as Move.STAY.
            - Two agents may occupy the same cell simultaneously (no penalty).
            - You may use instance attributes (self.*) to store state between calls.
        """
        return Move.STAY