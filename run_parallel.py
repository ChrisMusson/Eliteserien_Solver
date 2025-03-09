import subprocess
from concurrent.futures import ProcessPoolExecutor
from itertools import product


def get_dict_combinations(my_dict):
    keys = my_dict.keys()
    for key in keys:
        if my_dict[key] is None or len(my_dict[key]) == 0:
            my_dict[key] = [None]
    all_combs = [dict(zip(my_dict.keys(), values)) for values in product(*my_dict.values())]
    feasible_combs = []
    for comb in all_combs:
        comb_copy = comb.copy()
        if comb_copy.get("am"):
            comb_copy["am_1"] = comb_copy["am"] + 1
            comb_copy["am_2"] = comb_copy["am"] + 2
        c_values = [i for i in comb_copy.values() if i is not None]
        if len(c_values) == len(set(c_values)):
            feasible_combs.append(comb)
    return feasible_combs


def run_script(command):
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        return f'Command "{command}" failed with exit code {e.returncode}.'


def run_parallel_solves(jobs, max_workers=8):
    jobs = [".venv/bin/python solve.py " + " ".join(f"--use_{k} {v}" for k, v in combination.items() if v) for combination in combinations]
    print(len(jobs))

    # Use ProcessPoolExecutor to run commands in parallel
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(run_script, jobs))

    for result in results:
        if result:
            print(result)


if __name__ == "__main__":
    chip_gameweeks = {
        "wc": [],
        "ru": [2, 3, 4, 5, 6],
        "dk": [1, 2, 3, 4, 5, 6],
        "aa": [1, 2, 3, 4, 5, 6],
    }

    combinations = get_dict_combinations(chip_gameweeks)
    run_parallel_solves(combinations)
