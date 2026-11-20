"""
metrics.py - measuring the quality of a configuration (report item 6).

This is an OUTSIDE OBSERVER: it reads the guests' positions and computes the true distances.
It is not part of the automaton's rules and the guests never see it.

Quality = STRESS = the mean absolute error between the actual and the ideal distances:

    Stress(t) = (1 / |P|) * sum over (i, j) in P of | d_t(i, j) - ideal[i][j] |

    P       = all ordered pairs (guest i, target j) with j != i and ideal[i][j] != -1,
              where a target is another guest or the table
    d_t     = Chebyshev distance at generation t; for the table, the distance to its NEAREST cell

Lower is better; Stress = 0 means every guest is exactly at every ideal distance.
Its unit is cells: "on average, each preference is off by Stress cells".
"""

import numpy as np

from constants import (
    NUM_GUESTS, NUM_TARGETS, TABLE_INDEX, TABLE, INDIFFERENT, MOVE_PERIOD,
)


def chebyshev(p, q):
    """Chebyshev distance between two cells p = (row, col) and q = (row, col)."""
    return max(abs(p[0] - q[0]), abs(p[1] - q[1]))


def distance_to_table(position, table_cells):
    """Chebyshev distance from a cell to the nearest table cell."""
    return int(np.max(np.abs(table_cells - np.array(position)), axis=1).min())


def actual_distances(automaton):
    """Return a NUM_GUESTS x NUM_TARGETS array of the actual distances (same layout as the ideal matrix)."""
    positions = automaton.guest_positions()
    table_cells = np.argwhere(automaton.kind == TABLE)
    actual = np.zeros((NUM_GUESTS, NUM_TARGETS), dtype=int)
    for i in range(NUM_GUESTS):
        for j in range(NUM_GUESTS):
            actual[i, j] = chebyshev(positions[i], positions[j])
        actual[i, TABLE_INDEX] = distance_to_table(positions[i], table_cells)
    return actual


def pair_mask(ideal):
    """True for the ordered pairs (i, j) that count in the stress (j != i and not indifferent)."""
    ideal = np.asarray(ideal)
    mask = ideal != INDIFFERENT
    for i in range(NUM_GUESTS):
        mask[i, i] = False
    return mask


def stress(automaton):
    """The quality measure defined at the top of this file (lower is better)."""
    mask = pair_mask(automaton.ideal)
    errors = np.abs(actual_distances(automaton) - automaton.ideal)
    return float(errors[mask].mean())


def guest_unhappiness(automaton):
    """Per-guest unhappiness (sum of |actual - ideal| over the targets that guest cares about)."""
    mask = pair_mask(automaton.ideal)
    errors = np.abs(actual_distances(automaton) - automaton.ideal)
    return [int(errors[i][mask[i]].sum()) for i in range(NUM_GUESTS)]


def run_and_measure(automaton, num_generations, snapshot_every=None, detect_cycle=True):
    """
    Run the automaton and record the stress after every generation.

    Returns a dict with:
        "stress"     list, stress[t] = stress at generation t (t = 0..num_generations)
        "snapshots"  dict generation -> copy of the `kind` array (every `snapshot_every` generations)
        "positions"  list, positions[t] = guest positions at generation t
        "unhappiness" list, unhappiness[t] = per-guest unhappiness at generation t
        "cycle"      None, or (first_generation, period) if the full state repeated
                     (the automaton is deterministic, so from then on it repeats forever;
                     period == 1 at a move-cycle boundary would mean a fixed point)
    """
    stresses = [stress(automaton)]
    positions = [automaton.guest_positions()]
    unhappiness = [guest_unhappiness(automaton)]
    snapshots = {0: automaton.kind.copy()} if snapshot_every else {}
    seen = {automaton.state_key(): 0} if detect_cycle else None
    cycle = None

    for _ in range(num_generations):
        automaton.step()
        t = automaton.generation
        stresses.append(stress(automaton))
        positions.append(automaton.guest_positions())
        unhappiness.append(guest_unhappiness(automaton))
        if snapshot_every and t % snapshot_every == 0:
            snapshots[t] = automaton.kind.copy()
        if detect_cycle and cycle is None:
            key = automaton.state_key()
            if key in seen:
                cycle = (seen[key], t - seen[key])
            else:
                seen[key] = t

    return {"stress": stresses, "snapshots": snapshots, "positions": positions,
            "unhappiness": unhappiness, "cycle": cycle}


def describe_cycle(cycle):
    """Human-readable description of the result of cycle detection."""
    if cycle is None:
        return "no repetition of the full state was found"
    start, period = cycle
    # A full-state period of exactly one move cycle means nobody moves any more:
    # a guest can move at most once per cycle, so it could not have come back.
    if period == MOVE_PERIOD:
        return f"reached a STABLE configuration (fixed point) at generation {start}"
    return (f"became PERIODIC from generation {start}: the state repeats every {period} generations "
            f"(= {period // MOVE_PERIOD} move cycles)")
