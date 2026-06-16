from itertools import combinations


class Solver:
    def __init__(self, nonogram, do_step=False):
        self.nonogram = nonogram
        self.do_step = do_step

    def solve(self):
        # find all possible combinations, then fill in overlaps
        # horisontal
        changed = True
        iteration = 0
        while changed:
            changed = False
            if self.nonogram.solved:
                return iteration
            for i in range(len(self.nonogram.state)):
                row = self.nonogram.state[i]
                hint = self.nonogram.hints[0][i]
                if all([cell != 0 for cell in row]):
                    continue
                overlaps = [1 for _ in range(len(row))]  # black
                overlaps1 = [1 for _ in range(len(row))]  # white
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
                        changed = True
                    if self.nonogram.state[i][a] == 0 and overlaps1[a] == 1:
                        self.nonogram.move(i, a, -1)
                        changed = True

            if self.do_step:
                print(f"Iteration {iteration} in progress, horizontal solved, state:")
                self.nonogram.print_board(target='state')
                input()

            # vertical
            for j in range(len(self.nonogram.state[0])):
                row = [self.nonogram.state[i][j] for i in range(len(self.nonogram.state))]
                hint = self.nonogram.hints[1][j]
                if all([cell != 0 for cell in row]):
                    continue
                overlaps = [1 for _ in range(len(row))]  # black
                overlaps1 = [1 for _ in range(len(row))]  # white
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
                        changed = True
                    if self.nonogram.state[a][j] == 0 and overlaps1[a] == 1:
                        self.nonogram.move(a, j, -1)
                        changed = True
            iteration += 1

            if self.do_step:
                print(f"Iteration {iteration} completed, current state:")
                self.nonogram.print_board(target='state')
                input()
        return 0

    def _generate_rows(self, length, runs):
        total_black = sum(runs)
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
