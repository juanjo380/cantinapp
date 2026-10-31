from app.modules.recommendations.domain.cooccurrence import (
    cooccurrence_scores,
    detect_peaks,
    trailing_baselines,
)

DAYS = 100
FLOWER_PEAKS = [20, 40, 60, 80]


def _series(base: float, bumps: dict[int, float]) -> list[float]:
    return [bumps.get(i, base) for i in range(DAYS)]


def test_baseline_excludes_current_day_and_needs_full_window():
    baselines = trailing_baselines([1.0] * 14 + [10.0], window=14)
    assert baselines[:14] == [None] * 14
    assert baselines[14] == (1.0, 0.0)


def test_peak_requires_sigma_deviations():
    noisy = [2.0, 4.0] * 7  # media 3, desviación 1
    assert detect_peaks(noisy + [4.5], window=14, sigma=2.0) == []
    assert detect_peaks(noisy + [5.0], window=14, sigma=2.0) == [14]


def test_zero_baseline_spike_is_peak_but_flat_series_is_not():
    assert detect_peaks(_series(0, {20: 30}), window=14) == [20]
    assert detect_peaks(_series(3, {}), window=14) == []


def test_score_is_hits_over_peaks_and_excludes_self_and_unrelated():
    series = {
        "flores": _series(0, {p: 30 for p in FLOWER_PEAKS}),
        # sube al día siguiente en 3 de los 4 picos de flores
        "chocolates": _series(1, {21: 5, 42: 5, 63: 5}),
        "pan": _series(3, {}),
    }
    pairs = {(p.product_id, p.related_product_id): p for p in cooccurrence_scores(series, window=14)}

    assert set(pairs) == {("flores", "chocolates")}
    pair = pairs[("flores", "chocolates")]
    assert (pair.peaks, pair.hits, pair.score) == (4, 3, 0.75)


def test_pairs_below_min_hits_are_discarded():
    series = {
        "flores": _series(0, {p: 30 for p in FLOWER_PEAKS}),
        "chocolates": _series(1, {21: 5, 42: 5}),
    }
    assert cooccurrence_scores(series, window=14, min_hits=3) == []
    assert len(cooccurrence_scores(series, window=14, min_hits=2)) == 1


def test_rise_outside_lag_window_does_not_count():
    series = {
        "flores": _series(0, {p: 30 for p in FLOWER_PEAKS}),
        "chocolates": _series(1, {p + 4: 5 for p in FLOWER_PEAKS}),
    }
    assert cooccurrence_scores(series, window=14, max_lag=3) == []
