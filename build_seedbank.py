"""Build the seed bank behind the "From seedbank" button.

For each size, sieves seeds upward from 0 until it has found the target number of line-solvable puzzles, then writes
seedbank/<rows>x<cols>.json holding the seeds plus the generation settings they are only valid with. Sizes run in
parallel, one process each.

    uv run python build_seedbank.py            # rebuild every size
    uv run python build_seedbank.py 30x30 5x5  # rebuild only these
"""

import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

from nonogram.sieve import default_frequency, sieve

SEEDBANK_DIR = "seedbank"
DENSITY = 0.5
RANDOM_FUNCTION = "perlin2d"  # what sieve() generates with
NUMBER_LIMIT = 5

# "<rows>x<cols>": number of solvable seeds to store
TARGETS = {f"{r}x{c}": 10000 for r in (5, 10, 15) for c in (5, 10, 15)} | {
    "20x20": 2000,
    "25x20": 2000,
    "20x25": 2000,
    "30x30": 1500,
}


def build(size):
    rows, cols = map(int, size.split("x"))
    frequency = default_frequency(rows, cols)
    started = time.time()
    seeds = sieve(0, None, rows, cols, DENSITY, frequency, NUMBER_LIMIT, verbose=False, target=TARGETS[size])
    bank = {
        "rows": rows,
        "cols": cols,
        "density": DENSITY,
        "random_function": RANDOM_FUNCTION,
        "frequency": frequency,
        "number_limit": NUMBER_LIMIT,
        "seeds": seeds,  # [seed, difficulty (solver passes)]
    }
    with open(os.path.join(SEEDBANK_DIR, f"{size}.json"), "w") as f:
        json.dump(bank, f, separators=(",", ":"))
    return size, len(seeds), seeds[-1][0] + 1, time.time() - started


if __name__ == "__main__":
    sizes = sys.argv[1:] or list(TARGETS)
    unknown = [s for s in sizes if s not in TARGETS]
    if unknown:
        sys.exit(f"unknown sizes {unknown}; known: {', '.join(TARGETS)}")
    os.makedirs(SEEDBANK_DIR, exist_ok=True)
    # Biggest boards first: they take longest, so starting them last would leave the other cores idle at the end.
    sizes.sort(key=lambda s: -math.prod(map(int, s.split("x"))))
    with ProcessPoolExecutor() as pool:
        for future in as_completed([pool.submit(build, s) for s in sizes]):
            size, found, scanned, seconds = future.result()
            print(f"{size}: {found} seeds (scanned {scanned}) in {seconds / 60:.1f} min", flush=True)
