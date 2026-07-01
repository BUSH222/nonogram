import random
from nonogram.const import BLACK, RANDOM_FUNCTIONS, WHITE, X_CHAR
from nonogram.noise import Perlin2D
from nonogram.solver import Solver


class Nonogram:
    def __init__(self):
        self.board = []  # 1 is black, 0 is white - ground truth
        self.state = []  # user progress, 1 for black, 0 for white, -1 for x
        self.hints = [[], []]  # top hints bar first
        self.user_highlighted_hints = [[], []]  # arrays of bools mirroring hints, for UI purposes
        self.details = {}
        self._solvable = None

    @property
    def solvable(self):
        if self._solvable is not None:
            return self._solvable
        else:
            solver = Solver(self, do_step=False)
            if solver.solve():
                self._solvable = True
            else:
                self._solvable = False
            return self._solvable

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
        assert 0 <= x < len(self.state) and 0 <= y < len(self.state[0]) and value in [1, 0, -1]
        self.state[x][y] = value

    def generate_board(self, rows, cols, seed, density, random_function='perlin2d', frequency=6):
        assert 2 < rows < 100 and 2 < cols < 100 and 0 < density < 1 and random_function in RANDOM_FUNCTIONS, \
            "Invalid parameters"
        self.details = {"rows": rows, "cols": cols, "seed": seed, "density": density,
                        "random_function": random_function, "frequency": frequency}
        if random_function == 'random':
            random.seed(seed)
            self.board = [[1 if random.random() < density else 0 for x in range(cols)] for y in range(rows)]
        elif random_function == 'perlin2d':
            perlin = Perlin2D(seed=seed)
            self.board = [[1 if perlin.noise(x/cols * frequency, y/rows * frequency) < density else 0
                           for x in range(cols)] for y in range(rows)]
        self.compute_hints()
        self.state = [[0 for x in range(cols)] for y in range(rows)]

    def compute_hints(self):
        hor_state, ver_state = [], []  # 1 list for each hint type, horisontal and vertical
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
        self.user_highlighted_hints = [[False for _ in range(len(h))] for h in hor_state], \
                                      [[False for _ in range(len(h))] for h in ver_state]

    def get_board(self):
        return {"state": self.state, "hints": self.hints, "details": self.details}

    def print_board(self, target='board'):
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
                print(' '.join([' ' for _ in range(hint_length_hor-len(self.hints[0][i]))]
                               + list(map(str, self.hints[0][i]))) + '| ', end='')
            for j in range(len(tgt[i])):
                if tgt[i][j] == 1:
                    print(BLACK, end=' ')
                elif tgt[i][j] == 0:
                    print(WHITE, end=' ')
                elif tgt[i][j] == -1:
                    print(X_CHAR, end=' ')
            print()
        return ''

    def __repr__(self):
        self.print_board(target='state')
        return ''
