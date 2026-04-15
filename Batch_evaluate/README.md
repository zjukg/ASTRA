# Batch_evaluate Module

该模块用于评估树生成的稳定性和质量，通过对同一表格进行多次（N次）树形结构生成，记录和分析不同生成结果之间的差异。

## 📁 文件说明

- **`__init__.py`**: 使该目录成为 Python 包
- **`batch_tree_evaluation.py`**: 核心评估脚本，包含 `TreeBatchEvaluator` 类
- **`run_rollout_example.py`**: 快速运行示例脚本
- **`ROLLOUT_EVALUATION_README.md`**: 详细使用文档
- **`ROLLOUT_SUMMARY.md`**: 功能总结和快速参考

## 🚀 快速开始

### 方法 1: 使用示例脚本（推荐新手）

```bash
cd table2tree/Batch_evaluate

# 编辑配置参数
nano run_batch_example.py

# 运行
python run_batch_example.py
```

### 方法 2: 在代码中使用

```python
from Batch_evaluate import TreeBatchEvaluator

# 初始化评估器
evaluator = TreeBatchEvaluator(output_dir="./batch_results")

# 批量评估
results = evaluator.batch_evaluate(
    dataset_name="aitqa",
    table_indices=[0, 1, 2],
    n_iterations=5,
    model_name="gpt-4o",
    temperature=0.7,
    model_type="oai",
    enable_quality_eval=True
)
```

### 方法 3: 直接运行主脚本

```bash
cd table2tree/Batch_evaluate
python batch_tree_evaluation.py
```

## 🎯 主要功能

1. **多次生成评估**: 对同一表格进行 N 次树生成（batch）
2. **质量评估集成**: 每次生成都进行完整的质量评估（使用 `Quality_evaluate` 模块）
3. **统计分析**: 自动计算平均值、标准差、最大最小值等统计指标
4. **结果记录**: 保存每棵树的内容、原始表格、表格ID、质量指标
5. **批量处理**: 支持对多个表格进行批量 batch 评估

## 📊 使用场景

1. **评估生成稳定性**: 使用较低温度（0.3-0.5），检查质量指标的标准差
2. **探索生成多样性**: 使用较高温度（0.8-1.0），分析不同树结构
3. **寻找最佳生成**: 从多次生成中选择质量最高的树
4. **模型对比**: 对比不同模型或参数的稳定性和质量

## 📈 输出结果

结果保存在 `batch_results/` 目录下，包含：
- 原始表格数据
- 每次 batch 生成的树
- 每棵树的质量评估指标
- 统计分析结果（均值、标准差、最值）

文件命名格式：
- 单表格: `rollout_{table_uid}_n{n_iterations}_{timestamp}.json`
- 批量: `batch_evaluate_{dataset}_{n_tables}tables_n{n_iterations}_{timestamp}.json`

## 📖 详细文档

请查看 **`ROLLOUT_EVALUATION_README.md`** 获取：
- 详细的配置参数说明
- 输出结果结构详解
- 使用场景示例代码
- 最佳实践建议
- 问题排查指南

## ⚙️ 配置建议

### Roll_out 次数
- **快速测试**: 3 次
- **常规评估**: 5-7 次
- **深度分析**: 10-20 次

### 温度参数
- **高稳定性**: 0.3-0.5
- **平衡**: 0.6-0.8
- **高多样性**: 0.9-1.2

## ⚠️ 注意事项

1. **不使用缓存**: 该模块故意不使用缓存，每次都重新生成，用于观察差异
2. **API 成本**: 多次生成会增加 API 调用次数和成本
3. **时间开销**: N 次 batch 约需单次生成的 N 倍时间
4. **存储空间**: 每次生成都保存完整树结构，注意磁盘空间

## 🔗 依赖模块

- `tableqa`: 用于加载数据集
- `table2tree`: 用于树形结构生成
- `Quality_evaluate`: 用于质量评估

---

**版本**: v1.0  
**创建日期**: 2025-10-16
