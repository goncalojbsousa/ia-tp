class BaseViewer:
    """
    Base class for all viewers.
    Subclasses must implement on_turn(state).
    state dict keys:
        maze, pos1, pos2, score1, score2,
        turn, is_agent1_turn, name1, name2
    on_turn returns True to terminate the game early, False otherwise.
    """

    def on_turn(self, state) -> bool:
        raise NotImplementedError

    def close(self):
        pass
