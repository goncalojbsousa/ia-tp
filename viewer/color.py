import viewer.ansicolors as ansicolors
from .base import BaseViewer


class ColorViewer(BaseViewer):

    def on_turn(self, state) -> bool:
        maze           = state['maze']
        pos1           = state['pos1']
        pos2           = state['pos2']
        score1         = state['score1']
        score2         = state['score2']
        turn           = state['turn']
        is_agent1_turn = state['is_agent1_turn']
        name1          = state['name1']
        name2          = state['name2']

        player = name1 if is_agent1_turn else name2
        print(f"\n--- Turn {turn} | Player: {player} | {name1}: {score1} pts | {name2}: {score2} pts ---")

        for row_idx, row in enumerate(maze):
            line = ''
            for col_idx, cell in enumerate(row):
                pos = (row_idx, col_idx)
                if pos == pos1 == pos2:
                    line += ansicolors.style('WW', bg=ansicolors.BG_RED)
                elif pos == pos1:
                    line += ansicolors.style('XX', bg=ansicolors.BG_MAGENTA)
                elif pos == pos2:
                    line += ansicolors.style('YY', bg=ansicolors.BG_BLUE)
                elif cell == '#':
                    line += '██'
                elif cell == '.':
                    line += '  '
                else:
                    line += ansicolors.style(' ' + cell, bg=ansicolors.BG_BRIGHT_GREEN)
            print(line)

        answer = input("Press Enter to continue or N to quit... ").strip().upper()
        return answer == 'N'
