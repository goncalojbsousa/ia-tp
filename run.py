import argparse
import sys
import importlib.util
import struct
import importlib
import os
import glob
import time

from game import load_maze, init_agent, run_game
from viewer import TextViewer, ColorViewer, GraphViewer


def load_agent_class(name):
    """
    Loads an agent class by name.
    Returns the agent class, or None if loading fails.
    """
    if name.lower().startswith('group') and name[5:].isdigit():
        module_name = f'agents.{name}'
        class_name  = 'Group' + name[5:]
        file_base   = name
    else:
        module_name = f'agents.{name}_agent'
        class_name  = name[0].upper() + name[1:] + 'Agent'
        file_base   = f'{name}_agent'

    py_path  = os.path.join('agents', file_base + '.py')
    pyc_path = os.path.join('agents', file_base + '.pyc')

    print(f"Loading agent '{name}' from module '{module_name}', class '{class_name}'...")

    if os.path.exists(py_path):
        # Normal .py loading
        try:
            module = importlib.import_module(module_name)
            agent_class = getattr(module, class_name)
            return agent_class
        except ModuleNotFoundError:
            print(f"Error: could not find file '{file_base}.py' in 'agents/' folder.")
            return None
        except AttributeError:
            print(f"Error: file '{file_base}.py' does not contain a class named '{class_name}'.")
            return None

    elif os.path.exists(pyc_path):
        # Load .pyc directly
        try:
            spec   = importlib.util.spec_from_file_location(module_name, pyc_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            agent_class = getattr(module, class_name)
            return agent_class
        except Exception as e:
            print(f"Error loading '{file_base}.pyc': {e}")
            return None

    else:
        print(f"Error: could not find '{file_base}.py' or '{file_base}.pyc' in 'agents/' folder.")
        return None


def print_result(name1, name2, result):
    """
    Prints the game result to the console.
    """
    print()
    print("=" * 40)
    print("           GAME RESULT")
    print("=" * 40)
    print(f"  Turns played       : {result['turns_played']}")
    print(f"  Agent 1 - {name1:<15}: {result['score1']:>3} pts")
    print(f"  Agent 2 - {name2:<15}: {result['score2']:>3} pts")
    print(f"  Time agent 1: {result['move_time1']*1000:12.6f} ms")
    print(f"  Time agent 2: {result['move_time2']*1000:12.6f} ms")
    print("-" * 40)
    if result['score1'] > result['score2']:
        print(f"  Winner by points: Agent 1 ({name1})")
    elif result['score2'] > result['score1']:
        print(f"  Winner by points: Agent 2 ({name2})")
    else:
        print("  Result by points: Draw")
    if result['move_time1'] < result['move_time2']:
        print(f"  Winner by time  : Agent 1 ({name1})")
    elif result['move_time2'] < result['move_time1']:
        print(f"  Winner by time  : Agent 2 ({name2})")
    else:
        print("  Result by time  : Draw")
    print("=" * 40)
    print()

def print_run_results(name1, name2, runs, totals):
    avg = {k: v / runs for k, v in totals.items()}
    print()
    print("=" * 40)
    print(f"        AVERAGE RESULTS ({runs} runs)")
    print("=" * 40)
    print(f"  Avg turns played       : {avg['turns_played']:.1f}")
    print(f"  Avg Agent 1 - {name1:<10}: {avg['score1']:>6.2f} pts")
    print(f"  Avg Agent 2 - {name2:<10}: {avg['score2']:>6.2f} pts")
    print(f"  Avg time agent 1: {avg['move_time1']*1000:12.6f} ms")
    print(f"  Avg time agent 2: {avg['move_time2']*1000:12.6f} ms")
    print("=" * 40)
    print()

def list_available_agents():
    """
    Lists all available agent names in folder 'agents'.
    Returns a list of agent names (without _agent.py or .pyc extensions).
    """
    agents_dir = os.path.join(os.path.dirname(__file__), 'agents')
    
    py_pattern  = os.path.join(agents_dir, '*_agent.py')
    pyc_pattern = os.path.join(agents_dir, '*_agent.pyc')
    
    py_names  = set(os.path.basename(f).replace('_agent.py',  '') for f in glob.glob(py_pattern))
    pyc_names = set(os.path.basename(f).replace('_agent.pyc', '') for f in glob.glob(pyc_pattern))

    return sorted(py_names | pyc_names)


def main():
    time.perf_counter()  # warm up the perf_counter to avoid possible first-call overhead in timing

    agents = list_available_agents()
    epilog = "Available agents: " + ", ".join(agents) if agents else "No agents found in agents/ folder."

    parser = argparse.ArgumentParser(
        description="Run a maze game between two agents.",
        usage="python %(prog)s maze_file max_turns agent1 agent2 [-v {text,color,graph}]",
        epilog=epilog
    )
    parser.add_argument('maze_file',
        help="path to the maze file. If not found, will also search in 'mazes/' folder with .txt extension (e.g. 'maze01' will try 'mazes/maze01.txt')")
    parser.add_argument('max_turns', type=int, help="maximum total number of turns")
    parser.add_argument('agent1', help="Agent from list below or group name (e.g. group05)")
    parser.add_argument('agent2', help="Agent from list below or group name (e.g. group05)")
    parser.add_argument('-v', "--view", choices=['text', 'color', 'graph'],
                        help='Show maze state at each turn: "text" for simple text, "color" for colored output, "graph" for graphical output')
    parser.add_argument('-r', '--runs', type=int, default=1,
                        help="number of runs to execute (default: 1). Viewer is disabled when runs > 1")

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
    agent1, init_time1 = init_agent(agent1_class, maze, prize_positions, pos1, pos2, args.max_turns)
    agent2, init_time2 = init_agent(agent2_class, maze, prize_positions, pos2, pos1, args.max_turns)

    # Select viewer (disabled when runs > 1)
    viewer_map = {
        'text':  TextViewer,
        'color': ColorViewer,
        'graph': GraphViewer,
    }
    viewer_class = viewer_map.get(args.view) if args.runs == 1 else None
    viewer = viewer_class() if viewer_class else None

    # Run loop
    totals = {'score1': 0, 'score2': 0, 'move_time1': 0.0, 'move_time2': 0.0, 'turns_played': 0}

    if args.runs > 1:
      print(f"\nStarting {args.runs} run(s) between '{name1}' and '{name2}' on maze '{args.maze_file}' with max {args.max_turns} turns...")

    for i in range(args.runs):
        agent1, _ = init_agent(agent1_class, maze, prize_positions, pos1, pos2, args.max_turns)
        agent2, _ = init_agent(agent2_class, maze, prize_positions, pos2, pos1, args.max_turns)

        result = run_game(
            agent1, agent2, maze, pos1, pos2, prize_positions, args.max_turns,
            on_turn=viewer.on_turn if viewer else None,
        )

        for key in totals:
            totals[key] += result[key]

        if args.runs > 1:
            print('.', end='', flush=True)

    if viewer:
        viewer.close()

    if args.runs == 1:
        print_result(name1, name2, result)
    else:
        print()
        print_run_results(name1, name2, args.runs, totals)

if __name__ == '__main__':
    main()
