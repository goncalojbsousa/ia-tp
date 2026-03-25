from .base import BaseViewer


class TextViewer(BaseViewer):

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
            if row_idx == pos1[0] == pos2[0] and pos1[1] == pos2[1]:
                print(row[:pos1[1]] + 'W' + row[pos1[1] + 1:])
            elif row_idx == pos1[0]:
                print(row[:pos1[1]] + 'X' + row[pos1[1] + 1:])
            elif row_idx == pos2[0]:
                print(row[:pos2[1]] + 'Y' + row[pos2[1] + 1:])
            else:
                print(row)

        answer = input("Press Enter to continue or N to quit... ").strip().upper()
        return answer == 'N'
