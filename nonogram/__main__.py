from nonogram.nonogram import Nonogram
from nonogram.solver import Solver

n = Nonogram()
n.generate_board(rows=15, cols=15, seed=4, density=0.5)
print(n)
s = Solver(n, do_step=True)
s.solve()
