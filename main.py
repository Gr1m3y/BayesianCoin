#!/usr/bin/env python3
"""
Bayesian fairness tracker for the cookie coin. Run this file.

    python3 main.py                    # fresh start, or resume from coin_flips.txt
    python3 main.py --init 47 27       # start from earlier counts (single, multiple)
    python3 main.py --rope 0.10        # "near 50/50" means within +/- 10 points

Keys: s = single cookie, m = multiple cookies, u = undo, q = quit.
Plots are saved to plots/ (and opened) when a verdict is first reached and when you quit.
"""
import argparse

from coin_bayes.model import Settings
from coin_bayes.session import run


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--init", nargs=2, type=int, metavar=("SINGLE", "MULTIPLE"), default=[0, 0],
                    help="counts from earlier flips to start from")
    ap.add_argument("--prior", type=float, default=1.0, help="Beta(prior, prior); 1 = flat (default)")
    ap.add_argument("--rope", type=float, default=0.05, help="half-width of the near-fair zone (default 0.05)")
    ap.add_argument("--conf", type=float, default=0.95, help="confidence needed for a verdict (default 0.95)")
    ap.add_argument("--cred", type=float, default=0.95, help="credible interval level (default 0.95)")
    ap.add_argument("--min-flips", type=int, default=30,
                    help="no verdict before this many total flips (default 30; 0 = no minimum)")
    ap.add_argument("--log", default="coin_flips.txt", help="file that stores the flips")
    ap.add_argument("--plots-dir", default="plots", help="folder for saved plots (default plots/)")
    ap.add_argument("--no-show", action="store_true", help="save plots but don't open a window")
    args = ap.parse_args()

    cfg = Settings(prior=args.prior, rope=args.rope, conf=args.conf, cred=args.cred,
                   min_flips=args.min_flips)
    run(cfg, tuple(args.init), args.log, args.plots_dir, show=not args.no_show)


if __name__ == "__main__":
    main()
