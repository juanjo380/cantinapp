"""Co-ocurrencia temporal de picos de venta (Fase 1, sin IA). Lógica pura.

Un producto A tiene un "pico" el día i si vende más que su media de los
`window` días anteriores y al menos `sigma` desviaciones por encima de ella.
B "sube tras A" si, en alguno de los días i+1..i+max_lag, vende más que su
propia media de los `window` días anteriores. score(A→B) = coincidencias / picos de A.

shortcut: no corrige subidas generales del negocio (quincena, festivos) que hacen
subir a todos a la vez; si genera falsos pares, normalizar por la venta total diaria.
"""
import math
from dataclasses import dataclass
from typing import Hashable


@dataclass
class PairScore:
    product_id: Hashable
    related_product_id: Hashable
    peaks: int
    hits: int
    score: float


def trailing_baselines(daily: list[float], window: int) -> list[tuple[float, float] | None]:
    """(media, desviación) de los `window` días anteriores a cada día, sin incluirlo.
    None para los primeros días sin ventana completa."""
    out: list[tuple[float, float] | None] = [None] * min(window, len(daily))
    for i in range(window, len(daily)):
        prev = daily[i - window : i]
        mean = sum(prev) / window
        std = math.sqrt(sum((v - mean) ** 2 for v in prev) / window)
        out.append((mean, std))
    return out


def _peaks(daily: list[float], baselines: list[tuple[float, float] | None], sigma: float) -> list[int]:
    # value > mean evita que una serie constante (std 0) marque pico en cada día
    return [
        i
        for i, base in enumerate(baselines)
        if base is not None and daily[i] > base[0] and daily[i] >= base[0] + sigma * base[1]
    ]


def detect_peaks(daily: list[float], window: int = 14, sigma: float = 2.0) -> list[int]:
    """Índices de los días pico de una serie diaria densa."""
    return _peaks(daily, trailing_baselines(daily, window), sigma)


def cooccurrence_scores(
    series: dict[Hashable, list[float]],
    *,
    window: int = 14,
    sigma: float = 2.0,
    max_lag: int = 3,
    min_hits: int = 3,
) -> list[PairScore]:
    """Pares A→B con al menos `min_hits` coincidencias. Todas las series deben
    cubrir los mismos días (serie densa, 0 los días sin ventas)."""
    baselines = {key: trailing_baselines(daily, window) for key, daily in series.items()}
    pairs: list[PairScore] = []
    for a, daily_a in series.items():
        peaks_a = _peaks(daily_a, baselines[a], sigma)
        if not peaks_a:
            continue
        for b, daily_b in series.items():
            if b == a:
                continue
            base_b = baselines[b]
            hits = sum(
                1
                for p in peaks_a
                if any(
                    p + d < len(daily_b) and base_b[p + d] is not None and daily_b[p + d] > base_b[p + d][0]
                    for d in range(1, max_lag + 1)
                )
            )
            if hits >= min_hits:
                pairs.append(PairScore(a, b, len(peaks_a), hits, round(hits / len(peaks_a), 4)))
    return pairs
