"""
Batch 评估快速运行示例

直接修改下面的配置参数，然后运行此脚本即可
"""

import os
import sys

# 添加父目录到路径以导入其他模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from Batch_evaluate import TreeBatchEvaluator

# ===================== 配置参数 =====================

# 【基本配置】
DATASET_NAME = "hitab"  # 数据集: "tatqa", "hitab", "aitqa"
TABLE_INDICES = [0, 1, 2, 3, 4, 5]  # 要评估的表格索引列表
N_ITERATIONS = 5  # 每个表格生成多少次树

# 【模型配置】
MODEL_NAME = "Qwen3-14B"  # 模型名称
TEMPERATURE = 0.7  # 温度 (0.3-1.0)
MODEL_TYPE = "opensource"  # "oai" 或 "opensource"

# 【评估配置】
ENABLE_QUALITY_EVAL = True  # 是否启用质量评估
OUTPUT_DIR = "./batch_results"  # 输出目录

# 【运行模式】
BATCH_MODE = True  # True=批量模式, False=单表格模式
SINGLE_TABLE_INDEX = 0  # 单表格模式时使用的索引

# ===================== 执行评估 =====================

def main():
    print("="*80)
    print("🎲 Batch 树评估脚本")
    print("="*80)
    print(f"\n【配置信息】")
    print(f"  数据集: {DATASET_NAME}")
    print(f"  模式: {'批量模式' if BATCH_MODE else '单表格模式'}")
    print(f"  模型: {MODEL_NAME} ({MODEL_TYPE})")
    print(f"  温度: {TEMPERATURE}")
    print(f"  Roll_out 次数: {N_ITERATIONS}")
    print(f"  质量评估: {'启用' if ENABLE_QUALITY_EVAL else '禁用'}")
    
    if BATCH_MODE:
        print(f"  表格数量: {len(TABLE_INDICES)}")
        print(f"  总计生成树: {len(TABLE_INDICES) * N_ITERATIONS} 棵")
    else:
        print(f"  表格索引: {SINGLE_TABLE_INDEX}")
        print(f"  总计生成树: {N_ITERATIONS} 棵")
    
    print("="*80)
    
    # 确认继续
    response = input("\n是否继续？(y/n): ").strip().lower()
    if response != 'y':
        print("❌ 已取消")
        return
    
    # 初始化评估器
    evaluator = TreeBatchEvaluator(output_dir=OUTPUT_DIR)
    
    if BATCH_MODE:
        # 批量模式
        results = evaluator.batch_evaluate(
            dataset_name=DATASET_NAME,
            table_indices=TABLE_INDICES,
            n_iterations=N_ITERATIONS,
            model_name=MODEL_NAME,
            temperature=TEMPERATURE,
            model_type=MODEL_TYPE,
            enable_quality_eval=ENABLE_QUALITY_EVAL
        )
        
        print(f"\n✅ 批量评估完成！")
        print(f"   共评估 {len(TABLE_INDICES)} 个表格")
        print(f"   生成 {len(TABLE_INDICES) * N_ITERATIONS} 棵树")
        
    else:
        # 单表格模式
        from tableqa import sample_from_dataset
        
        # 加载表格
        sample_data, _, table, _, _, table_uid = sample_from_dataset(
            SINGLE_TABLE_INDEX, DATASET_NAME
        )
        
        # Roll_out 评估
        result = evaluator.batch_single_table(
            table=table,
            table_uid=table_uid,
            n_iterations=N_ITERATIONS,
            model_name=MODEL_NAME,
            temperature=TEMPERATURE,
            model_type=MODEL_TYPE,
            enable_quality_eval=ENABLE_QUALITY_EVAL
        )
        
        # 保存结果
        filepath = evaluator.save_results(result)
        
        print(f"\n✅ 单表格评估完成！")
        print(f"   表格 ID: {table_uid}")
        print(f"   生成树数: {N_ITERATIONS}")
        
        # 打印质量统计
        if "quality_statistics" in result["statistics"]:
            stats = result["statistics"]["quality_statistics"]
            print(f"\n📊 质量统计摘要:")
            print(f"   综合得分: {stats['overall_score']['mean']:.2%} ± {stats['overall_score']['std']:.4f}")
            print(f"   覆盖率: {stats['coverage_rate']['mean']:.2%} ± {stats['coverage_rate']['std']:.4f}")
            print(f"   定位准确率: {stats['positioning_accuracy']['mean']:.2%} ± {stats['positioning_accuracy']['std']:.4f}")
            print(f"   一致性: {stats['consistency_rate']['mean']:.2%} ± {stats['consistency_rate']['std']:.4f}")
    
    print(f"\n📁 结果保存在: {OUTPUT_DIR}/")
    print("✅ 所有任务完成！")


if __name__ == "__main__":
    main()

