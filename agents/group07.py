from move import Move
from collections import deque


class Group07:

    def __init__(self, maze, prize_positions, agent_position, opponent_position, max_turns):
        self.maze = maze
        self.rows = len(maze)
        self.cols = len(maze[0])
        self.max_turns = max_turns

        # Precompute BFS distances from agent start and from each prize
        # We'll use BFS on demand (cached) since maze is static (walls don't change)
        self._dist_cache = {}  # {start_pos: {pos: dist}}

        # Precompute distances from agent starting position
        self._precompute_bfs(agent_position)

        # Precompute distances from all prize positions
        for pos in prize_positions:
            self._precompute_bfs(pos)

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

    def _score_prize(self, prize_pos, prize_value, agent_pos, opponent_pos, remaining_turns, my_dist_map):
        """
        Score a prize for selection. Higher is better.
        Considers: value, distance, whether opponent can beat us there.
        """
        my_dist = my_dist_map.get(prize_pos, float('inf'))
        if my_dist == float('inf'):
            return float('-inf')

        # Opponent distance to this prize
        opp_dist = self._bfs_distance(opponent_pos, prize_pos)

        # If we can't reach it in time, skip
        if my_dist > remaining_turns:
            return float('-inf')

        # If opponent will definitely beat us (arrives strictly before us), penalize heavily
        # But if it's a tie or we're closer, it's still worth going
        if opp_dist < my_dist:
            # Opponent beats us only pursue if prize value is very high and margin is small
            margin = my_dist - opp_dist
            if margin > 2:
                return float('-inf')
            # Still consider but heavily penalized
            return (prize_value / (my_dist + 1)) * 0.1

        # Base score: value per step (efficiency)
        score = prize_value / (my_dist + 1)

        # Bonus if opponent is close to us (competitive pressure) go faster to contested prizes
        competitive_bonus = 1.0
        if opp_dist <= my_dist + 2:
            competitive_bonus = 1.5  # urgency bonus

        return score * competitive_bonus

    def next_move(self, maze, prize_positions, agent_position, opponent_position):
        if not prize_positions:
            return Move.STAY

        # Recompute BFS from current agent position if not cached
        my_dist_map = self._precompute_bfs(agent_position)

        # Estimate remaining turns for this agent (conservative: half of max_turns)
        remaining_turns = self.max_turns  # upper bound

        # Score all available prizes
        best_prize = None
        best_score = float('-inf')

        for pos, value in prize_positions.items():
            score = self._score_prize(
                pos, value, agent_position, opponent_position,
                remaining_turns, my_dist_map
            )
            if score > best_score:
                best_score = score
                best_prize = pos

        if best_prize is None:
            return Move.STAY

        # Navigate towards best prize
        path = self._get_path(agent_position, best_prize)

        if len(path) < 2:
            # Already at prize (shouldn't happen since it'd be collected), or unreachable
            return Move.STAY

        next_pos = path[1]
        return self._pos_to_move(agent_position, next_pos)