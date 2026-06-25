from itertools import combinations


class Solver:
    def __init__(self, nonogram, do_step=False):
        self.nonogram = nonogram
        self.do_step = do_step

    def solve(self):
        rows, cols = len(self.nonogram.state), len(self.nonogram.state[0])
        dirty_rows, dirty_cols = set(range(rows)), set(range(cols))
        iteration = 0

        while dirty_rows or dirty_cols:
            if self.nonogram.solved:
                return iteration

            next_dirty_cols = set()
            for i in dirty_rows:
                row = self.nonogram.state[i]
                if all(cell != 0 for cell in row):
                    continue
                overlaps, overlaps1 = self._line_overlap(row, self.nonogram.hints[0][i])
                for a, (b, w) in enumerate(zip(overlaps, overlaps1)):
                    if row[a] == 0 and b == 1:
                        self.nonogram.move(i, a, 1)
                        next_dirty_cols.add(a)
                    elif row[a] == 0 and w == 1:
                        self.nonogram.move(i, a, -1)
                        next_dirty_cols.add(a)

            next_dirty_rows = set()
            for j in dirty_cols | next_dirty_cols:   # include cols just touched too
                col = [self.nonogram.state[i][j] for i in range(rows)]
                if all(cell != 0 for cell in col):
                    continue
                overlaps, overlaps1 = self._line_overlap(col, self.nonogram.hints[1][j])
                for a, (b, w) in enumerate(zip(overlaps, overlaps1)):
                    if col[a] == 0 and b == 1:
                        self.nonogram.move(a, j, 1)
                        next_dirty_rows.add(a)
                    elif col[a] == 0 and w == 1:
                        self.nonogram.move(a, j, -1)
                        next_dirty_rows.add(a)

            dirty_rows, dirty_cols = next_dirty_rows, next_dirty_cols
            iteration += 1
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

    def _line_overlap(self, line, hints):
        # generate all possible lines for hints, then find overlaps
        overlaps = [1 for _ in range(len(line))]  # black
        overlaps1 = [1 for _ in range(len(line))]  # white
        for r in self._generate_rows(len(line), hints):
            # conformity check
            skiprow = False
            for p in range(len(line)):
                if line[p] == 1 and r[p] != 1:
                    skiprow = True
                    break
                if line[p] == -1 and r[p] != 0:
                    skiprow = True
                    break
            if skiprow:
                continue

            for j in range(len(line)):
                overlaps[j] &= r[j]
                overlaps1[j] &= (1-r[j])
        return overlaps, overlaps1
