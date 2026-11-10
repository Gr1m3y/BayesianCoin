"""The flipping loop: read a key, update the counts, redraw, and draw the plots at the right moments."""
import os

from . import ui
from .model import p_near_fair, verdict
from .plots import make_figure, save_and_show


def load_history(path):
    """
    """
    if not os.path.exists(path):
        return ""
    with open(path) as f:
        return "".join(c for c in f.read() if c in "sm")


def save_history(path, history):
    """
    """
    with open(path, "w") as f:
        f.write(history)


def counts(init, history):
    return init[0] + history.count("s"), init[1] + history.count("m")


def current_verdict(init, history, cfg):
    s, m = counts(init, history)
    return verdict(float(p_near_fair(s, m, cfg)), s + m, cfg)


def draw_plots(history, init, cfg, plots_dir, show, reason):
    """Make and save the figure. Returns a one-line note for the screen."""
    if not history:
        return "No flips recorded yet, so there is nothing to plot."
    os.makedirs(plots_dir, exist_ok=True)
    s, m = counts(init, history)
    path = os.path.join(plots_dir, f"coin_bayes_{s + m}flips_{reason}.png")
    save_and_show(make_figure(history, init, cfg), path, show)
    return f"Plots saved to {path}"


def run(cfg, init, log, plots_dir, show):
    history = load_history(log)
    announced = current_verdict(init, history, cfg) is not None  # don't re-announce a resumed verdict
    note = ""

    try:
        with ui.keypress_mode():
            while True:
                s, m = counts(init, history)
                ui.render(s, m, cfg, history, note)
                note = ""
                key = ui.getkey().lower()

                if key in ("s", "m"):
                    history += key
                    save_history(log, history)
                    if current_verdict(init, history, cfg) and not announced:
                        announced = True
                        note = draw_plots(history, init, cfg, plots_dir, show, "verdict")
                elif key == "u":
                    history = history[:-1]
                    save_history(log, history)
                    announced = current_verdict(init, history, cfg) is not None
                elif key in ("q", ""):  # "" means stdin closed
                    break
    except KeyboardInterrupt:
        pass  # Ctrl-C counts as quit

    print(draw_plots(history, init, cfg, plots_dir, show, "final"))
