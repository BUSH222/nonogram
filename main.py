import random
from const import BLACK, WHITE, X_char
from noise import Perlin2D
from itertools import combinations


class Nonogram:
    def __init__(self):
        self.board = [] # 1 is black, 0 is white - ground truth
        self.state = [] # user progress, 1 for black, 0 for white, -1 for x
        self.hints = [[], []] # top hints bar first
    
    @property
    def solved(self):
        assert self.hints[0] and self.hints[1]
    
        hor_state, ver_state = [], []
        for i in range(len(self.state)):
            hor_state.append([0,])
            for j in range(len(self.state[i])):
                if self.state[i][j] == 0 or self.state[i][j] == -1:
                    hor_state[i].append(0)
                else:
                    hor_state[i][-1] += 1
            while 0 in hor_state[i]:
                hor_state[i].remove(0)

        for j in range(len(self.state[0])):
            ver_state.append([0,])
            for i in range(len(self.state)):
                if self.state[i][j] == 0 or self.state[i][j] == -1:
                    ver_state[j].append(0)
                else:
                    ver_state[j][-1] += 1
            while 0 in ver_state[j]:
                ver_state[j].remove(0)
        
        return hor_state == self.hints[0] and ver_state == self.hints[1]

    def move(self, x, y, value):
        assert 0<=x<len(self.state) and 0<=y<len(self.state[0]) and value in [1, 0, -1]
        self.state[x][y] = value

    def generate_board(self, rows, cols, seed, density, random_function='perlin2d', frequency=6):
        assert 2<rows<100 and 2<cols<100 and 0<density<1 and random_function in ['random', 'perlin2d']
        if random_function == 'random':
            random.seed(seed)
            self.board = [[1 if random.random() < density else 0 for x in range(cols)] for y in range(rows)]
        elif random_function == 'perlin2d':
            perlin = Perlin2D(seed=seed)
            self.board = [[1 if perlin.noise(x/cols * frequency, y/rows * frequency) < density else 0 for x in range(cols)] for y in range(rows)]
        self.compute_hints()
        self.state = [[0 for x in range(cols)] for y in range(rows)]
    
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

    def get_board(self, target='board'):
        assert target in ['board', 'state']
        if target == 'board':
            tgt = self.board
        else:
            tgt = self.state
        if self.hints[0] and self.hints[1]:
            hint_length_hor = len(max([''.join(list(map(str, item))) for item in self.hints[0]], key=len))
            hint_length_ver = len(max([''.join(list(map(str, item))) for item in self.hints[1]], key=len))

            hints1_with_padding = []
            for i in range(len(self.hints[1])):
                hints1_with_padding.append(self.hints[1][i].copy())
                for _ in range(hint_length_ver-len(hints1_with_padding[i])):
                    hints1_with_padding[i].insert(0, ' ')

            preamble = ' ' * (hint_length_hor*2-1) + '  '
            for i in range(hint_length_ver):
                print(preamble, end='')
                for j in range(len(tgt[0])):
                    if len(str(hints1_with_padding[j][i])) >= 2:
                        print(hints1_with_padding[j][i], end='')
                    else:
                        print(hints1_with_padding[j][i], end=' ')
                print()
            print(preamble[:-2] + '+' + '-'*len(tgt[0]*2))
        else:
            print("hints not generated yet, run compute_hints()")
        for i in range(len(tgt)):
            if self.hints[0] and self.hints[1]:
                print(' '.join([' ' for _ in range(hint_length_hor-len(self.hints[0][i]))] + list(map(str, self.hints[0][i]))) + '| ', end='')
            for j in range(len(tgt[i])):
                if tgt[i][j] == 1:
                    print(BLACK, end=' ')
                elif tgt[i][j] == 0:
                    print(WHITE, end=' ')
                elif tgt[i][j] == -1:
                    print(X_char, end=' ')
            print()
        return ''

    
    def __repr__(self):
        self.get_board(target='state')
        return ''
    

class Solver:
    def __init__(self, nonogram):
        self.nonogram = nonogram
    def solve(self):
        # step 1 - find all possible combinations, then fill in overlaps
        # horisontal
        for iteration in range(100):
            if self.nonogram.solved:
                print(f"Solved in {iteration} iterations!")
                return
            for i in range(len(self.nonogram.state)):
                row = self.nonogram.state[i]
                hint = self.nonogram.hints[0][i]
                if all([cell != 0 for cell in row]):
                    continue
                overlaps = [1 for _ in range(len(row))] # black
                overlaps1 = [1 for _ in range(len(row))] # white
                for r in self._generate_rows(len(row), hint):

                    # conformity check
                    skiprow = False
                    for p in range(len(row)):  
                        if row[p] == 1 and r[p] != 1:
                            skiprow = True
                            break
                        if row[p] == -1 and r[p] != 0:
                            skiprow = True
                            break
                    if skiprow:
                        continue

                    for j in range(len(row)):
                        overlaps[j] &= r[j]
                        overlaps1[j] &= (1-r[j])

                for a, b in enumerate(overlaps):
                    if self.nonogram.state[i][a] == 0 and b == 1:
                        self.nonogram.move(i, a, 1)
                    if self.nonogram.state[i][a] == 0 and overlaps1[a] == 1:
                        self.nonogram.move(i, a, -1)
            
            # vertical
            for j in range(len(self.nonogram.state[0])):
                row = [self.nonogram.state[i][j] for i in range(len(self.nonogram.state))]
                hint = self.nonogram.hints[1][j]
                if all([cell != 0 for cell in row]):
                    continue
                overlaps = [1 for _ in range(len(row))] # black
                overlaps1 = [1 for _ in range(len(row))] # white
                for r in self._generate_rows(len(row), hint):
                    # conformity check
                    skiprow = False
                    for p in range(len(row)):  
                        if row[p] == 1 and r[p] != 1:
                            skiprow = True
                            break
                        if row[p] == -1 and r[p] != 0:
                            skiprow = True
                            break
                    if skiprow:
                        continue

                    for k in range(len(row)):
                        overlaps[k] &= r[k]
                        overlaps1[k] &= (1-r[k])
                for a, b in enumerate(overlaps):
                    if self.nonogram.state[a][j] == 0 and b == 1:
                        self.nonogram.move(a, j, 1)
                    if self.nonogram.state[a][j] == 0 and overlaps1[a] == 1:
                        self.nonogram.move(a, j, -1)

        print("Couldn't solve in 100 iterations, giving up.")

    
    def _generate_rows(self, length, runs):
        try:
            total_black = sum(runs)
        except:
            print("runs:", runs)
            for item in runs:
                print(item, type(item))
        extra = length - (total_black + len(runs) - 1)
        assert extra >= 0
        gaps = len(runs) + 1
        for bars in combinations(range(extra + gaps - 1), gaps - 1):
            values = []
            prev = -1

            for bar in bars:
                values.append(bar - prev - 1)
                prev = bar
            values.append(extra + gaps - 1 - prev - 1)

            row = []
            row.extend([0] * values[0])
            for i, run in enumerate(runs):
                row.extend([1] * run)
                if i < len(runs) - 1:
                    row.extend([0] * (1 + values[i + 1]))
            row.extend([0] * values[-1])
            yield row


if __name__ == "__main__":
    n = Nonogram()
    n.generate_board(rows=15, cols=15, seed=3, density=0.5)
    print(n)
    s = Solver(n)
    s.solve()
    print(n)
    print(n.get_board())