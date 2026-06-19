"""Lightweight in-process metrics registry for observability.

The registry collects counters, histograms, and gauges. It is intentionally
simple (no external dependencies) so it can be embedded in the CLI without
increasing startup time. Metrics can be inspected via ``autoship metrics`` or
exported to the telemetry log.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Counter:
    """A monotonically increasing counter."""

    name: str
    description: str
    value: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def inc(self, amount: int = 1) -> None:
        with self._lock:
            self.value += amount

    def to_dict(self) -> dict[str, Any]:
        with self._lock:
            return {"type": "counter", "value": self.value, "description": self.description}


@dataclass
class Gauge:
    """A gauge that can go up or down."""

    name: str
    description: str
    value: float = 0.0

    def set(self, value: float) -> None:
        self.value = float(value)

    def inc(self, amount: float = 1.0) -> None:
        self.value += amount

    def dec(self, amount: float = 1.0) -> None:
        self.value -= amount

    def to_dict(self) -> dict[str, Any]:
        return {"type": "gauge", "value": self.value, "description": self.description}


@dataclass
class Histogram:
    """A histogram that records observed values and reports percentiles."""

    name: str
    description: str
    max_samples: int = 1000
    _values: deque[float] = field(default_factory=lambda: deque[float]())

    def __post_init__(self) -> None:
        self._values = deque[float](maxlen=self.max_samples)

    def observe(self, value: float) -> None:
        self._values.append(float(value))

    @property
    def count(self) -> int:
        return len(self._values)

    @property
    def mean(self) -> float:
        if not self._values:
            return 0.0
        return sum(self._values) / len(self._values)

    def percentile(self, p: float) -> float:
        if not self._values:
            return 0.0
        sorted_values = sorted(self._values)
        k = (len(sorted_values) - 1) * (p / 100.0)
        f = int(k)
        c = min(f + 1, len(sorted_values) - 1)
        if f == c:
            return sorted_values[f]
        return sorted_values[f] + (k - f) * (sorted_values[c] - sorted_values[f])

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "histogram",
            "count": self.count,
            "mean": round(self.mean, 4),
            "p50": round(self.percentile(50.0), 4),
            "p95": round(self.percentile(95.0), 4),
            "p99": round(self.percentile(99.0), 4),
            "description": self.description,
        }


class MetricsRegistry:
    """Thread-safe container for counters, gauges, and histograms."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}

    def counter(self, name: str, description: str = "") -> Counter:
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name=name, description=description)
            return self._counters[name]

    def gauge(self, name: str, description: str = "") -> Gauge:
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(name=name, description=description)
            return self._gauges[name]

    def histogram(self, name: str, description: str = "", max_samples: int = 1000) -> Histogram:
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(
                    name=name, description=description, max_samples=max_samples
                )
            return self._histograms[name]

    def inc(self, name: str, amount: int = 1, description: str = "") -> None:
        self.counter(name, description=description).inc(amount)

    def record(self, name: str, value: float, description: str = "") -> None:
        self.histogram(name, description=description).observe(value)

    def set(self, name: str, value: float, description: str = "") -> None:
        self.gauge(name, description=description).set(value)

    def time(self, name: str, description: str = "") -> Timer:
        return Timer(self, name, description)

    def snapshot(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return {
                **{n: c.to_dict() for n, c in self._counters.items()},
                **{n: g.to_dict() for n, g in self._gauges.items()},
                **{n: h.to_dict() for n, h in self._histograms.items()},
            }

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()


class Timer:
    """Context manager that records elapsed time to a histogram."""

    def __init__(self, registry: MetricsRegistry, name: str, description: str = "") -> None:
        self.registry = registry
        self.name = name
        self.description = description
        self._start: float | None = None

    def __enter__(self) -> Timer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *exc: object) -> None:
        if self._start is not None:
            elapsed = (time.perf_counter() - self._start) * 1000
            self.registry.record(self.name, elapsed, description=self.description)


# Global default registry used by the CLI. Tests can replace or reset this.
_registry: MetricsRegistry = MetricsRegistry()


def get_registry() -> MetricsRegistry:
    """Return the global metrics registry."""
    return _registry


def set_registry(registry: MetricsRegistry) -> MetricsRegistry:
    """Replace the global registry and return it."""
    global _registry
    _registry = registry
    return _registry
