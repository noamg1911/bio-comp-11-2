"""
visualize.py - all graphics for Question 2 (kept separate from the automaton's rules, as required).

Nothing here changes the automaton; these functions only READ its state (or saved copies of it).
"""

import math

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

from constants import (
    GRID_SIZE, NUM_GUESTS, GUEST_NAMES, TABLE_NAME, TABLE_INDEX, EMPTY, TABLE, D_MAX,
    GUEST_COLORS, TABLE_COLOR, FLOOR_COLOR, GRID_LINE_COLOR,
    SNAPSHOT_COLUMNS, SNAPSHOT_PANEL_SIZE, FIGURE_DPI,
    LIVE_INTERVAL_MS, LIVE_GENERATIONS_PER_FRAME, CITY_COORDS,
)

# colors for the "kind" values: index 0 = floor, 1 = table, 2.. = guests
_ROOM_CMAP = ListedColormap([FLOOR_COLOR, TABLE_COLOR] + GUEST_COLORS)
_FLOOR_CODE, _TABLE_CODE, _FIRST_GUEST_CODE = 0, 1, 2
# purely cosmetic plotting sizes (inches / points / transparency)
_LABEL_FONT_SIZE = 8
_TITLE_FONT_SIZE = 9
_FIELD_LABEL_FONT_SIZE = 9
_LEGEND_FONT_SIZE = 8
_LABEL_OFFSET_POINTS = (3, 3)
_CITY_LABEL_OFFSET_POINTS = (6, 4)
_CITY_MARKER_SIZE = 10
_GRID_LINE_WIDTH = 0.3
_PLOT_GRID_ALPHA = 0.3
_STRESS_FIGSIZE = (8, 4)
_MULTI_SEED_FIGSIZE = (13, 4.5)
_MULTI_SEED_WIDTH_RATIOS = [2, 1]
_SEED_CURVE_ALPHA = 0.35
_SEED_CURVE_WIDTH = 0.7
_MEAN_CURVE_WIDTH = 2
_THIN_LINE_WIDTH = 1
_FIELD_FIGSIZE = (6, 5.2)
_TRAJECTORY_FIGSIZE = (6, 6)
_TRAJECTORY_ALPHA = 0.8
_CITIES_FIGSIZE = (11, 5.5)
_LIVE_FIGSIZE = (6, 6)
_HALF_CELL = 0.5          # cell edges are half a cell away from cell centers


def _kind_to_codes(kind):
    """Map kind values (EMPTY, TABLE, guest index) to color codes of _ROOM_CMAP."""
    codes = np.full(kind.shape, _FLOOR_CODE)
    codes[kind == TABLE] = _TABLE_CODE
    for guest in range(NUM_GUESTS):
        codes[kind == guest] = _FIRST_GUEST_CODE + guest
    return codes


def draw_room(ax, kind, title="", names=GUEST_NAMES):
    """Draw one configuration of the room on a matplotlib axis. `names` = the label drawn next to each guest."""
    ax.imshow(_kind_to_codes(kind), cmap=_ROOM_CMAP, vmin=0, vmax=_FIRST_GUEST_CODE + NUM_GUESTS - 1,
              interpolation="nearest")
    # light grid lines between cells
    ax.set_xticks(np.arange(-_HALF_CELL, GRID_SIZE, 1), minor=True)
    ax.set_yticks(np.arange(-_HALF_CELL, GRID_SIZE, 1), minor=True)
    ax.grid(which="minor", color=GRID_LINE_COLOR, linewidth=_GRID_LINE_WIDTH)
    ax.tick_params(which="both", bottom=False, left=False, labelbottom=False, labelleft=False)
    # guest letters next to the guests
    for guest in range(NUM_GUESTS):
        r, c = np.argwhere(kind == guest)[0]
        ax.annotate(names[guest], (c, r), xytext=_LABEL_OFFSET_POINTS, textcoords="offset points",
                    fontsize=_LABEL_FONT_SIZE, fontweight="bold", color=GUEST_COLORS[guest])
    ax.set_title(title, fontsize=_TITLE_FONT_SIZE)


def save_snapshots(snapshots, stresses, path, names=GUEST_NAMES, suptitle=""):
    """Save a grid of snapshots: snapshots = {generation: kind array}."""
    generations = sorted(snapshots)
    rows = math.ceil(len(generations) / SNAPSHOT_COLUMNS)
    fig, axes = plt.subplots(rows, SNAPSHOT_COLUMNS,
                             figsize=(SNAPSHOT_COLUMNS * SNAPSHOT_PANEL_SIZE, rows * SNAPSHOT_PANEL_SIZE))
    axes = np.atleast_1d(axes).ravel()
    for ax, gen in zip(axes, generations):
        draw_room(ax, snapshots[gen], f"gen {gen}  (stress {stresses[gen]:.2f})", names)
    for ax in axes[len(generations):]:
        ax.axis("off")
    if suptitle:
        fig.suptitle(suptitle)
    fig.tight_layout()
    fig.savefig(path, dpi=FIGURE_DPI)
    plt.close(fig)


def plot_stress(stresses, path, title="Configuration quality over time"):
    """Stress (mean |actual - ideal| in cells) as a function of the generation."""
    fig, ax = plt.subplots(figsize=_STRESS_FIGSIZE)
    ax.plot(range(len(stresses)), stresses, linewidth=_THIN_LINE_WIDTH)
    ax.set_xlabel("generation")
    ax.set_ylabel("stress  (mean |actual - ideal|, cells)")
    ax.set_title(title)
    ax.set_ylim(bottom=0)
    ax.grid(alpha=_PLOT_GRID_ALPHA)
    fig.tight_layout()
    fig.savefig(path, dpi=FIGURE_DPI)
    plt.close(fig)


def plot_multi_seed(stress_runs, path, title="Stress for different random initial placements"):
    """
    stress_runs: 2D array, row s = the stress curve of random seed s.
    Left: all curves (thin) + their mean (thick). Right: initial vs. final stress of each seed.
    """
    stress_runs = np.asarray(stress_runs)
    gens = np.arange(stress_runs.shape[1])
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=_MULTI_SEED_FIGSIZE, gridspec_kw={"width_ratios": _MULTI_SEED_WIDTH_RATIOS})
    for run in stress_runs:
        ax1.plot(gens, run, color="gray", alpha=_SEED_CURVE_ALPHA, linewidth=_SEED_CURVE_WIDTH)
    ax1.plot(gens, stress_runs.mean(axis=0), color="black", linewidth=_MEAN_CURVE_WIDTH, label="mean over seeds")
    ax1.set_xlabel("generation")
    ax1.set_ylabel("stress (cells)")
    ax1.set_ylim(bottom=0)
    ax1.set_title(title)
    ax1.legend()
    ax1.grid(alpha=_PLOT_GRID_ALPHA)

    ax2.scatter(stress_runs[:, 0], stress_runs[:, -1])
    ax2.set_xlabel("stress at generation 0")
    ax2.set_ylabel(f"stress at generation {gens[-1]}")
    ax2.set_title("initial vs. final (one dot per seed)")
    ax2.grid(alpha=_PLOT_GRID_ALPHA)
    fig.tight_layout()
    fig.savefig(path, dpi=FIGURE_DPI)
    plt.close(fig)


def plot_guest_unhappiness(unhappiness, path, names=GUEST_NAMES, title="Unhappiness of each guest"):
    """unhappiness[t] = list of per-guest unhappiness at generation t; also draws their total."""
    unhappiness = np.asarray(unhappiness)
    gens = np.arange(len(unhappiness))
    fig, ax = plt.subplots(figsize=_STRESS_FIGSIZE)
    for guest in range(NUM_GUESTS):
        ax.plot(gens, unhappiness[:, guest], color=GUEST_COLORS[guest], linewidth=_THIN_LINE_WIDTH,
                label=names[guest])
    ax.plot(gens, unhappiness.sum(axis=1), color="black", linewidth=_MEAN_CURVE_WIDTH, label="total")
    ax.set_xlabel("generation")
    ax.set_ylabel("unhappiness (cells)")
    ax.set_title(title)
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=_LEGEND_FONT_SIZE, loc="upper right")
    ax.grid(alpha=_PLOT_GRID_ALPHA)
    fig.tight_layout()
    fig.savefig(path, dpi=FIGURE_DPI)
    plt.close(fig)


def plot_distance_field(automaton, target, path, names=GUEST_NAMES):
    """Heat map of dist[target] over the whole room (shows the 'ripples' of Rule A)."""
    field = automaton.dist[target]
    fig, ax = plt.subplots(figsize=_FIELD_FIGSIZE)
    im = ax.imshow(np.where(field >= D_MAX, np.nan, field), cmap="viridis", interpolation="nearest")
    fig.colorbar(im, ax=ax, label="dist value (cells)")
    for guest in range(NUM_GUESTS):
        r, c = np.argwhere(automaton.kind == guest)[0]
        ax.text(c, r, names[guest], ha="center", va="center", fontsize=_FIELD_LABEL_FONT_SIZE, fontweight="bold", color="white")
    target_name = TABLE_NAME if target == TABLE_INDEX else names[target]
    ax.set_title(f"dist[{target}] = distance to {target_name}, generation {automaton.generation}")
    ax.tick_params(bottom=False, left=False, labelbottom=False, labelleft=False)
    fig.tight_layout()
    fig.savefig(path, dpi=FIGURE_DPI)
    plt.close(fig)


def plot_trajectories(positions, path, first_gen, last_gen, names=GUEST_NAMES, kind=None, title=""):
    """Draw each guest's path between two generations (positions[t] = list of (row, col))."""
    fig, ax = plt.subplots(figsize=_TRAJECTORY_FIGSIZE)
    if kind is not None:
        background = np.where(kind == TABLE, TABLE, EMPTY)   # table only, no guests
        ax.imshow(_kind_to_codes(background), cmap=_ROOM_CMAP,
                  vmin=0, vmax=_FIRST_GUEST_CODE + NUM_GUESTS - 1, interpolation="nearest")
    for guest in range(NUM_GUESTS):
        path_rc = np.array([positions[t][guest] for t in range(first_gen, last_gen + 1)])
        ax.plot(path_rc[:, 1], path_rc[:, 0], color=GUEST_COLORS[guest], linewidth=_THIN_LINE_WIDTH, alpha=_TRAJECTORY_ALPHA,
                label=names[guest])
        ax.plot(path_rc[-1, 1], path_rc[-1, 0], "o", color=GUEST_COLORS[guest])
    ax.set_xlim(-_HALF_CELL, GRID_SIZE - _HALF_CELL)
    ax.set_ylim(GRID_SIZE - _HALF_CELL, -_HALF_CELL)
    ax.set_aspect("equal")
    ax.legend(fontsize=_LEGEND_FONT_SIZE, loc="upper right")
    ax.set_title(title or f"paths, generations {first_gen}-{last_gen} (dot = end)")
    fig.tight_layout()
    fig.savefig(path, dpi=FIGURE_DPI)
    plt.close(fig)


def plot_cities(kind, generation, path, city_names, city_labels):
    """The final party next to the real map (longitude = x, latitude = y)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=_CITIES_FIGSIZE)
    draw_room(ax1, kind, f"the party at generation {generation}", city_labels)
    lats = [lat for lat, lon in CITY_COORDS]
    lons = [lon for lat, lon in CITY_COORDS]
    for guest in range(NUM_GUESTS):
        ax2.plot(lons[guest], lats[guest], "o", color=GUEST_COLORS[guest], markersize=_CITY_MARKER_SIZE)
        ax2.annotate(city_names[guest], (lons[guest], lats[guest]), xytext=_CITY_LABEL_OFFSET_POINTS, textcoords="offset points")
    ax2.set_aspect(1 / math.cos(math.radians(np.mean(lats))))   # degrees of longitude are shorter
    ax2.set_title("the real map")
    ax2.set_xlabel("longitude")
    ax2.set_ylabel("latitude")
    ax2.grid(alpha=_PLOT_GRID_ALPHA)
    fig.tight_layout()
    fig.savefig(path, dpi=FIGURE_DPI)
    plt.close(fig)


def live_animation(automaton, num_generations, names=GUEST_NAMES):
    """
    A simple graphical interface: shows the room changing from generation to generation.
    Requires an interactive matplotlib backend (just run `python main.py --live`).
    """
    from matplotlib.animation import FuncAnimation
    from metrics import stress

    fig, ax = plt.subplots(figsize=_LIVE_FIGSIZE)

    def update(_frame):
        if automaton.generation < num_generations:
            for _ in range(LIVE_GENERATIONS_PER_FRAME):
                automaton.step()
        ax.clear()
        draw_room(ax, automaton.kind, f"generation {automaton.generation}   stress {stress(automaton):.2f}", names)

    frames = num_generations // LIVE_GENERATIONS_PER_FRAME
    animation = FuncAnimation(fig, update, frames=frames, interval=LIVE_INTERVAL_MS, repeat=False)
    plt.show()
    return animation


def use_file_backend():
    """Use a non-interactive backend (only saving figures to files - no windows)."""
    matplotlib.use("Agg")
