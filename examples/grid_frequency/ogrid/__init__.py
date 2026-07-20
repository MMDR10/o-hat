"""
Ô Grid Frequency Diagnostic Toolkit (O-Grid)
=============================================
Real-time classification of power grid frequency anomalies using
the Ô helicity diagnostic framework.

Reference:
  DR (2026). Ô Helicity Framework Case Study: Power Grid Frequency
  Anomaly Classification. Zenodo. doi:10.5281/zenodo.21448820
"""

from .classifier import (
    compute_o_metrics,
    time_series_to_trajectory,
    classify_segment,
    classify_stream,
    load_frequency_csv,
    ClassificationResult,
)

__version__ = "1.0.0"
__all__ = [
    "compute_o_metrics",
    "time_series_to_trajectory",
    "classify_segment",
    "classify_stream",
    "load_frequency_csv",
    "ClassificationResult",
]
