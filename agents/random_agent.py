import random
from move import Move


class RandomAgent:
    """
    Reference agent - moves randomly to a free adjacent cell.
    If no free cell is available, stays in place.
    """

    def __init__(self, maze, prize_positions, agent_position, opponent_position, max_turns):
        pass

    def next_move(self, maze, prize_positions, agent_position, opponent_position):
        row, col = agent_position
        num_rows = len(maze)
        num_cols = len(maze[0])

        candidates = []
        for move, (dr, dc) in [
            (Move.UP,    (-1,  0)),
            (Move.DOWN,  ( 1,  0)),
            (Move.RIGHT, ( 0,  1)),
            (Move.LEFT,  ( 0, -1)),
        ]:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < num_rows and 0 <= new_col < num_cols:
                if maze[new_row][new_col] != '#':
                    candidates.append(move)

        return random.choice(candidates) if candidates else Move.STAY
