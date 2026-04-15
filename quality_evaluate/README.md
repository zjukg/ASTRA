# 树形表格质量评估模块

## 📁 文件结构

```
Quality_evaluate/
├── __init__.py                          # 模块初始化文件
├── tree_quality_evaluator.py            # 核心评估类
├── tree_quality_evaluator.py            # Core evaluation implementation
├── test_llm_based_evaluation.py         # LLM_based 方法测试脚本
├── TREE_QUALITY_EVALUATION_README.md    # 详细使用文档
├── LLM_BASED_EVALUATION_UPDATE.md       # LLM_based 适配说明
└── README.md                            # 本文件
```

## 🚀 快速开始

### 1. 在其他模块中导入

从 pipeline 目录的其他文件导入：

```python
from Quality_evaluate import evaluate_tree_quality, TreeQualityEvaluator, batch_evaluate

# 评估单个树
metrics = evaluate_tree_quality(original_table, tree_table)

# 批量评估
results = batch_evaluate([(table1, tree1), (table2, tree2)])
```

### 2. 运行示例脚本

```bash
# 从 pipeline 目录运行
cd table2tree

# 运行基本示例
python -c "from quality_evaluate import evaluate_tree_quality"

# 运行 LLM_based 测试
python Quality_evaluate/test_llm_based_evaluation.py
```

### 3. 在 tableqa.py 中使用

质量评估已集成到 `tableqa.py` 中：

```python
# 在 tableqa.py 中
enable_quality_eval = True  # 启用质量评估
```

## 📊 主要功能

- **信息覆盖率评估**: 检查原表格信息是否被完整保留
- **结构定位准确率**: 验证树形结构的位置关系
- **路径一致性检查**: 确保路径节点来自原表格
- **支持组合键处理**: 适配 LLM_based 方法的组合键格式
- **批量评估**: 支持多个表格的批量质量评估

## 📖 详细文档

- [完整使用文档](./TREE_QUALITY_EVALUATION_README.md)
- [LLM_based 适配说明](./LLM_BASED_EVALUATION_UPDATE.md)

## 🔧 模块导入说明

**从 pipeline 目录的其他文件导入：**
```python
from Quality_evaluate import evaluate_tree_quality
```

**从 Quality_evaluate 目录内的文件导入：**
```python
# 文件开头添加路径
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Quality_evaluate import evaluate_tree_quality
```

## ⚙️ 配置选项

```python
# LLM_based 方法（默认）
metrics = evaluate_tree_quality(table, tree, handle_combined_keys=True)

# rule_based 方法
metrics = evaluate_tree_quality(table, tree, handle_combined_keys=False)
```

## 📝 输出文件位置

- 评估结果保存在：`Quality_evaluate/evaluation_results/`
- 记录文件位于：`pipeline/record/`

## 💡 注意事项

1. 运行示例脚本请从 `pipeline` 目录运行，而不是从 `Quality_evaluate` 目录
2. 导入时使用 `from Quality_evaluate import ...`
3. 评估结果会自动保存到 `evaluation_results` 子文件夹

## 🆘 问题排查

**导入错误？**
- 确保从 `pipeline` 目录运行
- 检查 `__init__.py` 是否存在

**路径错误？**
- 使用 `os.path.dirname(__file__)` 获取当前文件路径
- 使用相对于当前文件的路径引用

---

**版本**: v1.1.0  
**更新日期**: 2025-10-16
