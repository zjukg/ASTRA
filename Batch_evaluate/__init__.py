"""
Batch_evaluate Module

This module provides tools for evaluating the stability and quality of tree generation
through multiple batch iterations (N times generation for the same table).

Main Components:
- TreeBatchEvaluator: Core evaluator for performing multiple tree generations
"""

from .batch_tree_evaluation import TreeBatchEvaluator

__all__ = ['TreeBatchEvaluator']

__version__ = "1.0.0"

