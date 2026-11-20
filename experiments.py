"""
experiments.py - the experiments for report items 6 and 7.

    python experiments.py

Item 6(b): MAIN_MATRIX from NUM_SEEDS different random initial placements
           -> output/multi_seed_stress.png  and a summary in output/results.txt
Item 7:    the "interesting" matrices (cities map, chase, wallflowers, knot, Table 1)
           -> output/<name>_snapshots.png, <name>_stress.png, <name>_paths.png, cities_map.png
"""

import os

import numpy as np

import visualize
from automaton import PartyAutomaton
from constants import (
    MATRICES, MAIN_MATRIX, CITY_NAMES, NUM_GENERATIONS, SNAPSHOT_EVERY, DEFAULT_SEED, NUM_SEEDS,
    OUTPUT_DIR, MOVE_PERIOD,
)
from metrics import run_and_measure, describe_cycle, actual_distances

PATH_WINDOW = 300    # trajectories are drawn for the last PATH_WINDOW generations of a run

ITEM_7_RUNS = ["cities", "chase", "wallflowers", "knot", "table1"]   # names in constants.MATRICES


def multi_seed_experiment(report):
    """Item 6(b): does the configuration improve, and does it depend on the initial placement?"""
    runs, cycles = [], []
    for seed in range(NUM_SEEDS):
        result = run_and_measure(PartyAutomaton(MAIN_MATRIX, seed=seed), NUM_GENERATIONS)
        runs.append(result["stress"])
        cycles.append(describe_cycle(result["cycle"]))
    runs = np.array(runs)
    visualize.plot_multi_seed(runs, os.path.join(OUTPUT_DIR, "multi_seed_stress.png"),
                              title=f"MAIN_MATRIX, {NUM_SEEDS} random initial placements")

    initial, final = runs[:, 0], runs[:, -1]
    report.append("=== Item 6(b): MAIN_MATRIX, %d seeds ===" % NUM_SEEDS)
    report.append(f"initial stress: mean {initial.mean():.2f}, min {initial.min():.2f}, max {initial.max():.2f}")
    report.append(f"final stress:   mean {final.mean():.2f}, min {final.min():.2f}, max {final.max():.2f}")
    report.append(f"improved in {(final < initial).sum()} of {NUM_SEEDS} runs")
    report.append(f"correlation(initial, final) = {np.corrcoef(initial, final)[0, 1]:.2f}")
    for seed in range(NUM_SEEDS):
        report.append(f"  seed {seed:2d}: {initial[seed]:6.2f} -> {final[seed]:5.2f}   {cycles[seed]}")
    report.append("")


def item_7_experiment(name, report):
    """Run one 'interesting' matrix (by its name in MATRICES) and save its figures."""
    matrix, names = MATRICES[name]
    automaton = PartyAutomaton(matrix, seed=DEFAULT_SEED)
    result = run_and_measure(automaton, NUM_GENERATIONS, snapshot_every=SNAPSHOT_EVERY)
    prefix = os.path.join(OUTPUT_DIR, name)

    visualize.save_snapshots(result["snapshots"], result["stress"], prefix + "_snapshots.png",
                             names=names, suptitle=f"matrix '{name}', seed {DEFAULT_SEED}")
    visualize.plot_stress(result["stress"], prefix + "_stress.png", title=f"Configuration quality - '{name}'")
    visualize.plot_trajectories(result["positions"], prefix + "_paths.png",
                                NUM_GENERATIONS - PATH_WINDOW, NUM_GENERATIONS, names=names,
                                kind=automaton.kind, title=f"'{name}': paths in the last {PATH_WINDOW} generations")
    visualize.plot_guest_unhappiness(result["unhappiness"], prefix + "_unhappiness.png", names=names,
                                     title=f"'{name}': unhappiness of each guest and the total")
    if name == "cities":
        visualize.plot_cities(automaton.kind, automaton.generation, os.path.join(OUTPUT_DIR, "cities_map.png"),
                              CITY_NAMES, names)

    report.append(f"=== Item 7: '{name}' (seed {DEFAULT_SEED}) ===")
    report.append(f"stress: {result['stress'][0]:.2f} -> {result['stress'][-1]:.2f}")
    report.append("dynamics: " + describe_cycle(result["cycle"]))
    report.append("final actual distances (rows = guests, columns = A..E, T):")
    report.append(str(actual_distances(automaton)))
    report.append("")


def main():
    visualize.use_file_backend()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report = [f"(one move cycle = {MOVE_PERIOD} generations; {NUM_GENERATIONS} generations per run)", ""]
    multi_seed_experiment(report)
    for name in ITEM_7_RUNS:
        item_7_experiment(name, report)
    with open(os.path.join(OUTPUT_DIR, "results.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print("\n".join(report))


if __name__ == "__main__":
    main()
