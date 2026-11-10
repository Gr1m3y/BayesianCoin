"""
Beta-Binomial distribution code for the coin. This module only contains the
code needed to run the simulation, including generating the prior distribution
from the initial settings, updating the posterior distribution, and checking
if enough data has been collected to make a call.

p = P(coin lands on the "single cookie" side).
Prior Beta(prior, prior); after s singles and m multiples the posterior is
Beta(prior + s, prior + m).
"""
from dataclasses import dataclass

import numpy as np
from scipy.stats import beta


@dataclass(frozen=True)
class Settings:
    """
    Initial settings
        prior       - Value to use for the prior distribution (1.0 assumes the distribution is flat)
        rope        - Maximum acceptable distance from 50/50 to be considered fair
        conf        - Confidence needed before a verdict is made (i.e., 95% confidence)
        cred        - Size of credible interval to report (i.e., 95% credible interval)
        min_flips   - The minimum required flips before a call can be made
    """
    prior: float = 1.0   # Beta(prior, prior); 1 = flat
    rope: float = 0.05   # the "near 50/50" zone is 0.5 +/- rope
    conf: float = 0.95   # confidence needed before we call a verdict 
    cred: float = 0.95   # level of the credible interval
    min_flips: int = 30  # never call a verdict before this many total flips

    @property
    def zone(self):
        return 0.5 - self.rope, 0.5 + self.rope


def posterior(s: int, m: int, cfg: Settings):
    """
    Returns the posterior by updating the prior with the number of times the coin came up with a single
    cookie (s) and the number of times it came up with multiple cookies (m). This uses a beta binomial
    distribution (standard)
    """
    return beta(cfg.prior + s, cfg.prior + m)


def p_near_fair(s: int, m: int, cfg: Settings):
    """
    Determine the posterior probability that the result lies within the near-fair zone (i.e., 
    50/50 +/- rope from settings)

        s   - Number of single-cookie flips
        m   - Number of multi-cookie flips
        cfg - Settings
    """
    lo, hi = cfg.zone
    post = posterior(s, m, cfg)
    return post.cdf(hi) - post.cdf(lo)


def credible_interval(s: int, m: int, cfg: Settings):
    """
    Calculate credible interval according to the config (cfg)
    """
    tail = (1 - cfg.cred) / 2
    post = posterior(s, m, cfg)
    return post.ppf(tail), post.ppf(1 - tail)


def verdict(p_near: float, n: int, cfg: Settings):
    """
    Determine if, given the evidence, the coin seems fair or biased
    
        p_near  - Equal to P(p<=0.95) - P(p<=0.45)
        n       - Number of times the coin has been tossed
        cfg     - Settings
    """
    if n < cfg.min_flips:  # with a flat prior a few identical flips already look "biased"
        return None
    if p_near >= cfg.conf:
        return "fair"
    if p_near <= 1 - cfg.conf:
        return "biased"
    return None


def summary(s, m, cfg):
    """
    Generate summary of the current state for printing to screen

        s   - Number of single-cookie flips
        m   - Number of multi-cookie flips
        cfg - Settings
    """
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

        history - String of flips with 'm' meaning aa multi-cookie flipe and s meaning
                    a single-cookie flip, in the order they occurred (e.g., smmmsms)
        init    - Tuple in the form (single-cookie flips, multi-cookie flips)
        cfg     - Settings

    Note: The first entry in trajectory is init and is then updated one flip at a time
    from history
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
