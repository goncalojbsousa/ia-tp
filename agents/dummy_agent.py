from move import Move


class DummyAgent:
    """
    Reference agent - always stays in place.
    Used in Phase 1 to validate the agent interface.
    """

    def __init__(self, maze, prize_positions, agent_position, opponent_position, max_turns):
        pass

    def next_move(self, maze, prize_positions, agent_position, opponent_position):
        return Move.STAY
