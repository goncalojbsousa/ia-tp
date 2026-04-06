from move import Move
from collections import deque


class Group07:

    def __init__(self, maze, prize_positions, agent_position, opponent_position, max_turns):
        # Guardar o labirinto e o número máximo de turnos para usar depois
        self.maze = maze
        self.max_turns = max_turns

        # Pré-calcular as dimensões do labirinto uma vez só
        self.rows = len(maze)
        self.cols = len(maze[0])

        # Turno atual (cada chamada a next_move é um turno nosso)
        self.turn = 0


    def next_move(self, maze, prize_positions, agent_position, opponent_position):
        self.turn += 1

        # Se não há prémios, não há nada para fazer
        if not prize_positions:
            return Move.STAY

        # Escolher o prémio mais valioso que esteja mais perto (relação valor/distância)
        best_target = self._escolher_melhor_premio(maze, agent_position, prize_positions)

        if best_target is None:
            return Move.STAY

        # Calcular o caminho até ao prémio escolhido com BFS
        path = self._bfs(maze, agent_position, best_target)

        # Se encontrou caminho, dar o primeiro passo
        if path and len(path) > 1:
            next_pos = path[1]  # path[0] é a posição atual, path[1] é o próximo passo
            return self._pos_to_move(agent_position, next_pos)

        return Move.STAY


    def _escolher_melhor_premio(self, maze, pos, prize_positions):
        """
        Percorre todos os prémios disponíveis e escolhe o que tem melhor
        relação entre valor e distância até lá chegar.
        """
        melhor = None
        melhor_score = -1

        for prize_pos, prize_val in prize_positions.items():
            dist = self._distancia_manhattan(pos, prize_pos)

            # Evitar divisão por zero (caso estejamos em cima do prémio)
            if dist == 0:
                return prize_pos

            # Score = valor / distância — quanto maior, mais apetecível
            score = prize_val / dist

            if score > melhor_score:
                melhor_score = score
                melhor = prize_pos

        return melhor


    def _distancia_manhattan(self, a, b):
        """
        Distância de Manhattan entre dois pontos numa grelha.
        É a soma das diferenças absolutas nas linhas e colunas.
        Serve como estimativa rápida (sem ter em conta paredes).
        """
        return abs(a[0] - b[0]) + abs(a[1] - b[1])


    def _bfs(self, maze, inicio, objetivo):
        """
        Procura em largura (Breadth-First Search) para encontrar o caminho
        mais curto entre dois pontos no labirinto.

        O BFS garante que o primeiro caminho encontrado é o mais curto
        em número de passos.

        Devolve a lista de posições desde o início até ao objetivo,
        ou None se não houver caminho.
        """
        if inicio == objetivo:
            return [inicio]

        # Fila de pares (posição_atual, caminho_até_aqui)
        fila = deque()
        fila.append((inicio, [inicio]))

        # Conjunto de posições já visitadas para não voltar atrás
        visitados = set()
        visitados.add(inicio)

        while fila:
            pos_atual, caminho = fila.popleft()

            for vizinho in self._vizinhos_validos(maze, pos_atual):
                if vizinho not in visitados:
                    novo_caminho = caminho + [vizinho]

                    if vizinho == objetivo:
                        return novo_caminho

                    visitados.add(vizinho)
                    fila.append((vizinho, novo_caminho))

        # Não foi possível chegar ao objetivo
        return None


    def _vizinhos_validos(self, maze, pos):
        """
        Devolve as posições adjacentes que são acessíveis (não são paredes).
        Verifica também se estão dentro dos limites do labirinto.
        """
        linha, col = pos
        candidatos = [
            (linha - 1, col),  # cima
            (linha + 1, col),  # baixo
            (linha, col - 1),  # esquerda
            (linha, col + 1),  # direita
        ]

        validos = []
        for r, c in candidatos:
            # Verificar se está dentro dos limites
            if 0 <= r < self.rows and 0 <= c < self.cols:
                # Verificar se não é parede
                if maze[r][c] != '#':
                    validos.append((r, c))

        return validos


    def _pos_to_move(self, atual, proximo):
        """
        Converte duas posições (atual e próxima) numa ação do tipo Move.
        Compara linha e coluna para determinar a direção do movimento.
        """
        dr = proximo[0] - atual[0]  # diferença de linhas
        dc = proximo[1] - atual[1]  # diferença de colunas

        if dr == -1:
            return Move.UP
        elif dr == 1:
            return Move.DOWN
        elif dc == -1:
            return Move.LEFT
        elif dc == 1:
            return Move.RIGHT

        return Move.STAY