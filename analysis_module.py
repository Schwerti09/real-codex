# -*- coding: utf-8 -*-
"""Forecast and anomaly detection utilities."""

from __future__ import annotations

from typing import List

import numpy as np


def moving_average(data: List[float], window: int = 5) -> List[float]:
    if len(data) < window:
        return data
    cumsum = np.cumsum(np.insert(data, 0, 0))
    result = (cumsum[window:] - cumsum[:-window]) / float(window)
    return result.tolist()


def detect_anomalies(data: List[float], threshold: float = 2.0) -> List[int]:
    mean = np.mean(data)
    std = np.std(data)
    anomalies = [i for i, x in enumerate(data) if abs(x - mean) > threshold * std]
    return anomalies


def forecast_next(data: List[float], steps: int = 1) -> List[float]:
    """Very small naive forecasting using the latest moving average."""
    if not data:
        return [0.0] * steps
    avg = np.mean(data[-5:])
    return [float(avg)] * steps


class EarlyWarningSystem:
    """Tracks a metric and reports anomalies."""

    def __init__(self, threshold: float = 2.0) -> None:
        self.threshold = threshold
        self.history: List[float] = []

    def update(self, value: float) -> bool:
        """Add a value and check for anomaly."""
        self.history.append(value)
        anomalies = detect_anomalies(self.history, self.threshold)
        return len(anomalies) > 0

    def latest_forecast(self) -> float:
        return forecast_next(self.history, 1)[0]
