"""
Angry Men Experiment Package
===========================

A sophisticated multi-agent deliberation simulation using Tsukuyomi.
"""

__version__ = "1.0.0"

from .run_experiment import JurorAgent, run_simulation
from .analysis.analyzer import ExperimentAnalyzer, analyze_experiment

__all__ = ["JurorAgent", "run_simulation", "ExperimentAnalyzer", "analyze_experiment"]