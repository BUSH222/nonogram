from main import Nonogram, Solver

seeds = []
size = 15
density = 0.5

for seed in range(10000, 20000):
    n = Nonogram()
    n.generate_board(rows=size, cols=size, seed=seed, density=density)
    if len(max(n.hints[0], key=len)) > 5 or len(max(n.hints[1], key=len)) > 5: # too many runs, skip
        continue  
    s = Solver(n, do_step=False)
    result = s.solve()
    if result:
        print(result, end=' ', flush=True)
        seeds.append([seed, result])
    else:
        print('.', end='', flush=True)

print("Seeds that can be solved:", seeds)
print("Hardest seed:", max(seeds, key=lambda x: x[1]))


# Hardest seed: [7934, 18]
# Hardest seed: [12586, 22]