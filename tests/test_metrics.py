"""Unit tests for core metric logic. These test INVARIANTS, not published
values. `assert roas == 3.20` breaks whenever data arrives; `assert roas ==
revenue / spend` catches the bug class that produced this repo's failed
figures."""
import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def toy_jobs():
    """Row B carries the tip-drop bug: 100 + 25 logged as 100."""
    return pd.DataFrame({
        "customer":      ["A", "B", "C", "D", "E"],
        "job_value":     [100.0, 100.0, 200.0, 90.0, 150.0],
        "tip":           [0.0, 25.0, 0.0, 40.0, np.nan],
        "logged_total":  [100.0, 100.0, 200.0, 130.0, 150.0],
        "channel":       ["Meta Ads"] * 4 + ["D2D"],
        "ad_attributed": [1, 1, 0, 1, 0],
    })


def recompute_total(df):
    return df.job_value.fillna(0) + df.tip.fillna(0)


def roas(revenue, spend):
    if spend is None or pd.isna(spend) or spend == 0:
        return None
    return round(revenue / spend, 2)


def test_total_is_recomputed_not_trusted(toy_jobs):
    assert recompute_total(toy_jobs).tolist() == [100.0, 125.0, 200.0, 130.0, 150.0]


def test_tip_drop_is_detected(toy_jobs):
    bad = toy_jobs.logged_total != recompute_total(toy_jobs)
    assert bad.sum() == 1
    assert toy_jobs.loc[bad, "customer"].item() == "B"


def test_blank_tip_does_not_null_the_total(toy_jobs):
    assert not recompute_total(toy_jobs).isna().any()


def test_gross_roas_overstates_when_organic_is_mistagged(toy_jobs):
    d = toy_jobs.assign(total=recompute_total(toy_jobs))
    meta = d[d.channel == "Meta Ads"]
    gross = roas(meta.total.sum(), 100.0)
    attributed = roas(meta[meta.ad_attributed == 1].total.sum(), 100.0)
    assert gross == 5.55
    assert attributed == 3.55
    assert gross > attributed


def test_attributed_revenue_is_subset_of_channel_revenue(toy_jobs):
    d = toy_jobs.assign(total=recompute_total(toy_jobs))
    meta = d[d.channel == "Meta Ads"]
    assert meta[meta.ad_attributed == 1].total.sum() <= meta.total.sum()


@pytest.mark.parametrize("spend", [0, 0.0, None, np.nan])
def test_zero_or_missing_spend_returns_none_not_inf(spend):
    assert roas(1000.0, spend) is None


def test_zero_revenue_is_zero_not_an_error():
    assert roas(0.0, 100.0) == 0.0


def test_empty_frame_does_not_raise(toy_jobs):
    assert recompute_total(toy_jobs.iloc[0:0]).sum() == 0


def test_cost_per_event_must_include_zero_event_rows():
    """Cost per message computed only over rows that produced messages is not
    cost per message. This is the bug that made p=0.45 look like p=0.0005."""
    rows = pd.DataFrame({"spend": [10.0]*4, "messages": [5.0, 0.0, 0.0, 5.0]})
    cond = rows[rows.messages > 0]
    assert cond.spend.sum() / cond.messages.sum() == 2.0
    assert rows.spend.sum() / rows.messages.sum() == 4.0
