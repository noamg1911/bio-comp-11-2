"""
test_automaton.py - checks that the automaton's rules do what they should.

    python test_automaton.py

Checked for every matrix, after every generation:
    1. every guest appears exactly once (no guest is lost or duplicated, no two guests share a cell)
    2. the table never changes
    3. no guest moves more than one cell per generation
Checked once more:
    4. when nobody moves, Rule A makes every dist[k] equal to the true Chebyshev distance to target k
"""

import numpy as np

from automaton import PartyAutomaton
from constants import (
    MATRICES, NUM_GUESTS, NUM_TARGETS, TABLE, TABLE_HEIGHT, TABLE_WIDTH, GRID_SIZE, DEFAULT_SEED,
)
from metrics import chebyshev

TEST_GENERATIONS = 600              # generations per matrix (enough to reach the stable / moving phase)
MAX_STEP_PER_GENERATION = 1         # a guest moves at most one cell at a time
SETTLE_GENERATIONS = 2 * GRID_SIZE  # more than enough generations for a ripple to cross the room


def true_distance_field(kind, target):
    """The real Chebyshev distance from every cell to the nearest cell of `target` (guest index or table)."""
    code = target if target < NUM_GUESTS else TABLE
    sources = np.argwhere(kind == code)
    rows, cols = np.indices(kind.shape)
    per_source = [np.maximum(np.abs(rows - r), np.abs(cols - c)) for r, c in sources]
    return np.min(per_source, axis=0)


def check_invariants(name, matrix):
    automaton = PartyAutomaton(matrix, seed=DEFAULT_SEED)
    previous = automaton.guest_positions()
    for _ in range(TEST_GENERATIONS):
        automaton.step()
        for guest in range(NUM_GUESTS):
            assert (automaton.kind == guest).sum() == 1, f"{name}: guest {guest} is not on exactly one cell"
        assert (automaton.kind == TABLE).sum() == TABLE_HEIGHT * TABLE_WIDTH, f"{name}: the table changed"
        current = automaton.guest_positions()
        for guest, (p, q) in enumerate(zip(previous, current)):
            assert chebyshev(p, q) <= MAX_STEP_PER_GENERATION, f"{name}: guest {guest} jumped"
        previous = current
    print(f"  OK  {name:12s} {TEST_GENERATIONS} generations: guests conserved, table fixed, steps of <= 1 cell")


def check_rule_a():
    automaton = PartyAutomaton(MATRICES["main"][0], seed=DEFAULT_SEED)
    for _ in range(SETTLE_GENERATIONS):          # apply only Rule A: the guests stay where they are
        automaton.dist = automaton._rule_a_distances()
    for target in range(NUM_TARGETS):
        assert np.array_equal(automaton.dist[target], true_distance_field(automaton.kind, target)), \
            f"dist[{target}] differs from the true distance"
    print(f"  OK  Rule A: after {SETTLE_GENERATIONS} generations every dist[k] equals the true Chebyshev distance")


if __name__ == "__main__":
    print("Checking the automaton's rules:")
    for matrix_name, (matrix, _labels) in MATRICES.items():
        check_invariants(matrix_name, matrix)
    check_rule_a()
    print("All checks passed.")
