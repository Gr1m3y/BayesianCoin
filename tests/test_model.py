"""Run with:  python -m pytest   (or just: python tests/test_model.py)"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coin_bayes.model import Settings, summary, trajectory, p_near_fair  # noqa: E402

CFG = Settings()


def test_flat_prior_zone_mass():
    # Uniform prior: the zone 0.45-0.55 holds exactly 10% of the probability
    assert abs(p_near_fair(0, 0, CFG) - 0.10) < 1e-9


def test_symmetric_data_is_centred_but_not_yet_called():
    r = summary(129, 129, CFG)
    assert abs(r["mean"] - 0.5) < 1e-9
    assert 0.88 < r["p_near"] < 0.90      # ~89%, as worked out by hand
    assert r["verdict"] is None


def test_enough_even_flips_calls_fair():
    assert summary(200, 200, CFG)["verdict"] == "fair"


def test_lopsided_data_calls_biased():
    assert summary(150, 50, CFG)["verdict"] == "biased"


def test_no_verdict_too_early():
    assert summary(4, 0, CFG)["verdict"] is None                        # 4 flips: too few
    assert summary(4, 0, Settings(min_flips=0))["verdict"] == "biased"  # old behaviour, opt-in


def test_trajectory_counts_and_consistency():
    t = trajectory("ssm", (10, 5), CFG)
    assert list(t["s"]) == [10, 11, 12, 12]
    assert list(t["m"]) == [5, 5, 5, 6]
    assert list(t["n"]) == [15, 16, 17, 18]
    last = summary(12, 6, CFG)             # final entry must equal a direct summary
    assert abs(t["mean"][-1] - last["mean"]) < 1e-12
    assert abs(t["p_near"][-1] - last["p_near"]) < 1e-12


def test_trajectory_with_no_flips_is_just_the_start():
    t = trajectory("", (3, 4), CFG)
    assert list(t["n"]) == [7]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
