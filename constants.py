"""
constants.py - every constant used in Question 2 (Party Planner cellular automaton).

The assignment requires that no "magic numbers" appear in the code, so every number
used by the automaton, the measurements and the experiments is defined here with a name.

All distances in this project are measured in CELLS, using the Chebyshev metric:
    distance((r1, c1), (r2, c2)) = max(|r1 - r2|, |c1 - c2|)
(the number of king-moves between two cells - see SPEC.md, decision D1).
"""

# =====================================================================  lattice
GRID_SIZE = 40              # the lattice is GRID_SIZE x GRID_SIZE cells (assignment: at least 30x30)

# The food table: a fixed rectangle of cells (its position is not randomized - assignment item 6).
TABLE_TOP = 18              # first row of the table
TABLE_LEFT = 17             # first column of the table
TABLE_HEIGHT = 4            # number of rows the table occupies
TABLE_WIDTH = 6             # number of columns the table occupies

# =====================================================================  guests
NUM_GUESTS = 5              # m = 5 guests (A..E)
GUEST_NAMES = ["A", "B", "C", "D", "E"]
TABLE_NAME = "T"
TABLE_INDEX = NUM_GUESTS    # in every distance vector, index 0..4 are the guests and index 5 is the table
NUM_TARGETS = NUM_GUESTS + 1  # number of entries in a cell's distance vector (5 guests + table)

# =====================================================================  cell contents ("kind" field)
# A guest cell stores the guest's index (0..NUM_GUESTS-1). The other contents are negative codes:
EMPTY = -1                  # an empty floor cell
TABLE = -2                  # a table cell (guests cannot step on it)
WALL = -3                   # used only for "cells" outside the lattice (the walls of the room)

# =====================================================================  distance field ("dist" field)
SOURCE_DISTANCE = 0         # the value a cell has in dist[k] when target k is standing on it
STEP_COST = 1               # one king-move = distance 1 (Chebyshev)
D_MAX = GRID_SIZE           # "unknown / very far". Real Chebyshev distances are at most GRID_SIZE-1,
                            # so D_MAX can never be confused with a real distance. Values are capped
                            # at D_MAX, which keeps the set of cell states finite.

# =====================================================================  ideal-distance matrix values
INDIFFERENT = -1            # ideal[i][j] == -1: guest i does not care where j is (decision D3)
MIN_IDEAL = 0               # smallest allowed value in the input matrix (0 = "as close as possible", decision D2)
MAX_IDEAL = GRID_SIZE - 1   # largest allowed ideal distance (the largest distance that fits in the lattice)
CLOSEST_POSSIBLE = 1        # two guests can't share a cell and nobody stands on the table, so the closest
                            # possible distance is 1. An input 0 ("as close as possible") is turned into 1
                            # when the matrix is loaded (decision D2). 0 then always means "on me" (Rule A).

# =====================================================================  movement (3-phase cycle)
PHASE_INTENT = 0            # phase 0: every guest chooses a direction it wants to move to
PHASE_ACCEPT = 1            # phase 1: every empty cell accepts at most one guest that wants to enter it
PHASE_MOVE = 2              # phase 2: the accepted moves happen
MOVE_PERIOD = 3             # number of phases = number of generations per possible move
INITIAL_PHASE = PHASE_INTENT

# The 8 Moore neighbors as (row offset, column offset). Row 0 is the TOP row.
# The ORDER is the tie-break (decision D5): straight moves first, then diagonal moves.
DIRECTIONS = [
    (-1, 0),    # 0: up
    (0, 1),     # 1: right
    (1, 0),     # 2: down
    (0, -1),    # 3: left
    (-1, 1),    # 4: up-right
    (1, 1),     # 5: down-right
    (1, -1),    # 6: down-left
    (-1, -1),   # 7: up-left
]
NUM_DIRECTIONS = len(DIRECTIONS)
NO_DIRECTION = -1           # value of the intent/accept fields when there is no request
# OPPOSITE[d] = index of the direction that points back (up <-> down, up-right <-> down-left, ...)
OPPOSITE = [DIRECTIONS.index((-dr, -dc)) for (dr, dc) in DIRECTIONS]

# =====================================================================  simulation / output
NUM_GENERATIONS = 2000      # n = 2000 generations (assignment item 5)
SNAPSHOT_EVERY = 100        # save / print the guests' positions every 100 generations
DEFAULT_SEED = 1            # random seed of the initial placement (for reproducible runs)
NUM_SEEDS = 20              # number of different random initial placements in the multi-seed experiment
OUTPUT_DIR = "output"       # folder for all figures and printouts

# =====================================================================  ideal-distance matrices
# Every matrix has NUM_GUESTS rows (the guest who "feels") and NUM_TARGETS columns
# (guests A..E and then the table T). ideal[i][j] = the distance (in cells) guest i wants from j.
# The matrices do not have to be symmetric. The diagonal (a guest and itself) is ignored.

# --- The main matrix of the assignment run (our own, sized for a 40x40 room).
#     A is the host: stays near the table and moderately close to everyone.
#     B and C are friends; D and E are a couple that keeps away from B and C.
#     Small asymmetries (e.g. A wants 10 from C, C wants 12 from A) make the party "alive".
MAIN_MATRIX = [
    #  A   B   C   D   E   T
    [  0,  6, 10, 12,  8,  2],   # A
    [  6,  0,  4, 15, 10,  8],   # B
    [ 12,  3,  0, 18, 14, 10],   # C
    [ 15, 20, 16,  0,  4, 12],   # D
    [  9, 12, 14,  5,  0,  6],   # E
]

# --- Table 1 from the assignment (an example only; values are small for a 40x40 room).
ASSIGNMENT_TABLE_1 = [
    #  A  B  C  D  E  T
    [  0, 5, 8, 7, 7, 0],   # A
    [  0, 0, 1, 0, 3, 8],   # B
    [  6, 1, 0, 1, 0, 6],   # C
    [  5, 7, 0, 0, 4, 5],   # D
    [  4, 4, 0, 2, 0, 6],   # E
]

# --- Item 7a: "geographic party" (Dewdney's cities idea).
#     The guests are 5 Israeli cities: A=Haifa, B=Tel Aviv, C=Jerusalem, D=Be'er Sheva, E=Tiberias.
#     Each value is the real straight-line distance between the two cities divided by 6 km and
#     rounded (so 1 cell ~ 6 km). The cities don't care about the table (-1).
#     If the automaton works, the guests should draw the map of Israel (possibly rotated/mirrored).
CITY_NAMES = ["Haifa", "Tel Aviv", "Jerusalem", "Be'er Sheva", "Tiberias"]
CITY_LABELS = ["Hai", "TA", "Jer", "BS", "Tib"]   # short labels drawn next to the guests
# (latitude, longitude) of each city - used only to draw the real map next to the result
CITY_COORDS = [(32.794, 34.990), (32.085, 34.782), (31.769, 35.216), (31.252, 34.791), (32.795, 35.531)]
CITIES_MATRIX = [
    #  A   B   C   D   E   T
    [  0, 14, 19, 29,  8, -1],   # A = Haifa        (81, 116, 172, 51 km)
    [ 14,  0,  9, 15, 18, -1],   # B = Tel Aviv     (81, 54, 92, 106 km)
    [ 19,  9,  0, 12, 20, -1],   # C = Jerusalem    (116, 54, 70, 118 km)
    [ 29, 15, 12,  0, 31, -1],   # D = Be'er Sheva  (172, 92, 70, 185 km)
    [  8, 18, 20, 31,  0, -1],   # E = Tiberias     (51, 106, 118, 185 km)
]

# --- Item 7b: a closed chain of one-way attractions (Dewdney: "A loves B but B hates A ...").
#     Each guest wants to be right next to the next guest in the chain (A->B->C->D->E->A)
#     and as far as possible from the previous one. Everything else is indifferent.
NEAR = 0                    # "as close as possible" - becomes CLOSEST_POSSIBLE (1) when loaded
FAR = MAX_IDEAL
CHASE_MATRIX = [
    #  A            B            C            D            E            T
    [  0,           NEAR,        INDIFFERENT, INDIFFERENT, FAR,         INDIFFERENT],  # A loves B, flees E
    [  FAR,         0,           NEAR,        INDIFFERENT, INDIFFERENT, INDIFFERENT],  # B loves C, flees A
    [  INDIFFERENT, FAR,         0,           NEAR,        INDIFFERENT, INDIFFERENT],  # C loves D, flees B
    [  INDIFFERENT, INDIFFERENT, FAR,         0,           NEAR,        INDIFFERENT],  # D loves E, flees C
    [  NEAR,        INDIFFERENT, INDIFFERENT, FAR,         0,           INDIFFERENT],  # E loves A, flees D
]

# --- Item 7c (extra): everybody wants to be far from everybody ("wallflowers").
WALLFLOWER_MATRIX = [[FAR] * NUM_GUESTS + [INDIFFERENT] for _ in range(NUM_GUESTS)]

# --- Item 7d (extra): everybody wants to be right next to everybody and to the table ("tight knot").
KNOT_MATRIX = [[NEAR] * NUM_TARGETS for _ in range(NUM_GUESTS)]

# --- All the matrices by name: name -> (matrix, label drawn next to each guest).
#     Used by main.py (--matrix NAME) and experiments.py.
MATRICES = {
    "main": (MAIN_MATRIX, GUEST_NAMES),
    "table1": (ASSIGNMENT_TABLE_1, GUEST_NAMES),
    "cities": (CITIES_MATRIX, CITY_LABELS),
    "chase": (CHASE_MATRIX, GUEST_NAMES),
    "wallflowers": (WALLFLOWER_MATRIX, GUEST_NAMES),
    "knot": (KNOT_MATRIX, GUEST_NAMES),
}

# =====================================================================  plotting
GUEST_COLORS = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e"]  # one color per guest
TABLE_COLOR = "#8c8c8c"
FLOOR_COLOR = "#ffffff"
GRID_LINE_COLOR = "#e6e6e6"
SNAPSHOT_COLUMNS = 7        # snapshot figure layout: 21 snapshots (gen 0, 100, ..., 2000) in 3 rows of 7
SNAPSHOT_PANEL_SIZE = 2.6   # inches per snapshot panel
FIGURE_DPI = 130            # resolution of saved figures
LIVE_INTERVAL_MS = 30       # delay between frames in the live (GUI) animation
LIVE_GENERATIONS_PER_FRAME = MOVE_PERIOD  # draw once per move cycle
