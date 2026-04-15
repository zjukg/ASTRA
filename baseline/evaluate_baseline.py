"""
Baseline 方法评估脚本
用于评估 direct.py 和 tree_direct.py 生成的输出文件
"""

import json
import os
import sys
import re
from typing import Dict, List, Any

# 添加父目录到路径以导入相关模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from evaluate import TableQAEvaluator


class BaselineEvaluator(TableQAEvaluator):
    """Baseline 方法评估器，继承自 TableQAEvaluator"""
    
    def load_baseline_results(self, input_file: str) -> tuple:
        """
        加载 baseline 输出文件并提取问题数据
        
        Args:
            input_file: baseline 输出文件路径
            
        Returns:
            (questions_list, data_id_list): 问题列表和数据ID列表
        """
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        questions_list = []
        data_id_list = []
        
        # 检测是 direct.py 还是 tree_direct.py 的输出
        # direct.py 使用 "table_results"，tree_direct.py 使用 "results"
        table_results_key = "table_results" if "table_results" in data else "results"
        table_results = data.get(table_results_key, [])
        
        print(f"📋 检测到 baseline 方法: {data.get('method', 'unknown')}")
        print(f"📊 使用键名: {table_results_key}")
        print(f"📈 表格数量: {len(table_results)}")
        
        # 提取所有问题
        for table_result in table_results:
            data_index = table_result.get("data_index")
            table_uid = table_result.get("table_uid", "")
            
            # 获取该表格的所有问题结果
            question_results = table_result.get("results", [])
            
            # 为每个问题创建评估数据
            for q_result in question_results:
                # 构建评估所需的数据结构
                question_data = {
                    "question": q_result.get("question", ""),
                    "correct_answer": q_result.get("correct_answer", ""),
                    "generated_answer": q_result.get("generated_answer", ""),
                    "extracted_answer": q_result.get("extracted_answer", ""),
                    "symbolic_answer": "",  # baseline 方法没有 symbolic_answer
                }
                
                questions_list.append(question_data)
                data_id_list.append([data_index, table_uid])
        
        print(f"✅ 提取了 {len(questions_list)} 个问题")
        return questions_list, data_id_list
    
    def evaluate_single_baseline_question(
        self,
        data_id: List,
        question_data: Dict[str, Any],
        use_llm: bool = True,
        use_extracted: bool = True
    ) -> Dict[str, Any]:
        """
        评估单个 baseline 问题
        
        Args:
            data_id: [data_index, table_uid]
            question_data: 问题数据字典
            use_llm: 是否使用LLM评估
            use_extracted: 是否使用 extracted_answer 进行评估（True）还是 generated_answer（False）
            
        Returns:
            评估结果字典
        """
        question = question_data.get("question", "")
        correct_answer = question_data.get("correct_answer", "")
        
        # 选择使用 extracted_answer 还是 generated_answer
        if use_extracted:
            prediction_answer = question_data.get("extracted_answer", "")
            answer_type = "extracted"
        else:
            prediction_answer = question_data.get("generated_answer", "")
            answer_type = "generated"
        
        # EM评估
        em_label = 1 if self.exact_match(prediction_answer, correct_answer) else 0
        
        # LLM评估
        llm_label = 0
        if use_llm and self.client:
            llm_label = 1 if self.llm_judge(question, prediction_answer, correct_answer) else 0
        
        # 构建结果
        result = {
            "question_index": data_id[0],
            "table_id": data_id[1],
            "question": question,
            "correct_answer": correct_answer,
            "generated_answer": question_data.get("generated_answer", ""),
            "extracted_answer": question_data.get("extracted_answer", ""),
            "answer_type_used": answer_type,
            "EM_label": em_label,
            "LLM_label": llm_label,
        }
        
        return result
    
    def evaluate_baseline(
        self,
        input_file: str,
        output_dir: str = "judge_res",
        use_llm: bool = True,
        use_extracted: bool = True
    ) -> Dict[str, float]:
        """
        评估 baseline 输出文件
        
        Args:
            input_file: baseline 输出文件路径
            output_dir: 输出目录
            use_llm: 是否使用LLM评估
            use_extracted: 是否使用 extracted_answer 进行评估
            
        Returns:
            评估指标字典
        """
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 加载 baseline 结果
        questions_list, data_id_list = self.load_baseline_results(input_file)
        
        if len(questions_list) == 0:
            print("⚠️  未找到任何问题，无法进行评估")
            return {}
        
        # 评估每个问题
        results = []
        for i, (question_data, data_id) in enumerate(zip(questions_list, data_id_list)):
            if (i + 1) % 100 == 0:
                print(f"评估问题 {i+1}/{len(questions_list)}...")
            
            result = self.evaluate_single_baseline_question(
                data_id=data_id,
                question_data=question_data,
                use_llm=use_llm,
                use_extracted=use_extracted
            )
            results.append(result)
        
        # 统计准确率
        total = len(results)
        em_correct = sum(r["EM_label"] for r in results)
        llm_correct = sum(r["LLM_label"] for r in results)
        
        # 计算准确率
        metrics = {
            "total_questions": total,
            "answer_type_used": "extracted" if use_extracted else "generated",
            "EM_accuracy": em_correct / total if total > 0 else 0,
            "LLM_accuracy": llm_correct / total if total > 0 else 0,
            "EM_correct": em_correct,
            "LLM_correct": llm_correct,
        }
        
        # 保存详细结果
        output_file = os.path.join(output_dir, "evaluation_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 保存统计指标
        metrics_file = os.path.join(output_dir, "evaluation_metrics.json")
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
        
        # 打印结果
        print("\n" + "="*50)
        print("Baseline 评估结果统计")
        print("="*50)
        print(f"总问题数: {total}")
        print(f"使用的答案类型: {'extracted_answer' if use_extracted else 'generated_answer'}")
        print(f"\nEM评估:")
        print(f"  准确率: {metrics['EM_accuracy']:.2%} ({em_correct}/{total})")
        
        if use_llm:
            print(f"\nLLM评估:")
            print(f"  准确率: {metrics['LLM_accuracy']:.2%} ({llm_correct}/{total})")
        
        print(f"\n结果已保存到: {output_dir}/")
        print("="*50)
        
        return metrics


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Baseline 方法评估工具')
    parser.add_argument('--input', '-i', required=True, help='Baseline 输出JSON文件路径')
    parser.add_argument('--output', '-o', default='judge_res', help='输出目录')
    parser.add_argument('--model', '-m', default='deepseek-v3-250324', 
                        help='LLM评估模型名称 (默认: deepseek-v3-250324)')
    parser.add_argument('--no-llm', action='store_true', help='不使用LLM评估')
    parser.add_argument('--use-generated', action='store_true', 
                        help='使用 generated_answer 而不是 extracted_answer 进行评估')
    
    args = parser.parse_args()
    
    # 创建评估器
    evaluator = BaselineEvaluator(
        model=args.model if not args.no_llm else None
    )
    
    # 执行评估
    evaluator.evaluate_baseline(
        input_file=args.input,
        output_dir=args.output,
        use_llm=not args.no_llm,
        use_extracted=not args.use_generated
    )


if __name__ == "__main__":
    main()

