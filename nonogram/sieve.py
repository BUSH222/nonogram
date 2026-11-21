import argparse

from nonogram.nonogram import Nonogram
from nonogram.solver import Solver

try:
    import tqdm
except ImportError:
    tqdm = None


def sieve(start, stop, rows, cols, density, freq, number_limit=5, verbose=True, use_tqdm=False):
    seeds = []
    if use_tqdm:
        seed_range = tqdm.tqdm(range(start, stop), desc="Processing seeds", unit="seeds")
    else:
        seed_range = range(start, stop)
    for seed in seed_range:
        n = Nonogram()
        n.generate_board(rows=rows, cols=cols, seed=seed, density=density, frequency=freq)
        if len(max(n.hints[0], key=len)) > number_limit or len(max(n.hints[1], key=len)) > number_limit:
            continue
        s = Solver(n, do_step=False)
        result = s.solve()
        if result is not None:
            if verbose and not use_tqdm:
                print(result, end=" ", flush=True)
            seeds.append([seed, result])
        else:
            if verbose and not use_tqdm:
                print(".", end="", flush=True)
    return seeds


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="ProgramName", description="What the program does", epilog="Text at the bottom of help"
    )
    parser.add_argument("--start", "-s", type=int, default=0, help="Start seed")
    parser.add_argument("--stop", "-t", type=int, default=1000, help="Stop seed")
    parser.add_argument("--size", "-sz", type=int, help="Size of the grid")
    parser.add_argument("--sizex", "-sx", type=int, help="Width of the grid (columns)")
    parser.add_argument("--sizey", "-sy", type=int, help="Height of the grid (rows)")
    parser.add_argument("--density", "-d", type=float, default=0.5, help="Density of the grid")
    parser.add_argument("--freq", "-f", type=int, default=6, help="Frequency of the grid")
    parser.add_argument("--limit", "-l", type=int, default=5, help="Max hints per row/col")
    parser.add_argument("-saveto", nargs="?", type=str, help="Save results to file")
    args = parser.parse_args()

    if args.sizex is None:
        args.sizex = args.size
    if args.sizey is None:
        args.sizey = args.size
    if args.sizex is None or args.sizey is None:
        parser.error("give --size, or both --sizex and --sizey")
    results = sieve(args.start, args.stop, args.sizey, args.sizex, args.density, args.freq, number_limit=args.limit)

    print("Seeds that can be solved:", results)
    try:
        print("Hardest seed:", max(results, key=lambda x: x[1]))
        print("Easiest seed:", min(results, key=lambda x: x[1]))
    except ValueError:
        print("no solvable seeds")

    if args.saveto:
        with open(args.saveto, "w") as f:
            for seed, result in results:
                f.write(f"{seed},{result}\n")
