"""
automaton.py - the Party Planner cellular automaton (Question 2). No graphics here.

------------------------------------------------------------------------------------------
THE CELL STATE
Every cell of the GRID_SIZE x GRID_SIZE lattice holds a vector with these fields:

    kind      what is on the cell: EMPTY, TABLE, or a guest index 0..4
    dist[k]   k = 0..5: the cell's estimate of its Chebyshev distance to guest k (k = 5: the table).
              An integer in 0..D_MAX (D_MAX means "unknown / very far").
    phase     a clock 0..MOVE_PERIOD-1. It has the same value in all cells and advances by 1
              every generation, so every cell knows which phase of the move cycle it is in.
    intent    a guest's requested move: NO_DIRECTION or a direction 0..7
    accept    an empty cell's accepted incoming guest: NO_DIRECTION or the direction 0..7
              in which that guest is standing

Every field takes finitely many values, so the set of states is finite.

THE NEIGHBORHOOD: Moore, radius 1 (the 8 surrounding cells). Cells outside the lattice are walls.

THE RULES (applied to all cells at once, the new generation is computed only from the old one):
    Rule A - distance propagation, every generation:
        dist[k] = 0 if target k is on me, otherwise min(over the 8 neighbors of dist[k]) + 1
    Rule B - movement, a 3-phase cycle:
        phase 0 (intent): a guest compares its unhappiness on its own cell with its unhappiness
                          on every empty neighbor (read from the neighbor's dist vector) and
                          requests the best neighbor if it is strictly better.
        phase 1 (accept): an empty cell accepts ONE guest that requested it (the lowest index).
        phase 2 (move):   the accepted guest appears on the empty cell and disappears from its old cell.
------------------------------------------------------------------------------------------

A NOTE ON NUMPY (for readers new to it)
Instead of looping over the cells one by one, the code works on whole arrays at once:
  * `kind` is a 2D array: kind[r, c] is the kind of the cell in row r, column c.
  * `dist` is a 3D array: dist[k, r, c] is the distance field of target k at cell (r, c).
  * An expression like `kind == EMPTY` gives a 2D True/False array ("a mask") - one answer per cell.
  * `np.where(mask, a, b)` picks, for every cell separately, a where mask is True and b where it is False.
  * `shift(arr, dr, dc, fill)` gives, for every cell, the value of its neighbor at offset (dr, dc).
So each line of numpy below is "the same local rule, applied to every cell simultaneously".
This is exactly the synchronous update of a cellular automaton.
"""

import numpy as np

from constants import (
    GRID_SIZE, TABLE_TOP, TABLE_LEFT, TABLE_HEIGHT, TABLE_WIDTH,
    NUM_GUESTS, NUM_TARGETS, TABLE_INDEX,
    EMPTY, TABLE, WALL,
    SOURCE_DISTANCE, STEP_COST, D_MAX,
    INDIFFERENT, MIN_IDEAL, MAX_IDEAL, CLOSEST_POSSIBLE,
    PHASE_INTENT, PHASE_ACCEPT, PHASE_MOVE, MOVE_PERIOD, INITIAL_PHASE,
    DIRECTIONS, NO_DIRECTION, OPPOSITE,
)


# ======================================================================================
# helper: looking at a neighbor
# ======================================================================================
def shift(arr, dr, dc, fill):
    """
    Return an array `out` of the same shape as `arr` where, for every cell (r, c):
        out[..., r, c] = arr[..., r + dr, c + dc]
    i.e. every cell receives the value of its neighbor at offset (dr, dc).
    Neighbors outside the lattice (walls) get the value `fill`.

    Works for 2D arrays (kind, intent, ...) and for the 3D dist array (shifts the last two axes).
    """
    # np.pad adds a frame of width 1 filled with `fill` around the last two axes
    # (the leading axis of a 3D array - the target index k - is not padded).
    pad_width = [(0, 0)] * (arr.ndim - 2) + [(1, 1), (1, 1)]
    padded = np.pad(arr, pad_width, mode="constant", constant_values=fill)
    rows, cols = arr.shape[-2], arr.shape[-1]
    # In the padded array, the original cell (r, c) sits at (r + 1, c + 1),
    # so its neighbor (r + dr, c + dc) sits at (r + 1 + dr, c + 1 + dc).
    return padded[..., 1 + dr: 1 + dr + rows, 1 + dc: 1 + dc + cols]


# ======================================================================================
# input validation
# ======================================================================================
def validate_matrix(ideal):
    """
    Check that the ideal-distance matrix has the right shape and allowed values, and return it as numpy
    with every off-diagonal 0 replaced by CLOSEST_POSSIBLE (decision D2).
    """
    ideal = np.array(ideal, dtype=int)
    expected_shape = (NUM_GUESTS, NUM_TARGETS)
    if ideal.shape != expected_shape:
        raise ValueError(f"The ideal-distance matrix must have shape {expected_shape} "
                         f"(rows = guests, columns = guests + table), got {ideal.shape}.")
    allowed = (ideal == INDIFFERENT) | ((ideal >= MIN_IDEAL) & (ideal <= MAX_IDEAL))
    if not allowed.all():
        bad = [(int(i), int(j), int(ideal[i, j])) for i, j in np.argwhere(~allowed)]
        raise ValueError(f"Matrix values must be {INDIFFERENT} (indifferent) or between "
                         f"{MIN_IDEAL} and {MAX_IDEAL} (they are distances in cells). "
                         f"Bad entries (row, column, value): {bad}")

    # Decision D2: an input 0 means "as close as possible". Two guests can't share a cell and nobody
    # can stand on the table, so the closest possible distance is CLOSEST_POSSIBLE (1). We store it as 1,
    # so that 0 always means "on me" (as in Rule A) and a satisfied "next to" wish counts as 0 error.
    # (Mostly this changes only the measured error, not the moves: a guest only stands on cells whose
    #  distance to the others is >= 1. The exception: for one generation after a guest moves, the cell it
    #  left still shows distance 0 to it, and the two versions judge that "ghost" reading differently.)
    off_diagonal = ~np.eye(NUM_GUESTS, NUM_TARGETS, dtype=bool)   # the diagonal (a guest and itself) is ignored
    ideal = np.where(off_diagonal & (ideal == MIN_IDEAL), CLOSEST_POSSIBLE, ideal)
    return ideal


# ======================================================================================
# the automaton
# ======================================================================================
class PartyAutomaton:
    """The lattice and its state. Call step() to advance one generation."""

    def __init__(self, ideal, seed):
        self.ideal = validate_matrix(ideal)
        self.generation = 0

        # ---- field `kind`: start with an empty floor and put the table in its fixed place
        self.kind = np.full((GRID_SIZE, GRID_SIZE), EMPTY, dtype=int)
        self.kind[TABLE_TOP:TABLE_TOP + TABLE_HEIGHT, TABLE_LEFT:TABLE_LEFT + TABLE_WIDTH] = TABLE

        # ---- generation 0: put the guests on random, distinct, empty cells
        rng = np.random.default_rng(seed)
        free_cells = np.argwhere(self.kind == EMPTY)            # list of (row, col) of all empty cells
        chosen = rng.choice(len(free_cells), size=NUM_GUESTS, replace=False)
        for guest, cell_number in enumerate(chosen):
            r, c = free_cells[cell_number]
            self.kind[r, c] = guest

        # ---- field `dist`: nothing is known yet -> every distance is "unknown" (D_MAX)
        self.dist = np.full((NUM_TARGETS, GRID_SIZE, GRID_SIZE), D_MAX, dtype=int)

        # ---- fields `phase`, `intent`, `accept`
        self.phase = np.full((GRID_SIZE, GRID_SIZE), INITIAL_PHASE, dtype=int)
        self.intent = np.full((GRID_SIZE, GRID_SIZE), NO_DIRECTION, dtype=int)
        self.accept = np.full((GRID_SIZE, GRID_SIZE), NO_DIRECTION, dtype=int)

    # ----------------------------------------------------------------------------------
    # Rule A: distance propagation
    # ----------------------------------------------------------------------------------
    def _rule_a_distances(self):
        """
        For every target k and every cell:
            new dist[k] = SOURCE_DISTANCE           if target k is on the cell
                          min(neighbors' dist[k]) + STEP_COST, capped at D_MAX   otherwise
        The cell does not use its own old value - so when a guest walks away, the old
        (too small) numbers are corrected by the wave coming from the guest's new place.
        """
        # smallest dist[k] among the 8 neighbors, for all k and all cells at once
        neighbor_min = np.full_like(self.dist, D_MAX)
        for dr, dc in DIRECTIONS:
            neighbor_min = np.minimum(neighbor_min, shift(self.dist, dr, dc, D_MAX))
        new_dist = np.minimum(neighbor_min + STEP_COST, D_MAX)

        # sources: guest k's own cell has distance 0 to guest k; table cells have distance 0 to the table
        for guest in range(NUM_GUESTS):
            new_dist[guest][self.kind == guest] = SOURCE_DISTANCE
        new_dist[TABLE_INDEX][self.kind == TABLE] = SOURCE_DISTANCE
        return new_dist

    # ----------------------------------------------------------------------------------
    # unhappiness of the guest standing on each cell, as seen through a dist vector
    # ----------------------------------------------------------------------------------
    def _unhappiness(self, dist_view, ideal_here, cares):
        """
        dist_view[k, r, c]  : the distance vector the guest on (r, c) is looking at
                              (its own cell's vector, or one of its neighbors' vectors)
        ideal_here[k, r, c] : ideal distance from target k of the guest standing on (r, c)
        cares[k, r, c]      : True if that guest cares about target k (not -1, not itself)
        Returns U[r, c] = sum over the cared-about targets of |dist - ideal|.
        """
        return np.where(cares, np.abs(dist_view - ideal_here), 0).sum(axis=0)

    # ----------------------------------------------------------------------------------
    # Rule B, phase 0: intent
    # ----------------------------------------------------------------------------------
    def _phase_intent(self):
        """
        Phase 0. Every guest compares its unhappiness on its own cell with its unhappiness on each
        EMPTY neighbor, and requests the best neighbor if it is strictly better than staying.
        Returns the new `intent` field (a direction 0..7, or NO_DIRECTION).
        """
        is_guest = self.kind >= 0
        guest_id = np.where(is_guest, self.kind, 0)   # guest index per cell (0 is a dummy for non-guests)

        # ideal_here[k, r, c] = ideal[guest on (r, c)][k]
        # i.e. every guest cell gets its own row of the matrix. Example: if guest B (index 1) stands on
        # (5, 7), then ideal_here[:, 5, 7] is row B of the matrix: B's ideal distance to A, B, C, D, E, T.
        # self.ideal[guest_id] has shape (rows, cols, 6); moveaxis puts the "6" first, like in `dist`.
        ideal_here = np.moveaxis(self.ideal[guest_id], -1, 0)
        target_index = np.arange(NUM_TARGETS)[:, None, None]   # 0..5, shaped to broadcast over the grid
        # cares[k, r, c] = does the guest on (r, c) care about target k? (not -1, and not itself)
        cares = (ideal_here != INDIFFERENT) & (target_index != guest_id[None, :, :])

        # A guest moves only after the information from every target it cares about has arrived
        # (no "unknown" value in its own vector). This is a local test on the cell's own state.
        informed = ~np.any(cares & (self.dist >= D_MAX), axis=0)

        best_u = self._unhappiness(self.dist, ideal_here, cares)   # unhappiness of staying
        best_dir = np.full_like(self.kind, NO_DIRECTION)
        for d, (dr, dc) in enumerate(DIRECTIONS):                  # fixed order = tie-break (D5)
            neighbor_kind = shift(self.kind, dr, dc, WALL)
            neighbor_dist = shift(self.dist, dr, dc, D_MAX)
            u = self._unhappiness(neighbor_dist, ideal_here, cares)
            better = (neighbor_kind == EMPTY) & (u < best_u)       # strictly better, enterable cell
            best_u = np.where(better, u, best_u)
            best_dir = np.where(better, d, best_dir)

        return np.where(is_guest & informed, best_dir, NO_DIRECTION)

    # ----------------------------------------------------------------------------------
    # Rule B, phase 1: accept
    # ----------------------------------------------------------------------------------
    def _phase_accept(self):
        """An empty cell accepts the requesting neighbor guest with the lowest index (if any)."""
        accept = np.full_like(self.kind, NO_DIRECTION)
        accepted_guest = np.full_like(self.kind, NUM_GUESTS)   # "no guest yet" (larger than any index)
        for d, (dr, dc) in enumerate(DIRECTIONS):
            neighbor_kind = shift(self.kind, dr, dc, WALL)
            neighbor_intent = shift(self.intent, dr, dc, NO_DIRECTION)
            # the neighbor in direction d is a guest whose intent points back at me
            wants_me = (neighbor_kind >= 0) & (neighbor_intent == OPPOSITE[d])
            take = (self.kind == EMPTY) & wants_me & (neighbor_kind < accepted_guest)
            accept = np.where(take, d, accept)
            accepted_guest = np.where(take, neighbor_kind, accepted_guest)
        return accept

    # ----------------------------------------------------------------------------------
    # Rule B, phase 2: move
    # ----------------------------------------------------------------------------------
    def _phase_move(self):
        """
        Phase 2. Both halves of a move happen at once, each decided by looking only at a neighbor:
        the empty cell that accepted a guest becomes that guest, and the guest whose requested cell
        accepted IT becomes an empty cell. A guest that was not accepted stays where it is.
        Returns the new `kind` field.
        """
        new_kind = self.kind.copy()
        for d, (dr, dc) in enumerate(DIRECTIONS):
            # an empty cell that accepted the guest in direction d becomes that guest
            neighbor_kind = shift(self.kind, dr, dc, WALL)
            arrives = (self.kind == EMPTY) & (self.accept == d)
            new_kind = np.where(arrives, neighbor_kind, new_kind)
            # a guest whose target (in direction d) accepted it leaves its cell
            target_accept = shift(self.accept, dr, dc, NO_DIRECTION)
            leaves = (self.kind >= 0) & (self.intent == d) & (target_accept == OPPOSITE[d])
            new_kind = np.where(leaves, EMPTY, new_kind)
        return new_kind

    # ----------------------------------------------------------------------------------
    # one generation
    # ----------------------------------------------------------------------------------
    def step(self):
        """
        Advance one generation. Every new field is computed from the OLD state only (synchronous).

        How the phases work in numpy: the rule of a single cell says "if my phase is 0 do X, if it is 1
        do Y, ...". With whole arrays we compute X, Y and Z for every cell and then let np.where pick,
        for each cell separately, the result that matches its phase. (All cells have the same phase,
        so in practice one branch is used each generation.)
        """
        in_intent = self.phase == PHASE_INTENT
        in_accept = self.phase == PHASE_ACCEPT
        in_move = self.phase == PHASE_MOVE

        new_dist = self._rule_a_distances()
        # intent: chosen in phase 0, kept during phase 1 (it is read in phases 1 and 2), cleared after the move
        new_intent = np.where(in_intent, self._phase_intent(),
                              np.where(in_accept, self.intent, NO_DIRECTION))
        # accept: chosen in phase 1, read in phase 2, cleared after the move
        new_accept = np.where(in_accept, self._phase_accept(), NO_DIRECTION)
        new_kind = np.where(in_move, self._phase_move(), self.kind)
        new_phase = (self.phase + 1) % MOVE_PERIOD

        self.kind, self.dist = new_kind, new_dist
        self.intent, self.accept, self.phase = new_intent, new_accept, new_phase
        self.generation += 1

    # ----------------------------------------------------------------------------------
    # read-only helpers (used by measurements and graphics, not by the rules)
    # ----------------------------------------------------------------------------------
    def guest_positions(self):
        """Return a list of (row, col) for guests 0..NUM_GUESTS-1."""
        positions = []
        for guest in range(NUM_GUESTS):
            cells = np.argwhere(self.kind == guest)
            positions.append(tuple(int(v) for v in cells[0]))
        return positions

    def state_key(self):
        """A hashable fingerprint of the full state (all fields) - used to detect cycles."""
        return (self.kind.tobytes(), self.dist.tobytes(), self.phase.tobytes(),
                self.intent.tobytes(), self.accept.tobytes())
