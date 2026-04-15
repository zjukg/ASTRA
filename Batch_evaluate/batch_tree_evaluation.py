"""
Batch Tree Evaluation - 多次生成树并评估质量

该脚本对同一表格进行多次（N次）树形结构生成，记录每次生成的树及其质量指标，
用于分析不同生成结果之间的差异和稳定性。
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any

# 添加父目录到路径以导入其他模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from tableqa import sample_from_dataset
from table2tree import table2tree_llm
from quality_evaluate import evaluate_tree_quality


class TreeBatchEvaluator:
    """树形结构多次生成评估器"""
    
    def __init__(self, output_dir="./batch_results"):
        """
        初始化评估器
        
        Args:
            output_dir: 结果输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def batch_single_table(self, 
                            table: List[List[str]], 
                            table_uid: str,
                            n_iterations: int,
                            model_name: str,
                            temperature: float,
                            model_type: str,
                            enable_quality_eval: bool = True) -> Dict[str, Any]:
        """
        对单个表格进行 N 次 batch 生成树
        
        Args:
            table: 原始表格
            table_uid: 表格唯一标识
            n_iterations: batch 次数
            model_name: 模型名称
            temperature: 温度参数
            model_type: 模型类型 ("oai" 或 "opensource")
            enable_quality_eval: 是否启用质量评估
            
        Returns:
            包含所有 batch 结果的字典
        """
        print(f"\n{'='*80}")
        print(f"🎲 开始对表格 {table_uid} 进行 {n_iterations} 次 Batch")
        print(f"📊 表格大小: {len(table)} 行 × {len(table[0]) if table else 0} 列")
        print(f"🔧 模型: {model_name} (类型: {model_type}), 温度: {temperature}")
        print(f"{'='*80}\n")
        
        batch_results = []
        overall_start_time = time.time()
        
        for batch_idx in range(n_iterations):
            print(f"\n{'─'*60}")
            print(f"🔄 Batch {batch_idx + 1}/{n_iterations}")
            print(f"{'─'*60}")
            
            batch_start_time = time.time()
            
            try:
                # 生成树
                print("🌳 生成树形结构...")
                tree_table_v1, tree_table_v2 = table2tree_llm(
                    table, 
                    model_name, 
                    temperature, 
                    model_type
                )
                tree_table = tree_table_v1
                
                conversion_time = time.time() - batch_start_time
                print(f"✅ 树生成完成，耗时: {conversion_time:.2f}秒")
                print(f"   根节点数量: {len(tree_table) if tree_table else 0}")
                
                # 质量评估
                quality_metrics = None
                if enable_quality_eval and tree_table:
                    try:
                        print("\n📊 开始质量评估...")
                        eval_start_time = time.time()
                        quality_metrics = evaluate_tree_quality(table, tree_table)
                        eval_time = time.time() - eval_start_time
                        print(f"✅ 质量评估完成，耗时: {eval_time:.2f}秒")
                        print(f"   综合得分: {quality_metrics['overall_score']:.2%}")
                    except Exception as e:
                        print(f"⚠️  质量评估失败: {e}")
                        quality_metrics = None
                
                # 记录本次 batch 结果
                batch_result = {
                    "batch_index": batch_idx,
                    "timestamp": time.time(),
                    "conversion_time_seconds": conversion_time,
                    "tree_table": tree_table,
                    "tree_stats": {
                        "root_nodes_count": len(tree_table) if tree_table else 0,
                        "tree_json_size": len(json.dumps(tree_table, ensure_ascii=False)) if tree_table else 0
                    }
                }
                
                # 添加质量指标（简化版）
                if quality_metrics:
                    batch_result["quality_metrics"] = {
                        "coverage_rate": quality_metrics["coverage"]["coverage_rate"],
                        "positioning_accuracy": quality_metrics["positioning"]["positioning_accuracy"],
                        "consistency_rate": quality_metrics["path_consistency"]["consistency_rate"],
                        "overall_score": quality_metrics["overall_score"],
                        "total_paths": quality_metrics["positioning"]["total_paths"],
                        "valid_paths": quality_metrics["positioning"]["valid_paths"]
                    }
                    # 保存完整的质量指标到单独的字段
                    batch_result["quality_metrics_full"] = quality_metrics
                
                batch_results.append(batch_result)
                print(f"✅ Batch {batch_idx + 1} 完成")
                
            except Exception as e:
                print(f"❌ Batch {batch_idx + 1} 失败: {e}")
                batch_results.append({
                    "batch_index": batch_idx,
                    "timestamp": time.time(),
                    "error": str(e),
                    "conversion_time_seconds": 0
                })
        
        total_time = time.time() - overall_start_time
        
        # 计算统计信息
        successful_batches = [r for r in batch_results if "error" not in r]
        
        statistics = self._calculate_statistics(successful_batches)
        
        # 汇总结果
        final_result = {
            "table_uid": table_uid,
            "original_table": table,
            "table_info": {
                "rows": len(table),
                "cols": len(table[0]) if table else 0,
                "total_cells": len(table) * len(table[0]) if table else 0
            },
            "batch_config": {
                "n_iterations": n_iterations,
                "model_name": model_name,
                "temperature": temperature,
                "model_type": model_type,
                "enable_quality_eval": enable_quality_eval
            },
            "batch_results": batch_results,
            "statistics": statistics,
            "total_time_seconds": total_time,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 打印总结
        self._print_summary(final_result)
        
        return final_result
    
    def _calculate_statistics(self, successful_batches: List[Dict]) -> Dict[str, Any]:
        """计算 batch 结果的统计信息"""
        if not successful_batches:
            return {
                "successful_count": 0,
                "failed_count": 0,
                "message": "所有 batch 均失败"
            }
        
        stats = {
            "successful_count": len(successful_batches),
            "avg_conversion_time": sum(r["conversion_time_seconds"] for r in successful_batches) / len(successful_batches),
            "min_conversion_time": min(r["conversion_time_seconds"] for r in successful_batches),
            "max_conversion_time": max(r["conversion_time_seconds"] for r in successful_batches)
        }
        
        # 如果有质量指标，计算质量统计
        batches_with_quality = [r for r in successful_batches if "quality_metrics" in r]
        if batches_with_quality:
            stats["quality_statistics"] = {
                "coverage_rate": {
                    "mean": sum(r["quality_metrics"]["coverage_rate"] for r in batches_with_quality) / len(batches_with_quality),
                    "min": min(r["quality_metrics"]["coverage_rate"] for r in batches_with_quality),
                    "max": max(r["quality_metrics"]["coverage_rate"] for r in batches_with_quality),
                    "std": self._calculate_std([r["quality_metrics"]["coverage_rate"] for r in batches_with_quality])
                },
                "positioning_accuracy": {
                    "mean": sum(r["quality_metrics"]["positioning_accuracy"] for r in batches_with_quality) / len(batches_with_quality),
                    "min": min(r["quality_metrics"]["positioning_accuracy"] for r in batches_with_quality),
                    "max": max(r["quality_metrics"]["positioning_accuracy"] for r in batches_with_quality),
                    "std": self._calculate_std([r["quality_metrics"]["positioning_accuracy"] for r in batches_with_quality])
                },
                "consistency_rate": {
                    "mean": sum(r["quality_metrics"]["consistency_rate"] for r in batches_with_quality) / len(batches_with_quality),
                    "min": min(r["quality_metrics"]["consistency_rate"] for r in batches_with_quality),
                    "max": max(r["quality_metrics"]["consistency_rate"] for r in batches_with_quality),
                    "std": self._calculate_std([r["quality_metrics"]["consistency_rate"] for r in batches_with_quality])
                },
                "overall_score": {
                    "mean": sum(r["quality_metrics"]["overall_score"] for r in batches_with_quality) / len(batches_with_quality),
                    "min": min(r["quality_metrics"]["overall_score"] for r in batches_with_quality),
                    "max": max(r["quality_metrics"]["overall_score"] for r in batches_with_quality),
                    "std": self._calculate_std([r["quality_metrics"]["overall_score"] for r in batches_with_quality])
                }
            }
        
        return stats
    
    def _calculate_std(self, values: List[float]) -> float:
        """计算标准差"""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _print_summary(self, result: Dict[str, Any]):
        """打印评估总结"""
        print(f"\n{'='*80}")
        print("📊 Batch 评估总结")
        print(f"{'='*80}")
        
        stats = result["statistics"]
        config = result["batch_config"]
        
        print(f"\n【配置信息】")
        print(f"  • 表格 ID: {result['table_uid']}")
        print(f"  • Roll_out 次数: {config['n_iterations']}")
        print(f"  • 模型: {config['model_name']} ({config['model_type']})")
        print(f"  • 温度: {config['temperature']}")
        
        print(f"\n【执行统计】")
        print(f"  • 成功次数: {stats['successful_count']}/{config['n_iterations']}")
        print(f"  • 总耗时: {result['total_time_seconds']:.2f} 秒")
        print(f"  • 平均转换时间: {stats.get('avg_conversion_time', 0):.2f} 秒")
        print(f"  • 时间范围: {stats.get('min_conversion_time', 0):.2f}s - {stats.get('max_conversion_time', 0):.2f}s")
        
        if "quality_statistics" in stats:
            print(f"\n【质量指标统计】")
            q_stats = stats["quality_statistics"]
            
            print(f"  信息覆盖率:")
            print(f"    - 平均: {q_stats['coverage_rate']['mean']:.2%}")
            print(f"    - 范围: {q_stats['coverage_rate']['min']:.2%} - {q_stats['coverage_rate']['max']:.2%}")
            print(f"    - 标准差: {q_stats['coverage_rate']['std']:.4f}")
            
            print(f"  结构定位准确率:")
            print(f"    - 平均: {q_stats['positioning_accuracy']['mean']:.2%}")
            print(f"    - 范围: {q_stats['positioning_accuracy']['min']:.2%} - {q_stats['positioning_accuracy']['max']:.2%}")
            print(f"    - 标准差: {q_stats['positioning_accuracy']['std']:.4f}")
            
            print(f"  路径一致性:")
            print(f"    - 平均: {q_stats['consistency_rate']['mean']:.2%}")
            print(f"    - 范围: {q_stats['consistency_rate']['min']:.2%} - {q_stats['consistency_rate']['max']:.2%}")
            print(f"    - 标准差: {q_stats['consistency_rate']['std']:.4f}")
            
            print(f"  综合得分:")
            print(f"    - 平均: {q_stats['overall_score']['mean']:.2%}")
            print(f"    - 范围: {q_stats['overall_score']['min']:.2%} - {q_stats['overall_score']['max']:.2%}")
            print(f"    - 标准差: {q_stats['overall_score']['std']:.4f}")
        
        print(f"\n{'='*80}")
    
    def save_results(self, results: Dict[str, Any], filename: str = None):
        """保存结果到 JSON 文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            table_uid = results["table_uid"]
            n_iterations = results["batch_config"]["n_iterations"]
            filename = f"batch_{table_uid}_n{n_iterations}_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 结果已保存到: {filepath}")
            return filepath
        except Exception as e:
            print(f"\n❌ 保存结果失败: {e}")
            return None
    
    def batch_evaluate(self, 
                     dataset_name: str,
                     table_indices: List[int],
                     n_iterations: int,
                     model_name: str,
                     temperature: float,
                     model_type: str,
                     enable_quality_eval: bool = True) -> List[Dict[str, Any]]:
        """
        批量对多个表格进行 batch 评估
        
        Args:
            dataset_name: 数据集名称
            table_indices: 表格索引列表
            n_iterations: 每个表格的 batch 次数
            model_name: 模型名称
            temperature: 温度参数
            model_type: 模型类型
            enable_quality_eval: 是否启用质量评估
            
        Returns:
            所有表格的评估结果列表
        """
        print(f"\n{'='*80}")
        print(f"🚀 批量 Batch 评估")
        print(f"{'='*80}")
        print(f"  数据集: {dataset_name}")
        print(f"  表格数量: {len(table_indices)}")
        print(f"  每表格 Roll_out 次数: {n_iterations}")
        print(f"  总计将生成: {len(table_indices) * n_iterations} 棵树")
        print(f"{'='*80}\n")
        
        all_results = []
        batch_start_time = time.time()
        
        for idx, table_idx in enumerate(table_indices):
            print(f"\n{'#'*80}")
            print(f"处理表格 {idx + 1}/{len(table_indices)} (索引: {table_idx})")
            print(f"{'#'*80}")
            
            try:
                # 加载表格
                sample_data, whole_paragraph, table, questions, answers, table_uid, _ = sample_from_dataset(
                    table_idx, dataset_name
                )
                
                # 对单个表格进行 batch
                result = self.batch_single_table(
                    table=table,
                    table_uid=table_uid,
                    n_iterations=n_iterations,
                    model_name=model_name,
                    temperature=temperature,
                    model_type=model_type,
                    enable_quality_eval=enable_quality_eval
                )
                
                # 保存单个表格的结果
                self.save_results(result)
                
                all_results.append(result)
                
            except Exception as e:
                print(f"\n❌ 处理表格 {table_idx} 时出错: {e}")
                all_results.append({
                    "table_index": table_idx,
                    "error": str(e),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        
        batch_total_time = time.time() - batch_start_time
        
        # 保存批量结果汇总
        batch_summary = {
            "dataset_name": dataset_name,
            "table_indices": table_indices,
            "n_iterations_per_table": n_iterations,
            "total_tables": len(table_indices),
            "total_trees_generated": len(table_indices) * n_iterations,
            "total_time_seconds": batch_total_time,
            "results": all_results,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 保存批量汇总
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_filename = f"batch_{dataset_name}_{len(table_indices)}tables_n{n_iterations}_{timestamp}.json"
        self.save_results(batch_summary, batch_filename)
        
        # 打印批量总结
        self._print_batch_summary(batch_summary)
        
        return all_results
    
    def _print_batch_summary(self, batch_summary: Dict[str, Any]):
        """打印批量评估总结"""
        print(f"\n{'='*80}")
        print("🎉 批量 Batch 评估完成")
        print(f"{'='*80}")
        print(f"  数据集: {batch_summary['dataset_name']}")
        print(f"  处理表格数: {batch_summary['total_tables']}")
        print(f"  生成树总数: {batch_summary['total_trees_generated']}")
        print(f"  总耗时: {batch_summary['total_time_seconds']:.2f} 秒")
        print(f"  平均每表格: {batch_summary['total_time_seconds'] / batch_summary['total_tables']:.2f} 秒")
        print(f"{'='*80}\n")


if __name__ == "__main__":
    # ===================== 配置参数 =====================
    
    # 数据集配置
    dataset_name = "sstqa"  # 可选: "tatqa", "hitab", "aitqa"
    table_indices = [0, 1, 2, 3, 4, 5]  # 要评估的表格索引列表
    
    # Roll_out 配置
    n_iterations = 5  # 每个表格生成多少次树
    
    # 模型配置
    model_name = "Qwen3-14B"  # 模型名称
    temperature = 0.7  # 温度（建议 0.7-1.0，温度越高差异越大）
    model_type = "opensource"  # "oai" 或 "opensource"
    
    # 评估配置
    enable_quality_eval = True  # 是否启用质量评估
    
    # ===================== 执行评估 =====================
    
    evaluator = TreeBatchEvaluator(output_dir="./batch_results")
    
    # 方式1: 单个表格评估
    if False:  # 设置为 True 启用单表格模式
        # 加载单个表格
        sample_data, whole_paragraph, table, questions, answers, table_uid = sample_from_dataset(
            table_indices[0], dataset_name
        )
        
        # Roll_out 评估
        result = evaluator.batch_single_table(
            table=table,
            table_uid=table_uid,
            n_iterations=n_iterations,
            model_name=model_name,
            temperature=temperature,
            model_type=model_type,
            enable_quality_eval=enable_quality_eval
        )
        
        # 保存结果
        evaluator.save_results(result)
    
    # 方式2: 批量评估（推荐）
    else:
        results = evaluator.batch_evaluate(
            dataset_name=dataset_name,
            table_indices=table_indices,
            n_iterations=n_iterations,
            model_name=model_name,
            temperature=temperature,
            model_type=model_type,
            enable_quality_eval=enable_quality_eval
        )
    
    print("\n✅ 所有评估完成！")

