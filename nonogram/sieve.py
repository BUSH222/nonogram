from nonogram.nonogram import Nonogram
from nonogram.solver import Solver
import argparse


def sieve(start, stop, size, density, freq, number_limit=5, verbose=True):
    seeds = []
    for seed in range(start, stop):
        n = Nonogram()
        n.generate_board(rows=size, cols=size, seed=seed, density=density, frequency=freq)
        if len(max(n.hints[0], key=len)) > number_limit or len(max(n.hints[1], key=len)) > number_limit:
            continue
        s = Solver(n, do_step=False)
        result = s.solve()
        if result:
            if verbose:
                print(result, end=' ', flush=True)
            seeds.append([seed, result])
        else:
            if verbose:
                print('.', end='', flush=True)
    return seeds


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='ProgramName',
        description='What the program does',
        epilog='Text at the bottom of help')
    parser.add_argument('--start', '-s', type=int, default=0, help='Start seed')
    parser.add_argument('--stop', '-t', type=int, default=1000, help='Stop seed')
    parser.add_argument('--size', '-sz', type=int, help='Size of the grid')
    parser.add_argument('--sizex', '-sx', type=int, help='Size of the grid (x)')
    parser.add_argument('--sizey', '-sy', type=int, help='Size of the grid (y)')
    parser.add_argument('--density', '-d', type=float, default=0.5, help='Density of the grid')
    parser.add_argument('--freq', '-f', type=int, default=6, help='Frequency of the grid')
    parser.add_argument('--limit', '-l', type=int, default=5, help='Max hints per row/col')
    parser.add_argument('savetofile', nargs='?', type=str, help='Save results to file')
    args = parser.parse_args()

    if args.sizex is None:
        args.sizex = args.size
    if args.sizey is None:
        args.sizey = args.size
    results = sieve(args.start, args.stop, args.sizex, args.density, args.freq, number_limit=5)

    print("Seeds that can be solved:", results)
    print("Hardest seed:", max(results, key=lambda x: x[1]))
    print("Easiest seed:", min(results, key=lambda x: x[1]))

    if args.savetofile:
        with open(args.savetofile, 'w') as f:
            for seed, result in results:
                f.write(f"{seed},{result}\n")
