from move import Move
from collections import deque


class Group07:

    def __init__(self, maze, prize_positions, agent_position, opponent_position, max_turns):
        self.maze = maze
        self.rows = len(maze)
        self.cols = len(maze[0])
        self.max_turns = max_turns

        # Distances are cached lazily by BFS source.
        self._dist_cache = {}  # {start_pos: {pos: dist}}

        # Turn and opponent behavior tracking.
        self._my_turns = 0
        self._prev_opponent_pos = opponent_position
        self._opponent_moved_flags = deque(maxlen=8)

        # Current route cache.
        self._current_target = None
        self._current_path = []

        # Short TTL cache for prizes currently not worth pursuing.
        self._skip_prizes_until_turn = {}  # {prize_pos: my_turn_number}

        # Warm up cache for current position only.
        self._precompute_bfs(agent_position)

    def _precompute_bfs(self, start):
        """BFS from start, returns dist dict for all reachable cells."""
        if start in self._dist_cache:
            return self._dist_cache[start]

        dist = {start: 0}
        queue = deque([start])
        maze = self.maze

        while queue:
            r, c = queue.popleft()
            for dr, dc in [(-1, 0), (1, 0), (0, 1), (0, -1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if maze[nr][nc] != '#' and (nr, nc) not in dist:
                        dist[(nr, nc)] = dist[(r, c)] + 1
                        queue.append((nr, nc))

        self._dist_cache[start] = dist
        return dist

    def _bfs_distance(self, start, end):
        """Get BFS distance between two points, using cache."""
        dist_map = self._precompute_bfs(start)
        return dist_map.get(end, float('inf'))

    def _remaining_own_turns(self):
        """Conservative estimate of turns left for this agent."""
        # We do not know globally whether we are first or second mover,
        # so use floor(max_turns / 2) as a safe bound.
        max_own_turns = self.max_turns // 2
        remaining = max_own_turns - (self._my_turns - 1)
        return max(1, remaining)

    def _opponent_activity(self):
        """Return movement ratio in [0, 1] based on recent observed turns."""
        if not self._opponent_moved_flags:
            return 0.5
        return sum(1 for moved in self._opponent_moved_flags if moved) / len(self._opponent_moved_flags)

    def _get_path(self, start, end):
        """BFS to find path from start to end. Returns list of positions."""
        if start == end:
            return [start]

        dist_map = self._precompute_bfs(start)
        if end not in dist_map:
            return []

        # Reconstruct path by walking backwards using distances
        path = [end]
        current = end
        maze = self.maze

        while current != start:
            r, c = current
            for dr, dc in [(-1, 0), (1, 0), (0, 1), (0, -1)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in dist_map and dist_map[(nr, nc)] == dist_map[current] - 1:
                    path.append((nr, nc))
                    current = (nr, nc)
                    break

        path.reverse()
        return path

    def _pos_to_move(self, current, next_pos):
        """Convert position change to Move enum."""
        r, c = current
        nr, nc = next_pos
        if nr == r - 1:
            return Move.UP
        if nr == r + 1:
            return Move.DOWN
        if nc == c + 1:
            return Move.RIGHT
        if nc == c - 1:
            return Move.LEFT
        return Move.STAY

    def _valid_moves(self, maze, position):
        r, c = position
        candidates = [
            (Move.UP, r - 1, c),
            (Move.DOWN, r + 1, c),
            (Move.LEFT, r, c - 1),
            (Move.RIGHT, r, c + 1),
        ]
        valid = []
        for move, nr, nc in candidates:
            if 0 <= nr < self.rows and 0 <= nc < self.cols and maze[nr][nc] != '#':
                valid.append((move, (nr, nc)))
        return valid

    def _best_fallback_move(self, maze, agent_position, prize_positions):
        """Choose a valid non-stay move that reduces distance to any remaining prize."""
        valid_moves = self._valid_moves(maze, agent_position)
        if not valid_moves:
            return Move.STAY

        # Deterministic ordering for stable behavior across runs.
        move_order = {Move.UP: 0, Move.LEFT: 1, Move.RIGHT: 2, Move.DOWN: 3}

        best = None
        best_key = (float('inf'), float('inf'), float('inf'))
        for move, next_pos in valid_moves:
            nearest = float('inf')
            best_value = 0
            for prize_pos, prize_value in prize_positions.items():
                d = self._bfs_distance(next_pos, prize_pos)
                if d < nearest:
                    nearest = d
                    best_value = prize_value
                elif d == nearest and prize_value > best_value:
                    best_value = prize_value

            # Prefer smaller distance, then larger prize value, then fixed move order.
            key = (nearest, -best_value, move_order[move])
            if key < best_key:
                best_key = key
                best = move

        return best if best is not None else Move.STAY

    def _advance_cached_path_to_position(self, agent_position):
        """Align cached path to current position, if possible."""
        if not self._current_path:
            return False
        if self._current_path[0] == agent_position:
            return True
        try:
            idx = self._current_path.index(agent_position)
            self._current_path = self._current_path[idx:]
            return True
        except ValueError:
            return False

    def _score_prize(self, prize_pos, prize_value, agent_pos, opponent_pos, remaining_turns, my_dist_map, prize_positions):
        """
        Score a prize for selection. Higher is better.
        Considers: value, distance, contest margin, opponent activity.
        """
        my_dist = my_dist_map.get(prize_pos, float('inf'))
        if my_dist == float('inf'):
            return float('-inf')

        if my_dist > remaining_turns:
            return float('-inf')

        opp_dist = self._bfs_distance(opponent_pos, prize_pos)
        margin = opp_dist - my_dist  # >0 means we are closer
        activity = self._opponent_activity()
        opponent_is_passive = activity < 0.35

        # Base efficiency: when opponent is active, prioritize short captures more.
        dist_exponent = 1.45 if activity >= 0.60 else 1.20
        score = prize_value / ((my_dist + 1) ** dist_exponent)

        # Favor local prize clusters to reduce travel overhead.
        cluster_count = 0
        for other_pos in prize_positions:
            if other_pos != prize_pos and abs(other_pos[0] - prize_pos[0]) + abs(other_pos[1] - prize_pos[1]) <= 4:
                cluster_count += 1
        if cluster_count:
            score *= (1.0 + min(cluster_count, 4) * 0.05)

        # Aggressive but margin-aware competition model.
        if margin >= 2:
            contest_factor = 1.45
        elif margin == 1:
            contest_factor = 1.25
        elif margin == 0:
            contest_factor = 1.10
        elif margin == -1:
            contest_factor = 0.90
        elif margin == -2:
            contest_factor = 0.65
        else:
            # Keep some pressure on distant-contested prizes without giving up entirely.
            contest_factor = max(0.25, 0.55 - 0.06 * (abs(margin) - 2))

        # If opponent tends to stay, reduce contest pressure and focus throughput.
        if opponent_is_passive:
            contest_factor = (contest_factor + 1.0) / 2.0

        score *= contest_factor

        # Endgame urgency: prioritize short, guaranteed captures.
        if remaining_turns <= 4:
            score *= (1.0 + 2.0 / (my_dist + 1))

        return score

    def next_move(self, maze, prize_positions, agent_position, opponent_position):
        self._my_turns += 1
        self._opponent_moved_flags.append(opponent_position != self._prev_opponent_pos)
        self._prev_opponent_pos = opponent_position

        if not prize_positions:
            return Move.STAY

        my_dist_map = self._precompute_bfs(agent_position)
        remaining_turns = self._remaining_own_turns()

        # Score all available prizes with deterministic tie-breaking.
        best_prize = None
        best_score = float('-inf')
        best_key = (float('inf'), float('inf'), float('inf'))

        for pos, value in prize_positions.items():
            score = self._score_prize(
                pos, value, agent_position, opponent_position,
                remaining_turns, my_dist_map, prize_positions
            )

            if score == float('-inf'):
                continue

            my_dist = my_dist_map.get(pos, float('inf'))
            tie_key = (-value, my_dist, pos[0] * self.cols + pos[1])

            if score > best_score or (score == best_score and tie_key < best_key):
                best_score = score
                best_prize = pos
                best_key = tie_key

        if best_prize is None:
            return self._best_fallback_move(maze, agent_position, prize_positions)

        # Reuse cached route if still valid and target did not change.
        if self._current_target == best_prize and self._advance_cached_path_to_position(agent_position):
            if len(self._current_path) >= 2:
                return self._pos_to_move(agent_position, self._current_path[1])

        path = self._get_path(agent_position, best_prize)
        self._current_target = best_prize
        self._current_path = path

        if len(path) < 2:
            return self._best_fallback_move(maze, agent_position, prize_positions)

        next_pos = path[1]
        return self._pos_to_move(agent_position, next_pos)