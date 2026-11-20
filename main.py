"""
main.py - one run of the Party Planner automaton (Question 2).

    python main.py                      run MAIN_MATRIX for 2000 generations, save the results in output/
    python main.py --live               the same run, shown live in a window (graphical interface)
    python main.py --matrix cities      another matrix: main, table1, cities, chase, wallflowers, knot
    python main.py --seed 7             a different random initial placement
    (the options can be combined, e.g.  python main.py --matrix chase --live)

What a (non-live) run does:
    1. builds the automaton (generation 0 = random placement)
    2. runs NUM_GENERATIONS generations, measuring the stress after each one
    3. saves into output/ (file names start with the matrix name, e.g. main_...):
         <name>_snapshots.png   the room at generation 0 and every 100 generations   (report item 5)
         <name>_positions.txt   the guests' positions at the same generations         (report item 5)
         <name>_stress.png      stress as a function of the generation                 (report item 6)
         <name>_field_*.png     heat maps of two distance fields at the end            (illustrates Rule A)
    4. prints a short summary
"""

import argparse
import os

import visualize
from automaton import PartyAutomaton
from constants import MATRICES, NUM_GENERATIONS, SNAPSHOT_EVERY, DEFAULT_SEED, OUTPUT_DIR, TABLE_INDEX
from metrics import run_and_measure, describe_cycle, actual_distances

FIELDS_TO_DRAW = (0, TABLE_INDEX)   # distance fields saved as heat maps: guest A and the table


def write_positions(result, path, names):
    """Text printout of every guest's (row, col) at every snapshot generation."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("generation  stress   " + "  ".join(f"{n:>10}" for n in names) + "\n")
        for gen in sorted(result["snapshots"]):
            cells = "  ".join(f"{str(p):>10}" for p in result["positions"][gen])
            f.write(f"{gen:>10}  {result['stress'][gen]:6.2f}   {cells}\n")


def main():
    parser = argparse.ArgumentParser(description="Party Planner cellular automaton (Maman 11, Q2)")
    parser.add_argument("--matrix", choices=sorted(MATRICES), default="main")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--live", action="store_true", help="show the run in a window")
    args = parser.parse_args()

    matrix, names = MATRICES[args.matrix]
    automaton = PartyAutomaton(matrix, seed=args.seed)

    # --- live mode: just show the automaton in a window, generation after generation
    if args.live:
        visualize.live_animation(automaton, NUM_GENERATIONS, names)
        return

    # --- file mode: run, measure, save figures and printouts
    visualize.use_file_backend()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    prefix = os.path.join(OUTPUT_DIR, args.matrix)

    result = run_and_measure(automaton, NUM_GENERATIONS, snapshot_every=SNAPSHOT_EVERY)

    visualize.save_snapshots(result["snapshots"], result["stress"], prefix + "_snapshots.png",
                             names=names, suptitle=f"matrix '{args.matrix}', seed {args.seed}")
    write_positions(result, prefix + "_positions.txt", names)
    visualize.plot_stress(result["stress"], prefix + "_stress.png",
                          title=f"Configuration quality - matrix '{args.matrix}', seed {args.seed}")
    for target in FIELDS_TO_DRAW:
        visualize.plot_distance_field(automaton, target, f"{prefix}_field_{target}.png", names)

    print(f"matrix '{args.matrix}', seed {args.seed}")
    print(f"stress: generation 0 = {result['stress'][0]:.2f}, "
          f"generation {NUM_GENERATIONS} = {result['stress'][-1]:.2f}")
    print("dynamics:", describe_cycle(result["cycle"]))
    print("actual distances at the end (rows = guests, columns = the other guests and T):")
    print(actual_distances(automaton))
    print(f"results saved in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
