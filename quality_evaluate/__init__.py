"""
Quality Evaluate Module - 树形表格质量评估模块

该模块提供了完整的树形表格质量评估功能，用于评估从原始表格转换为树形结构的质量。

主要组件：
- TreeQualityEvaluator: 核心评估类
- evaluate_tree_quality: 便捷评估函数
- batch_evaluate: 批量评估函数
"""

from .tree_quality_evaluator import (
    TreeQualityEvaluator,
    evaluate_tree_quality,
    batch_evaluate
)

__all__ = [
    'TreeQualityEvaluator',
    'evaluate_tree_quality',
    'batch_evaluate'
]

__version__ = '1.1.0'

