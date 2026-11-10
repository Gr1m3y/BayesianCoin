"""The terminal screen: one-keystroke input and a text readout with a sketch of the posterior."""
import sys
from contextlib import contextmanager

from scipy.stats import beta

from .model import summary

BLOCKS = " ▁▂▃▄▅▆▇█"
WIDTH = 50  # columns in the text plot


@contextmanager
def keypress_mode():
    """
    One-key-at-a-time input for the whole session. Staying in this mode (instead of
    switching on and off around every read) means keys pressed while the program is
    busy, e.g. drawing plots, are queued instead of being thrown away.
    """
    if not sys.stdin.isatty():  # piped input (tests): nothing to switch
        yield
        return
    import termios
    import tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)  # cbreak, not raw, so Ctrl-C still works
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def getkey():
    """Read one key (call inside keypress_mode)."""
    return sys.stdin.read(1)


def text_plot(s, m, cfg):
    """Three lines: posterior sketch, near-fair zone marker, axis."""
    xs = [(i + 0.5) / WIDTH for i in range(WIDTH)]
    dens = [beta.pdf(x, cfg.prior + s, cfg.prior + m) for x in xs]
    top = max(dens)
    curve = "".join(BLOCKS[round(d / top * (len(BLOCKS) - 1))] for d in dens)
    marks = "".join("=" if abs(x - 0.5) <= cfg.rope else "·" for x in xs)
    axis = "0" + " " * (WIDTH // 2 - 2) + "0.5" + " " * (WIDTH // 2 - 3) + "1"
    return curve, marks, axis


def verdict_line(r, cfg):
    lo, hi = cfg.zone
    if r["verdict"] == "fair":
        return f"✔ {r['p_near']:.1%} sure p is within {lo:.2f}–{hi:.2f}: close enough to fair. You can stop."
    if r["verdict"] == "biased":
        return f"✘ {1 - r['p_near']:.1%} sure p is OUTSIDE {lo:.2f}–{hi:.2f}: the coin looks biased."
    return "… not enough evidence either way yet. Keep flipping."


def render(s, m, cfg, history, note=""):
    r = summary(s, m, cfg)
    curve, marks, axis = text_plot(s, m, cfg)

    print("\033[H\033[J", end="")  # clear screen
    print("COOKIE COIN — Bayesian fairness tracker\n")
    print(f"  flips: {r['n']}    single: {s}    multiple: {m}")
    print(f"  P(single) mean: {r['mean']:.3f}    {cfg.cred:.0%} credible interval: [{r['lo']:.3f}, {r['hi']:.3f}]")
    print(f"  P(p > 0.5, favours single): {r['p_more']:.1%}")
    print(f"  P(p within 0.5 ± {cfg.rope}): {r['p_near']:.1%}   (want ≥ {cfg.conf:.0%})\n")
    print("  posterior for p = P(single cookie)")
    print("  " + curve)
    print("  " + marks + "   = near-fair zone")
    print("  " + axis + "\n")
    print("  " + verdict_line(r, cfg) + "\n")
    print("  last 40:", history[-40:])
    if note:
        print("\n  " + note)
    print("\n  [s] single cookie   [m] multiple cookies   [u] undo   [q] quit (draws the plots)")
