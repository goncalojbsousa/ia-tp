import sys
import importlib

from game import load_maze, init_agent, run_game

REFERENCE_AGENTS = {
    'dummy':  ('agents.dummy_agent',  'DummyAgent'),
    'random': ('agents.random_agent', 'RandomAgent'),
    'greedy': ('agents.greedy_agent', 'GreedyAgent'),
}


def load_agent_class(name):
    """
    Loads an agent class by name.

    For reference agents ('dummy', 'random', 'greedy'), maps to the correct
    module and class in the agents package.

    For group agents (e.g. 'group05'), looks for a file named 'group05.py'
    in the agents package and expects a class named 'Group05' inside it.

    Returns the agent class, or None if loading fails.
    """
    if name in REFERENCE_AGENTS:
        module_name, class_name = REFERENCE_AGENTS[name]
    else:
        # Assume group agent: e.g. 'group05' -> agents/group05.py, class 'Group05'
        module_name = f'agents.{name}'
        suffix = name[len('group'):] if name.lower().startswith('group') else name
        class_name = 'Group' + suffix

    try:
        module = importlib.import_module(module_name)
        agent_class = getattr(module, class_name)
        return agent_class
    except ModuleNotFoundError:
        print(f"Error: could not find file '{name}.py' in 'agents/' folder.")
        return None
    except AttributeError:
        print(f"Error: file '{name}.py' does not contain a class named '{class_name}'.")
        return None


def print_result(name1, name2, result):
    """
    Prints the game result to the console.
    """
    print()
    print("=" * 40)
    print("           GAME RESULT")
    print("=" * 40)
    print(f"  Agent 1 ({name1:<10}): {result['score1']:>4} pts")
    print(f"  Agent 2 ({name2:<10}): {result['score2']:>4} pts")
    print(f"  Turns played       : {result['turns_played']}")
    print("-" * 40)
    if result['result'] == 'agent1':
        print(f"  Winner: Agent 1 ({name1})")
    elif result['result'] == 'agent2':
        print(f"  Winner: Agent 2 ({name2})")
    else:
        print("  Result: Draw")
    print("=" * 40)
    print()


def main():
    if len(sys.argv) != 5:
        print("Usage: python run.py <maze_file> <max_turns> <agent1> <agent2>")
        print("  <maze_file> : path to the maze text file")
        print("  <max_turns> : maximum total number of turns")
        print("  <agent1>    : 'dummy', 'random', 'greedy', or group name (e.g. group05)")
        print("  <agent2>    : 'dummy', 'random', 'greedy', or group name (e.g. group05)")
        sys.exit(1)

    maze_file  = sys.argv[1]
    max_turns  = int(sys.argv[2])
    name1      = sys.argv[3]
    name2      = sys.argv[4]

    # Load agent classes
    agent1_class = load_agent_class(name1)
    agent2_class = load_agent_class(name2)

    if agent1_class is None:
        print(f"Agent 1 ({name1}) could not be loaded. Score set to -1.")
    if agent2_class is None:
        print(f"Agent 2 ({name2}) could not be loaded. Score set to -1.")

    if agent1_class is None or agent2_class is None:
        print()
        print("=" * 40)
        print("           GAME RESULT")
        print("=" * 40)
        print(f"  Agent 1 ({name1:<10}): {'N/A' if agent1_class is None else '?':>4}")
        print(f"  Agent 2 ({name2:<10}): {'N/A' if agent2_class is None else '?':>4}")
        print("-" * 40)
        score1 = -1 if agent1_class is None else 0
        score2 = -1 if agent2_class is None else 0
        print(f"  Score 1: {score1}")
        print(f"  Score 2: {score2}")
        print("=" * 40)
        sys.exit(1)

    # Load maze
    try:
        maze, pos1, pos2, prize_positions, _ = load_maze(maze_file)
    except FileNotFoundError:
        print(f"Error: maze file '{maze_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading maze: {e}")
        sys.exit(1)

    # Initialise agents (falls back to Dummy if __init__ raises an exception)
    agent1 = init_agent(agent1_class, maze, prize_positions, pos1, pos2, max_turns)
    agent2 = init_agent(agent2_class, maze, prize_positions, pos2, pos1, max_turns)

    # Run the game
    result = run_game(agent1, agent2, maze, pos1, pos2, prize_positions, max_turns)

    # Print result
    print_result(name1, name2, result)


if __name__ == '__main__':
    main()
