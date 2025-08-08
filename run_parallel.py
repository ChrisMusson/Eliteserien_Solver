import os
from concurrent.futures import ProcessPoolExecutor
from itertools import product

import pandas as pd

from solve import solve_regular


def get_dict_combinations(my_dict):
    keys = my_dict.keys()
    for key in keys:
        if my_dict[key] is None or len(my_dict[key]) == 0:
            my_dict[key] = [None]
    all_combs = [dict(zip(my_dict.keys(), values, strict=False)) for values in product(*my_dict.values())]
    feasible_combs = []
    for comb in all_combs:
        c_values = [i for i in comb.values() if i is not None]
        if len(c_values) == len(set(c_values)):
            feasible_combs.append({k: v for k, v in comb.items() if v is not None})
        # else we have a duplicate
    return feasible_combs


def run_parallel_solves(chip_combinations, max_workers=None):
    if not max_workers:
        max_workers = os.cpu_count() - 2

    # you can add any options you want to pass to the solve function here
    options = {"randomized": True}

    args = []
    for combination in chip_combinations:
        args.append({**options, **combination})

    # Use ProcessPoolExecutor to run commands in parallel
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(solve_regular, args))

    df = pd.concat(results).sort_values(by="score", ascending=False).reset_index(drop=True)
    df = df.drop("iter", axis=1)
    print(df)

    # you can save the results to a csv file if you want to, by uncommenting the line below
    df.to_csv("chip_solve.csv", encoding="utf-8", index=False)


if __name__ == "__main__":
    # edit the gameweeks you want to have chips available in here.
    # in this example it means it will run solves for 10 chips combinations:
    # no chips, aa18, aa19, aa20, dk18, dk19, aa18dk19, aa19dk18, aa20dk18, aa20dk19
    # note that this is the 3 bb options multiplied by the 4 fh options, minus the invalid combinations a18dk18 and aa19dk19
    chip_gameweeks = {
        "use_aa": [None, 18, 19, 20],
        "use_wc": [],
        "use_dk": [None, 18, 19],
        "use_ru": [],
    }

    combinations = get_dict_combinations(chip_gameweeks)
    run_parallel_solves(combinations)
