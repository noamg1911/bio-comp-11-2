# Maman 11 – Question 2: Party Planner as a Cellular Automaton — Spec

Course 20581 (Biological Computation). Based on the assignment PDF (`../מטלה 20581-01.pdf`)
and A. K. Dewdney, "Diverse personalities search for social equilibrium at a computer party",
Scientific American, Sept 1987 (`../Diverse personalities ... .pdf`).

## Goal
m = 5 guests (A–E) + a fixed table (T) on a 2D lattice. Input: an ideal-distance matrix
(5 rows × 6 columns: guests + table; may be asymmetric; values are in cells). Guests are placed randomly at
generation 0 and move by **local CA rules only** so that pairwise distances approach the matrix.
Run n = 2000 generations.

## Key idea
Guests cannot measure distance to far cells (radius-1 neighborhood). Instead, every cell stores
a vector of distance estimates `dist[0..5]` (to each guest and to the table). These values spread
through the lattice like ripples, one cell per generation. A guest reads `dist` in its 8 neighbor
cells and moves to the one with the lowest unhappiness.

## Decisions (must also appear in the report under "הנחות והחלטות" and in code comments)
| # | Decision |
|---|----------|
| D1 | Metric: **Chebyshev**, `max(|dx|,|dy|)`. Natural metric of the Moore neighborhood: equals both the number of generations for information to travel and the number of moves a guest needs. |
| D2 | Matrix value **0 = "as close as possible"**. Guests can't share a cell or stand on the table, so the closest possible distance is 1; every off-diagonal 0 is stored as 1 (`CLOSEST_POSSIBLE`) when the matrix is loaded. So 0 always means "on me" (as in Rule A), and the input format of the assignment's Table 1 is still accepted. |
| D3 | Matrix value **-1 = indifferent**: that term is skipped in the unhappiness sum (as Magi does in the paper). |
| D4 | **Two guests may not occupy the same cell.** Guests also can't enter wall or table cells. |
| D5 | Tie-break: deterministic. Stay unless a neighbor is strictly better; among equally good neighbors prefer straight (N,E,S,W) over diagonal, in a fixed order. |
| D6 | **No scaling: matrix values are distances in cells** (1 unit = 1 cell). Table 1 in the assignment is only an example; we design our own matrices with values suited to the grid size. On load, the code checks every value is -1 or within 0..GRID_SIZE-1 and raises a clear error otherwise. |
| D7 | Distance ripples pass through all non-wall cells (including table and guests); only walking is blocked. |

## Lattice
- Finite square `GRID_SIZE × GRID_SIZE` (default 40; assignment requires ≥ 30).
- Outside the lattice = wall (fixed boundary).
- Table: fixed rectangular block of cells near the center (position/size are constants).

## Cell state (vector)
| Field | Values | Meaning |
|-------|--------|---------|
| `type` | EMPTY, TABLE, GUEST_0..GUEST_4 | content of the cell |
| `dist[k]`, k=0..5 | 0..D_MAX (D_MAX = GRID_SIZE, also used as "unknown") | Chebyshev distance estimate to guest k (k=5: table) |
| `phase` | 0..MOVE_PERIOD-1 | global clock, identical in all cells, advances by 1 each generation |
| `intent` | NONE or one of 8 directions | guest's requested move (phase 0) |
| `accept` | NONE or one of 8 directions | empty cell's accepted incoming guest (phase 1) |

All fields are bounded integers → the state set is finite.

## Neighborhood
Moore, radius 1 (8 neighbors).

## Transition rules (synchronous: new grid computed only from the old grid)
**Rule A — distance propagation (every generation):**
- if guest k is on this cell: `dist[k] = 0`; table cells: `dist[5] = 0`
- else: `dist[k] = min(D_MAX, min over 8 neighbors of neighbor.dist[k] + 1)`

**Rule B — movement, 3-phase cycle driven by `phase`:**
- Phase 0 (intent): a guest cell (guest g) computes, for its own cell and each enterable
  neighbor (EMPTY), `U = Σ_{j: ideal[g][j] != -1, j != g} | dist[j](cell) − ideal[g][j] |`.
  If the best neighbor is strictly better than staying → `intent` = that direction (tie-break D5).
- Phase 1 (accept): an EMPTY cell looks at neighbors whose `intent` points at it and accepts exactly one
  (lowest guest index) → `accept` = its direction.
- Phase 2 (move): an EMPTY cell with `accept` becomes that guest; a guest cell whose intended target
  accepted it becomes EMPTY; `intent`/`accept` are cleared.

Guests move at most once per MOVE_PERIOD (=3) generations; information travels 1 cell/generation,
so the distance fields stay approximately up to date.

## Quality measure (report item 6) — computed by an external observer, not part of the CA
`Stress(t) = mean over ordered pairs (i, j), ideal[i][j] != -1, of | cheb(pos_i, pos_j) − ideal[i][j] |`
(includes guest→table, using the distance to the nearest table cell). Lower is better.
Optionally also a normalized version and a Euclidean version for comparison.

## Experiments / deliverables
1. Main matrix: our own 5×6 matrix with distances sized for the grid (e.g. values up to ~25 on a 40×40 grid); snapshots at generation 0 and every 100 generations up to 2000. (Table 1 from the assignment may be run as a small extra demo.)
2. Stress vs. generation for ~20 random seeds (mean + spread) → item 6(b): does it improve, does it depend on the start?
3. Item 7 interesting matrices (from the paper):
   - "Geographic party": true distances between 5 real cities → map is reconstructed (up to rotation/reflection) — link to NMDS/PCoA.
   - Chain of one-way attractions (A loves B, B avoids A, ...) → endless/periodic chase.
   - Optional: all distances large (wallflowers) vs. all small (knot at the table).

## Code layout (assignment rules: all constants named; GUI separate from rules; no CA libraries)
- `constants.py` — every number, with names and comments (incl. the default matrix)
- `automaton.py` — state arrays, Rule A, Rule B, synchronous `step()` (numpy; heavily commented for readers new to numpy)
- `metrics.py` — stress
- `visualize.py` — snapshots, stress plots (matplotlib)
- `main.py` — run Table 1; `experiments.py` — multi-seed and item-7 runs
- Code comments in English; report in Hebrew.

## Report (Hebrew) sections, per the assignment
1. Cell states and why the set is finite. 2. Neighborhood. 3. Transition rules (pseudocode / flowchart).
4. Constants table. 5. Snapshots. 6. Quality graph: (a) exact definition, (b) improvement & dependence on start.
7. Interesting matrix + explanation. Plus "הנחות והחלטות" (D1–D7).
