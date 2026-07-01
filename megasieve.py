from nonogram.sieve import sieve
import os


rows = list(range(3, 41))
cols = list(range(3, 41))


def freq(r, c):
    if r <= 5 or c <= 5:
        return 8
    if r <= 10 or c <= 10:
        return 7
    if r <= 20 or c <= 20:
        return 6
    else:
        return 5


seed_limit = 10000
seed_limit_exceptions = {"5x5": 100000,
                         "10x10": 100000,
                         "15x15": 1000000,
                         "20x20": 1000000,
                         "25x25": 100000,
                         "30x30": 50000,
                         "35x35": 50000,
                         "40x40": 50000}
start_at = [3, 3]
results_folder = "sieve_results"
os.makedirs(results_folder, exist_ok=True)

for r in rows:
    for c in cols:
        if r < start_at[0] or (r == start_at[0] and c < start_at[1]):
            continue
        print(f"Processing {r}x{c} grid...")
        real_seed_limit = seed_limit_exceptions.get(f"{r}x{c}", seed_limit)
        results = sieve(0, real_seed_limit, r, 0.5, freq(r, c), number_limit=5, verbose=True, use_tqdm=False)
        with open(os.path.join(results_folder, f"{r}x{c}_{freq(r, c)}_{real_seed_limit}.txt"), "w") as f:
            for seed, res in results:
                f.write(f"{seed}, {res}\n")
