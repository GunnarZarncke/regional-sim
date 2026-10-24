"""Compact multiplex graph: four private layers plus institutional feed."""
from dataclasses import dataclass
import numpy as np

LAYERS = ("close", "workplace", "community", "online")

@dataclass
class Multiplex:
    neighbors: np.ndarray   # shape (N,4), int32, -1 for unavailable
    layers: tuple = LAYERS

    @classmethod
    def build(cls, zones: np.ndarray, employers: np.ndarray, seed: int):
        n = len(zones)
        r = np.random.default_rng(seed)
        ids = np.arange(n, dtype=np.int32)
        result = np.full((n, 4), -1, dtype=np.int32)
        order = np.argsort(zones, kind="stable")
        for shift, col in [(1, 0), (2, 2)]:
            shifted = np.roll(order, -shift)
            valid = zones[order] == zones[shifted]
            result[order[valid], col] = shifted[valid]
        order = np.argsort(employers, kind="stable")
        shifted = np.roll(order, -1)
        valid = (employers[order] == employers[shifted]) & (employers[order] >= 0)
        result[order[valid], 1] = shifted[valid]
        result[:, 3] = r.integers(0, n, n, dtype=np.int32)
        result[result == ids[:, None]] = -1
        return cls(result)

    def targets(self, i: int, channel: str):
        if channel == "all":
            return [(int(j), self.layers[k]) for k, j in enumerate(self.neighbors[i]) if j >= 0]
        if channel in self.layers:
            j = int(self.neighbors[i, self.layers.index(channel)])
            return [(j, channel)] if j >= 0 else []
        return []

    def clustering_sample(self, size=1000):
        # directed local transitivity across all layers, not a census graph statistic
        n = len(self.neighbors)
        tested = closed = 0
        for i in range(0, n, max(1, n // size)):
            nbr = {int(j) for j in self.neighbors[i] if j >= 0}
            for j in nbr:
                nbr_j = {int(k) for k in self.neighbors[j] if k >= 0}
                tested += len(nbr) - 1
                closed += len((nbr - {j}) & nbr_j)
        return closed / tested if tested else 0.0
