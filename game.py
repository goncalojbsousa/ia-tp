from move import Move


# Mapping from Move enum to (row, col) delta
MOVE_DELTAS = {
    Move.UP:    (-1,  0),
    Move.DOWN:  ( 1,  0),
    Move.RIGHT: ( 0,  1),
    Move.LEFT:  ( 0, -1),
    Move.STAY:  ( 0,  0),
}


def load_maze(filepath):
    """
    Loads a maze from a text file.

    Returns:
        maze             : tuple[str, ...] - maze with 'X' and 'Y' replaced by '.'
        agent1_position  : (int, int) - starting position of Player 1 (was 'X')
        agent2_position  : (int, int) - starting position of Player 2 (was 'Y')
        prize_positions  : dict[(int, int), int] - mapping of (row, col) to prize value
        max_turns        : int - read from the first line of the file (see format below)

    File format:
        Line 1 : max_turns (integer)
        Line 2+: maze rows, one per line
    """
    with open(filepath, 'r') as f:
        lines = [line.rstrip('\n') for line in f.readlines()]

    max_turns = int(lines[0])
    raw_rows = lines[1:]

    agent1_position = None
    agent2_position = None
    prize_positions = {}
    processed_rows = []

    for row_idx, row in enumerate(raw_rows):
        processed_row = ''
        for col_idx, cell in enumerate(row):
            if cell == 'X':
                agent1_position = (row_idx, col_idx)
                processed_row += '.'
            elif cell == 'Y':
                agent2_position = (row_idx, col_idx)
                processed_row += '.'
            elif cell in '123456789ABCDEF':
                prize_positions[(row_idx, col_idx)] = int(cell, 16)
                processed_row += cell
            else:
                processed_row += cell
        processed_rows.append(processed_row)

    maze = tuple(processed_rows)
    return maze, agent1_position, agent2_position, prize_positions, max_turns


def _apply_move(maze, position, move):
    """
    Applies a move to a position.
    Returns the new position, or the original position if the move is invalid
    (out of bounds or wall).
    """
    row, col = position
    dr, dc = MOVE_DELTAS.get(move, (0, 0))
    new_row, new_col = row + dr, col + dc

    num_rows = len(maze)
    num_cols = len(maze[0])

    if 0 <= new_row < num_rows and 0 <= new_col < num_cols:
        if maze[new_row][new_col] != '#':
            return (new_row, new_col)

    return position


def _safe_next_move(agent, maze, prize_positions, agent_position, opponent_position):
    """
    Calls agent.next_move() safely.
    Returns Move.STAY if the agent raises an exception, returns None,
    or returns a value that is not a valid Move enum member.
    """
    try:
        result = agent.next_move(maze, prize_positions, agent_position, opponent_position)
        if isinstance(result, Move):
            return result
        return Move.STAY
    except Exception:
        return Move.STAY


def _update_maze(maze, position):
    """
    Removes a prize from the maze at the given position (replaces with '.').
    Returns the updated maze as a tuple of strings.
    """
    row, col = position
    updated_row = maze[row][:col] + '.' + maze[row][col + 1:]
    return maze[:row] + (updated_row,) + maze[row + 1:]


def run_game(agent1, agent2, maze, agent1_position, agent2_position, prize_positions, max_turns):
    """
    Runs a full game between two agents.

    Agent 1 always takes the first turn.
    Turns alternate between Agent 1 and Agent 2.
    A prize is collected when an agent moves into a cell containing a prize.

    Parameters:
        agent1, agent2       : agent objects with a next_move() method
        maze                 : tuple[str, ...] - initial maze state
        agent1_position      : (int, int) - starting position of Agent 1
        agent2_position      : (int, int) - starting position of Agent 2
        prize_positions      : dict[(int, int), int] - initial prize locations and values
        max_turns            : int - maximum total number of turns

    Returns:
        dict with keys:
            'score1'      : int - total score of Agent 1
            'score2'      : int - total score of Agent 2
            'turns_played': int - total number of turns played
            'result'      : str - 'agent1', 'agent2', or 'draw'
    """
    score1 = 0
    score2 = 0
    pos1 = agent1_position
    pos2 = agent2_position
    prize_positions = dict(prize_positions)  # work on a local copy
    turns_played = 0

    for turn in range(max_turns):
        # Determine which agent acts this turn
        if turn % 2 == 0:
            active_agent = agent1
            active_pos = pos1
            is_agent1 = True
        else:
            active_agent = agent2
            active_pos = pos2
            is_agent1 = False

        # Get and apply move
        move = _safe_next_move(active_agent, maze, prize_positions, active_pos,
                               pos2 if is_agent1 else pos1)
        new_pos = _apply_move(maze, active_pos, move)

        # Collect prize if present
        if new_pos in prize_positions:
            if is_agent1:
                score1 += prize_positions[new_pos]
            else:
                score2 += prize_positions[new_pos]
            del prize_positions[new_pos]
            maze = _update_maze(maze, new_pos)

        # Update position
        if is_agent1:
            pos1 = new_pos
        else:
            pos2 = new_pos

        turns_played += 1

        # Check end condition
        if not prize_positions:
            break

    # Determine result
    if score1 > score2:
        result = 'agent1'
    elif score2 > score1:
        result = 'agent2'
    else:
        result = 'draw'

    return {
        'score1':       score1,
        'score2':       score2,
        'turns_played': turns_played,
        'result':       result,
    }


def init_agent(agent_class, maze, prize_positions, agent_position, opponent_position, max_turns):
    """
    Instantiates an agent safely.
    If the __init__ raises an exception, returns a DummyAgent instance instead,
    so the game can proceed without interruption.
    """
    try:
        return agent_class(maze, prize_positions, agent_position, opponent_position, max_turns)
    except Exception:
        from agents.dummy_agent import DummyAgent
        return DummyAgent(maze, prize_positions, agent_position, opponent_position, max_turns)
