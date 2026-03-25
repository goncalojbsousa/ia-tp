import argparse
import sys
import importlib

from game import load_maze, init_agent, run_game
from viewer import TextViewer, ColorViewer


def load_agent_class(name):
    """
    Loads an agent class by name.
    Returns the agent class, or None if loading fails.
    """
    if name.lower().startswith('group') and name[5:].isdigit():
        module_name = f'agents.{name}'
        suffix = name[len('group'):]
        class_name = 'Group' + suffix
    else:
        module_name = f'agents.{name}_agent'
        class_name  = name[0].upper() + name[1:] + 'Agent'

    print(f"Loading agent '{name}' from module '{module_name}', class '{class_name}'...")
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
    parser = argparse.ArgumentParser(
        description="Run a maze game between two agents.",
        usage="python %(prog)s maze_file max_turns agent1 agent2 [-v {text,color}]"
    )
    parser.add_argument('maze_file', help="path to the maze text file")
    parser.add_argument('max_turns', type=int, help="maximum total number of turns")
    parser.add_argument('agent1', help="'dummy', 'random', 'greedy', or group name (e.g. group05)")
    parser.add_argument('agent2', help="'dummy', 'random', 'greedy', or group name (e.g. group05)")
    parser.add_argument('-v', choices=['text', 'color'],
                        help='Show maze state at each turn: "text" for simple text, "color" for colored output')
    args = parser.parse_args(None if sys.argv[1:] else ['--help'])

    name1     = args.agent1
    name2     = args.agent2

    # Load agent classes
    agent1_class = load_agent_class(name1)
    agent2_class = load_agent_class(name2)

    if agent1_class is None or agent2_class is None:
        if agent1_class is None:
            print(f"Agent 1 ({name1}) could not be loaded.")
        if agent2_class is None:
            print(f"Agent 2 ({name2}) could not be loaded.")
        sys.exit(1)

    # Load maze
    try:
        maze, pos1, pos2, prize_positions = load_maze(args.maze_file)
    except FileNotFoundError:
        print(f"Error: maze file '{args.maze_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading maze: {e}")
        sys.exit(1)

    # Initialise agents
    agent1 = init_agent(agent1_class, maze, prize_positions, pos1, pos2, args.max_turns)
    agent2 = init_agent(agent2_class, maze, prize_positions, pos2, pos1, args.max_turns)

    # Select viewer
    viewer_map = {
        'text':  TextViewer,
        'color': ColorViewer,
    }
    viewer_class = viewer_map.get(args.v)
    viewer = viewer_class() if viewer_class else None

    # Run the game
    result = run_game(
        agent1, agent2, maze, pos1, pos2, prize_positions, args.max_turns,
        on_turn=viewer.on_turn if viewer else None,
    )

    if viewer:
        viewer.close()

    print_result(name1, name2, result)


if __name__ == '__main__':
    main()
