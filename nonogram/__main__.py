from nonogram.nonogram import Nonogram
from nonogram.solver import Solver

n = Nonogram()
n.generate_board(rows=40, cols=40, seed=12586, density=0.5, frequency=5)
print(n)
print('Max hints per row:', max(len(h) for h in n.hints[0]))
print('Max hints per col:', max(len(h) for h in n.hints[1]))
s = Solver(n, do_step=True)
s.solve()
