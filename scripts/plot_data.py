import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ----------------------------
# Config
# ----------------------------
L1_PATH = "../data/xlsx/Test-L1-raw.xlsx"
L2_PATH = "../data/xlsx/Test-L2-raw.xlsx"
L3_PATH = "../data/xlsx/Test-L3-raw.xlsx"

# Switching window parameters (seconds)
PRE_S = 2.0
POST_S = 5.0
MERGE_GAP_S = 0.5  # merge windows closer than this

# Publication figure settings
BIN_S = 1.0
SMOOTH_BINS = 5
SWITCH_ALPHA = 0.2

# ----------------------------
# Helpers
# ----------------------------
def merge_intervals(intervals, merge_gap=0.0):
    """Merge [start, end] intervals with optional merge gap."""
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda x: x[0])
    merged = [list(intervals[0])]
    for s, e in intervals[1:]:
        if s <= merged[-1][1] + merge_gap:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return [tuple(x) for x in merged]

def intervals_to_mask(t, intervals):
    """Return boolean mask for t within any interval."""
    if not intervals:
        return np.zeros(len(t), dtype=bool)
    mask = np.zeros(len(t), dtype=bool)
    for s, e in intervals:
        mask |= (t >= s) & (t <= e)
    return mask

def compute_rate(t, mask=None, bin_s=0.5):
    """Compute packet counts per bin; optionally apply mask first."""
    if mask is not None:
        t = t[mask]
    if len(t) == 0:
        return np.array([]), np.array([])
    t0, t1 = float(np.min(t)), float(np.max(t))
    edges = np.arange(t0, t1 + bin_s, bin_s)
    counts, _ = np.histogram(t, bins=edges)
    centers = edges[:-1] + bin_s / 2
    rate = counts / bin_s
    return centers, rate

def centered_moving_average(y, window):
    """Light smoothing to reduce bin-boundary zig-zag."""
    if window <= 1 or len(y) == 0:
        return y
    return (
        pd.Series(y)
        .rolling(window=window, center=True, min_periods=1)
        .mean()
        .to_numpy()
    )

def infer_switching_windows(df, pre_s=2.0, post_s=5.0, merge_gap_s=0.5):
    """
    Infer switching windows based on benign CTRL/PROT stNum increments.
    Uses label==False and gocbRef containing CTRL or PROT.
    """
    benign = df[df["label"] == False].copy()

    # Only CTRL/PROT streams
    sel = benign["gocbRef"].astype(str).str.contains("CTRL|PROT", regex=True)
    benign = benign[sel].copy()

    # Ensure sorted per stream
    benign.sort_values(["gocbRef", "EpochArrivalTime"], inplace=True)

    windows = []
    for _, gdf in benign.groupby("gocbRef", sort=False):
        st = gdf["stNum"].to_numpy()
        tt = gdf["t_rel"].to_numpy()

        # detect stNum increments
        inc_idx = np.where(np.diff(st) > 0)[0] + 1
        for idx in inc_idx:
            t_event = tt[idx]
            windows.append((t_event - pre_s, t_event + post_s))

    windows = merge_intervals(windows, merge_gap=merge_gap_s)
    return windows

# ----------------------------
# Load + preprocess
# ----------------------------
df = pd.read_excel(L1_PATH)

required_cols = ["gocbRef", "EpochArrivalTime", "stNum", "label"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    raise ValueError(f"Missing columns: {missing}. Found: {list(df.columns)}")

df = df.copy()
df["EpochArrivalTime"] = pd.to_numeric(df["EpochArrivalTime"], errors="coerce")
df = df.dropna(subset=["EpochArrivalTime"]).copy()

t0 = df["EpochArrivalTime"].min()
df["t_rel"] = df["EpochArrivalTime"] - t0

# Infer switching windows and mark packets inside them
switch_windows = infer_switching_windows(df, PRE_S, POST_S, MERGE_GAP_S)
df["in_switch_window"] = intervals_to_mask(df["t_rel"].to_numpy(), switch_windows)

is_attack = df["label"].astype(bool).to_numpy()
is_benign = ~is_attack

t = df["t_rel"].to_numpy()
x_b, r_b = compute_rate(t, mask=is_benign, bin_s=BIN_S)

n_benign_streams = df.loc[~df["label"], "gocbRef"].nunique()
print(f"Number of benign streams: {n_benign_streams}")

r_b_avg = r_b / n_benign_streams
r_b_avg_smooth = centered_moving_average(r_b_avg, SMOOTH_BINS)

r_b_total = r_b
r_b_total_smooth = centered_moving_average(r_b_total, SMOOTH_BINS)

fig, ax = plt.subplots(figsize=(3.5, 2.0), dpi=300)

for (s, e) in switch_windows:
    ax.axvspan(s, e, color="tab:blue", alpha=SWITCH_ALPHA, linewidth=0)

if len(x_b):
    ax.plot(
        x_b,
        r_b_total_smooth,
        linewidth=1.2
    )

ax.set_xlabel("Time since first packet (s)")
ax.set_ylabel("Total benign packet rate (pps)")
ax.set_xlim(df["t_rel"].min(), df["t_rel"].max())
ax.set_ylim(0, None)

fig.tight_layout()
plt.show()

# ----------------------------
# Config
# ----------------------------
FILES = [    
    (L1_PATH, "Level 1 (Naive)"),
    (L2_PATH, "Level 2 (Stealth)"),
    (L3_PATH, "Level 3 (State-aware)"),]

BIN_S = 2.0          # slightly coarser -> less visual noise
SMOOTH_BINS = 3      # light smoothing only
SWITCH_ALPHA = 0.12

# Keep only the strongest attack spikes to reduce clutter.
# Set to None to keep everything.
ATTACK_CAP_PPS = 35

XMIN = 400
XMAX = 1050

# ----------------------------
# Helpers
# ----------------------------
def merge_intervals(intervals, merge_gap=0.0):
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda x: x[0])
    merged = [list(intervals[0])]
    for s, e in intervals[1:]:
        if s <= merged[-1][1] + merge_gap:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return [tuple(x) for x in merged]

def intervals_to_mask(t, intervals):
    if not intervals:
        return np.zeros(len(t), dtype=bool)
    mask = np.zeros(len(t), dtype=bool)
    for s, e in intervals:
        mask |= (t >= s) & (t <= e)
    return mask

def compute_rate(t, mask=None, bin_s=1.0, tmin=None, tmax=None):
    if mask is not None:
        t = t[mask]
    if len(t) == 0:
        return np.array([]), np.array([])
    if tmin is None:
        tmin = float(np.min(t))
    if tmax is None:
        tmax = float(np.max(t))
    edges = np.arange(tmin, tmax + bin_s, bin_s)
    counts, _ = np.histogram(t, bins=edges)
    centers = edges[:-1] + bin_s / 2
    rate = counts / bin_s
    return centers, rate

def centered_moving_average(y, window):
    if window <= 1 or len(y) == 0:
        return y
    return (
        pd.Series(y)
        .rolling(window=window, center=True, min_periods=1)
        .mean()
        .to_numpy()
    )

def infer_switching_windows(df, pre_s=2.0, post_s=5.0, merge_gap_s=0.5):
    benign = df[df["label"] == False].copy()
    sel = benign["gocbRef"].astype(str).str.contains("CTRL|PROT", regex=True)
    benign = benign[sel].copy()
    benign.sort_values(["gocbRef", "EpochArrivalTime"], inplace=True)

    windows = []
    for _, gdf in benign.groupby("gocbRef", sort=False):
        st = gdf["stNum"].to_numpy()
        tt = gdf["t_rel"].to_numpy()
        inc_idx = np.where(np.diff(st) > 0)[0] + 1
        for idx in inc_idx:
            t_event = tt[idx]
            windows.append((t_event - pre_s, t_event + post_s))

    return merge_intervals(windows, merge_gap=merge_gap_s)

def load_case(xlsx_path):
    df = pd.read_excel(xlsx_path)

    required_cols = ["gocbRef", "EpochArrivalTime", "stNum", "label"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"{xlsx_path}: missing columns {missing}")

    df = df.copy()
    df["EpochArrivalTime"] = pd.to_numeric(df["EpochArrivalTime"], errors="coerce")
    df = df.dropna(subset=["EpochArrivalTime"]).copy()

    t0 = df["EpochArrivalTime"].min()
    df["t_rel"] = df["EpochArrivalTime"] - t0

    switch_windows = infer_switching_windows(df, PRE_S, POST_S, MERGE_GAP_S)

    t = df["t_rel"].to_numpy()
    is_attack = df["label"].astype(bool).to_numpy()
    is_benign = ~is_attack

    tmin = float(np.min(t))
    tmax = float(np.max(t))

    # Benign: total packet rate
    x_b, r_b = compute_rate(t, mask=is_benign, bin_s=BIN_S, tmin=tmin, tmax=tmax)
    r_b_total = centered_moving_average(r_b, SMOOTH_BINS)

    # Attack: total injected rate
    x_a, r_a = compute_rate(t, mask=is_attack, bin_s=BIN_S, tmin=tmin, tmax=tmax)
    r_a = centered_moving_average(r_a, SMOOTH_BINS)

    if ATTACK_CAP_PPS is not None:
        r_a = np.minimum(r_a, ATTACK_CAP_PPS)

    return {
        "df": df,
        "switch_windows": switch_windows,
        "x_b": x_b,
        "r_b_total": r_b_total,
        "x_a": x_a,
        "r_a": r_a,
        "tmin": tmin,
        "tmax": tmax,
    }

cases = [(label, load_case(path)) for path, label in FILES]

# Shared y-limit across rows
ymax = 0.0
for _, c in cases:
    if len(c["r_b_total"]):
        ymax = max(ymax, float(np.max(c["r_b_total"])))
    if len(c["r_a"]):
        ymax = max(ymax, float(np.max(c["r_a"])))
ymax *= 1.08

# Shared x-limits
global_tmin = min(c["tmin"] for _, c in cases)
global_tmax = max(c["tmax"] for _, c in cases)
if XMIN is not None:
    global_tmin = XMIN
if XMAX is not None:
    global_tmax = XMAX

# ----------------------------
# Plot: attacker and benign
# ----------------------------
fig, axes = plt.subplots(
    nrows=1,
    ncols=3,
    figsize=(5.2, 1.7),
    sharex=True,
    sharey=True,
    constrained_layout=True,
    dpi=300
)

short_labels = ["(a) Level 1", "(b) Level 2", "(c) Level 3"]

for ax, short_label, (label, c) in zip(axes, short_labels, cases):
    for (s, e) in c["switch_windows"]:
        ax.axvspan(s, e, color="tab:blue", alpha=SWITCH_ALPHA, linewidth=0)

    # Interpolate attack onto benign time grid if needed
    r_total = c["r_b_total"].copy()
    if len(c["r_a"]) and len(c["x_a"]) == len(c["x_b"]):
        r_total = c["r_b_total"] + c["r_a"]
    else:
        # safer: interpolate
        r_a_interp = np.interp(c["x_b"], c["x_a"], c["r_a"], left=0, right=0)
        r_total = c["r_b_total"] + r_a_interp

    ax.plot(c["x_b"], r_total, linewidth=0.9, label="Benign + attack", color='orange')
    ax.plot(c["x_b"], c["r_b_total"], linewidth=0.9, alpha=0.9, label="Benign")

    ax.set_xlim(global_tmin, global_tmax)
    ax.set_ylim(0, ymax)

    ax.text(
        0.02, 0.95, short_label,
        transform=ax.transAxes,
        fontsize=4,
        va="top",
        ha="left",
        bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="0.8", alpha=0.9)
    )

axes[0].set_ylabel("Total packet rate (pps)", fontsize=6)
for ax in axes:
    ax.set_xlabel("Time (s)", fontsize=6)
    ax.tick_params(axis='both', labelsize=4)

axes[2].legend(loc="upper right", fontsize=4, frameon=True)

plt.show()