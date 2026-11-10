"""
The four plots, drawn as one 2x2 figure:

  top left      final posterior for p, with the near-fair zone and credible interval
  top right     posterior evolution: the density after a few checkpoints
  bottom left   posterior mean and credible interval after every flip
  bottom right  P(p is near-fair) after every flip, with the stopping thresholds
"""
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import beta

from .model import summary, trajectory

BLUE, ORANGE, GRAY = "#2a6fdb", "#e8710a", "#8a8f98"
GREEN, RED = "#1a9850", "#d73027"
CHECKPOINTS = (10, 25, 50, 100, 200, 400, 800, 1600, 3200)  # flip counts worth showing


def checkpoint_indices(n, max_curves=6):
    """Which states to draw in the evolution panel (indices into the trajectory arrays)."""
    n0, nf = int(n[0]), int(n[-1])
    wanted = sorted({n0, nf} | {c for c in CHECKPOINTS if n0 < c < nf})
    if len(wanted) > max_curves:  # keep first, last and evenly spaced ones between
        keep = np.linspace(0, len(wanted) - 1, max_curves).round().astype(int)
        wanted = [wanted[k] for k in keep]
    return [w - n0 for w in wanted]  # each flip adds exactly one to n


def make_figure(history, init, cfg):
    traj = trajectory(history, init, cfg)
    n, s, m = traj["n"], traj["s"], traj["m"]
    fin = summary(int(s[-1]), int(m[-1]), cfg)
    zlo, zhi = cfg.zone
    x = np.linspace(0, 1, 1000)

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    names = {"fair": "near-fair", "biased": "biased", None: "undecided"}
    fig.suptitle(f"Cookie coin: {n[-1]} flips ({s[-1]} single, {m[-1]} multiple), "
                 f"verdict: {names[fin['verdict']]}", fontsize=14)

    # 1. final posterior ------------------------------------------------------
    y = beta(cfg.prior + s[-1], cfg.prior + m[-1]).pdf(x)
    ymax = y.max()
    ax1.plot(x, beta(cfg.prior, cfg.prior).pdf(x), "--", color=GRAY, label="prior")
    ax1.plot(x, y, color=BLUE, lw=2, label="posterior")
    ax1.fill_between(x, y, where=(x >= zlo) & (x <= zhi), color=BLUE, alpha=0.3,
                     label=f"near-fair zone {zlo:.2f}–{zhi:.2f}: {fin['p_near']:.0%} of posterior")
    ax1.hlines(-0.04 * ymax, fin["lo"], fin["hi"], color=ORANGE, lw=5,
               label=f"{cfg.cred:.0%} credible interval [{fin['lo']:.3f}, {fin['hi']:.3f}]")
    ax1.axvline(0.5, color="k", lw=0.8, ls=":")
    ax1.set_ylim(-0.09 * ymax, 1.6 * ymax)  # headroom so the legend clears the peak
    ax1.set_yticks([t for t in ax1.get_yticks() if t >= 0])
    ax1.set(title="Final posterior", xlabel="p = P(single cookie)", ylabel="density", xlim=(0, 1))
    ax1.legend(fontsize=8, loc="upper right")

    # 2. posterior evolution -----------------------------------------------------
    idx = checkpoint_indices(n)
    colours = plt.cm.viridis(np.linspace(0.1, 0.85, len(idx)))
    ax2.axvspan(zlo, zhi, color=GRAY, alpha=0.2, label="near-fair zone")
    for colour, i in zip(colours, idx):
        curve = beta(cfg.prior + s[i], cfg.prior + m[i]).pdf(x)
        is_prior = n[i] == 0
        ax2.plot(x, curve, "--" if is_prior else "-", color=colour, lw=1.8,
                 label="prior" if is_prior else f"after {n[i]} flips")
    ax2.axvline(0.5, color="k", lw=0.8, ls=":")
    ax2.set(title="Posterior evolution", xlabel="p = P(single cookie)", ylabel="density", xlim=(0, 1))
    ax2.legend(fontsize=8, loc="upper left")

    # 3. estimate over flips ---------------------------------------------------------
    ax3.axhspan(zlo, zhi, color=GRAY, alpha=0.2, label="near-fair zone")
    ax3.axhline(0.5, color="k", lw=0.8, ls=":")
    ax3.fill_between(n, traj["lo"], traj["hi"], color=BLUE, alpha=0.25, label=f"{cfg.cred:.0%} credible interval")
    ax3.plot(n, traj["mean"], color=BLUE, lw=2, label="posterior mean")
    ax3.set_ylim(max(0, min(traj["lo"].min(), zlo) - 0.05), min(1, max(traj["hi"].max(), zhi) + 0.05))
    ax3.set(title="Estimate of p as flips accumulate", xlabel="total flips", ylabel="p")
    ax3.legend(fontsize=8, loc="upper right")

    # 4. P(near-fair) over flips ---------------------------------------------------------
    ax4.plot(n, traj["p_near"], color=BLUE, lw=2)
    ax4.axhline(cfg.conf, color=GREEN, ls="--", label=f"≥ {cfg.conf:.0%}: call it near-fair")
    ax4.axhline(1 - cfg.conf, color=RED, ls="--", label=f"≤ {1 - cfg.conf:.0%}: call it biased")
    # mark where the *final* verdict was reached and then held (+1 near-fair, -1 biased, 0 undecided)
    code = np.where(traj["p_near"] >= cfg.conf, 1, np.where(traj["p_near"] <= 1 - cfg.conf, -1, 0))
    code = np.where(n < cfg.min_flips, 0, code)  # no verdicts before min_flips
    if code[-1] != 0:
        changed = np.flatnonzero(code != code[-1])
        i = changed[-1] + 1 if changed.size else 0
        ax4.plot(n[i], traj["p_near"][i], "o", color="k")
        ax4.annotate(f"verdict held from {n[i]} flips", (n[i], traj["p_near"][i]), textcoords="offset points",
                     xytext=(-14, -30), ha="right", fontsize=9, arrowprops=dict(arrowstyle="-", lw=0.6))
    ax4.set(title=f"P(p within 0.5 ± {cfg.rope})", xlabel="total flips",
            ylabel="posterior probability", ylim=(0, 1))
    ax4.legend(fontsize=8, loc="center right")

    return fig


def save_and_show(fig, path, show=True):
    """Save the figure; also open a window (blocks until closed) if there is a display backend."""
    fig.savefig(path, dpi=130)
    if show and matplotlib.get_backend().lower() != "agg":
        plt.show()
    plt.close(fig)
