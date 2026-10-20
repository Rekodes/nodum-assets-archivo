"""Privacidad diferencial: el mecanismo de Laplace."""

from __future__ import annotations

import math
import random


class LaplaceMechanism:
    """Ruido de Laplace de escala sensibilidad/ε. Sin semilla: con una conocida, se podría restar."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.SystemRandom()

    def noise(self, sensitivity: float, epsilon: float) -> float:
        scale = sensitivity / epsilon
        u = self._rng.random() - 0.5
        return -scale * math.copysign(1.0, u) * math.log(1 - 2 * abs(u))
