import random
from const import BLACK, WHITE



class Nonogram:
    def __init__(self):
        self.board = [] # 1 is black, 0 is white - ground truth
        self.state = [] # user progress
        self.hints = [[], []] # top hints bar first
    
    def compute_hints(self):
        hor_state, ver_state = [], [] # 1 list for each hint type, horisontal and vertical
        for i in range(len(self.board)):
            hor_state.append([0,])
            for j in range(len(self.board[i])):
                if self.board[i][j] == 0:
                    hor_state[i].append(0)
                else:
                    hor_state[i][-1] += 1
            while 0 in hor_state[i]:
                hor_state[i].remove(0)

        for j in range(len(self.board[0])):
            ver_state.append([0,])
            for i in range(len(self.board)):
                if self.board[i][j] == 0:
                    ver_state[j].append(0)
                else:
                    ver_state[j][-1] += 1
            while 0 in ver_state[j]:
                ver_state[j].remove(0)
        
        self.hints = [hor_state, ver_state]


    def generate_board(self, rows, cols, seed, density):
        assert 2<rows<100 and 2<cols<100 and 0<density<1
        random.seed(seed)
        self.board = [[1 if random.random() < density else 0 for _ in range(cols)] for _ in range(rows)]
        self.compute_hints()

    def get_board(self):
        for row in self.board:
            print(' '.join(str(cell) for cell in row))

    
    def __repr__(self):
        if self.hints[0] and self.hints[1]:
            hint_length_hor = len(max([''.join(list(map(str, item))) for item in self.hints[0]], key=len))
            hint_length_ver = len(max([''.join(list(map(str, item))) for item in self.hints[1]], key=len))
            hints1_with_padding = []
            for i in range(len(self.hints[1])):
                hints1_with_padding.append(self.hints[1][i])
                for _ in range(hint_length_ver-len(hints1_with_padding[i])):
                    hints1_with_padding[i].insert(0, ' ')

            preamble = ' ' * (hint_length_hor*2-1) + '  '
            for i in range(hint_length_ver):
                print(preamble, end='')
                for j in range(len(self.board[0])):
                    print(hints1_with_padding[j][i], end=' ')
                print()
            print(preamble[:-2] + '+' + '-'*len(self.board[0]*2))

            
        else:
            print("hints not generated yet, run compute_hints()")
        for i in range(len(self.board)):
            if self.hints[0] and self.hints[1]:
                print(' '.join([' ' for _ in range(hint_length_hor-len(self.hints[0][i]))] + list(map(str, self.hints[0][i]))) + '| ', end='')
            for j in range(len(self.board[i])):
                if self.board[i][j]:
                    print(BLACK, end=' ')
                else:
                    print(WHITE, end=' ')
            print()
        return ''


if __name__ == "__main__":
    n = Nonogram()
    n.generate_board(rows=15, cols=15, seed=42, density=0.3)
    print(n)