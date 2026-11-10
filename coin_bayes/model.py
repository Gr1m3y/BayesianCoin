"""
Beta-Binomial maths for the coin. No printing and no plotting in here,
so it stays easy to read and easy to test.

p = P(coin lands on the "single cookie" side).
Prior Beta(prior, prior); after s singles and m multiples the posterior is
Beta(prior + s, prior + m).
"""
from dataclasses import dataclass

import numpy as np
from scipy.stats import beta


@dataclass(frozen=True)
class Settings:
    prior: float = 1.0   # Beta(prior, prior); 1 = flat
    rope: float = 0.05   # the "near 50/50" zone is 0.5 +/- rope
    conf: float = 0.95   # confidence needed before we call a verdict
    cred: float = 0.95   # level of the credible interval
    min_flips: int = 30  # never call a verdict before this many total flips

    @property
    def zone(self):
        return 0.5 - self.rope, 0.5 + self.rope


def posterior(s, m, cfg):
    """Posterior over p. s and m may be single numbers or numpy arrays."""
    return beta(cfg.prior + s, cfg.prior + m)


def p_near_fair(s, m, cfg):
    """Posterior probability that p lies inside the near-fair zone."""
    lo, hi = cfg.zone
    post = posterior(s, m, cfg)
    return post.cdf(hi) - post.cdf(lo)


def credible_interval(s, m, cfg):
    tail = (1 - cfg.cred) / 2
    post = posterior(s, m, cfg)
    return post.ppf(tail), post.ppf(1 - tail)


def verdict(p_near, n, cfg):
    """'fair' / 'biased' once the evidence is strong enough, otherwise None."""
    if n < cfg.min_flips:  # with a flat prior a few identical flips already look "biased"
        return None
    if p_near >= cfg.conf:
        return "fair"
    if p_near <= 1 - cfg.conf:
        return "biased"
    return None


def summary(s, m, cfg):
    """Everything the screen needs for one (s, m) state."""
    post = posterior(s, m, cfg)
    lo, hi = credible_interval(s, m, cfg)
    p_near = float(p_near_fair(s, m, cfg))
    return {
        "n": s + m, "s": s, "m": m,
        "mean": float(post.mean()),
        "lo": float(lo), "hi": float(hi),
        "p_near": p_near,
        "p_more": float(post.sf(0.5)),   # P(p > 0.5), i.e. favours single
        "verdict": verdict(p_near, s + m, cfg),
    }


def trajectory(history, init, cfg):
    """
    The posterior after every flip, as arrays for plotting.

    history: string of 's' / 'm' characters, oldest first
    init:    (singles, multiples) counted before this history started
    Entry 0 is the starting state (prior plus init); entry k is after k flips.
    """
    single = np.array([c == "s" for c in history], dtype=int)
    s = init[0] + np.concatenate([[0], np.cumsum(single)]).astype(int)
    m = init[1] + np.concatenate([[0], np.cumsum(1 - single)]).astype(int)
    lo, hi = credible_interval(s, m, cfg)
    return {
        "n": s + m, "s": s, "m": m,
        "mean": posterior(s, m, cfg).mean(),
        "lo": lo, "hi": hi,
        "p_near": p_near_fair(s, m, cfg),
    }
