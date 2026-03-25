from move import Move


class SimpleHCAgent:

    def __init__(self, maze, prize_positions, agent_position, opponent_position, max_turns):
        pass

    def next_move(self, maze, prize_positions, agent_position, opponent_position):
        if not prize_positions:
            return Move.STAY

        row, col = agent_position

        def min_prize_distance(r, c):
            return min(abs(p[0] - r) + abs(p[1] - c) for p in prize_positions)

        # Candidate moves: filter out walls
        candidates = [
            (move, min_prize_distance(nr, nc))
            for move, nr, nc in [
                (Move.UP,    row - 1, col),
                (Move.DOWN,  row + 1, col),
                (Move.LEFT,  row,     col - 1),
                (Move.RIGHT, row,     col + 1),
            ]
            if maze[nr][nc] != '#'
        ]

        if not candidates:
            return Move.STAY

        # For each candidate cell, compute distance to its nearest prize
        # and pick the move that minimises it
        return min(candidates, key=lambda x: x[1])[0]