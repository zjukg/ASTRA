import json
import os
import re
from typing import Dict, List, Any, Tuple
import numpy as np
from model_clients import OpenaimodelClient

class TableQAEvaluator:
    """表格问答评估器，支持EM和LLM两种评估方法"""
    
    def __init__(self, model: str = None):
        """
        初始化评估器
        
        Args:
            model: 模型名称，如 "deepseek-v3-250324", "deepseek-r1-250120" 等
        """
        if model:
            self.client = OpenaimodelClient(model=model)
        else:
            self.client = None
    
    def normalize_answer(self, answer: Any) -> str:
        """
        标准化答案，用于精确匹配
        
        Args:
            answer: 原始答案
            
        Returns:
            标准化后的答案字符串
        """
        if answer is None:
            return ""
        
        # 转换为字符串
        answer_str = str(answer).strip().lower()
        
        # 移除多余空格
        answer_str = re.sub(r'\s+', ' ', answer_str)
        
        # 移除标点符号
        answer_str = re.sub(r'[^\w\s]', '', answer_str)
        
        return answer_str
    
    def exact_match(self, prediction: Any, ground_truth: Any) -> bool:
        """
        精确匹配评估
        
        Args:
            prediction: 预测答案
            ground_truth: 正确答案
            
        Returns:
            是否匹配
        """
        pred_norm = self.normalize_answer(prediction)
        gt_norm = self.normalize_answer(ground_truth)
        
        # 完全匹配
        if pred_norm == gt_norm:
            return True
        
        # 尝试数值匹配
        try:
            pred_num = float(re.sub(r'[^\d.-]', '', str(prediction)))
            gt_num = float(re.sub(r'[^\d.-]', '', str(ground_truth)))
            return abs(pred_num - gt_num) < 1e-6
        except:
            pass
        
        return False
    
    def llm_judge(self, question: str, prediction: Any, ground_truth: Any) -> bool:
        """
        使用LLM进行答案评估
        
        Args:
            question: 问题
            prediction: 预测答案
            ground_truth: 正确答案
            
        Returns:
            LLM判断是否正确
        """
        if not self.client:
            print("警告: 未配置LLM客户端，LLM评估将返回False")
            return False
        
        prompt = f"""请判断以下问题的预测答案和正确答案是否一致。

            问题：{question}

            正确答案：{ground_truth}

            预测答案：{prediction}

            请判断预测答案是否正确。如果答案在语义上一致（即使表达方式不同），也应该判断为正确。
            如果答案涉及数值，允许微小的数值误差。

            请只回答"正确"或"错误"。
            """

        try:
            response = self.client.generate(
                prompt=prompt,
                temperature=0,
                max_length=10
            )
            
            # generate方法直接返回字符串
            result = response.strip()
            return "正确" in result or "correct" in result.lower() or "yes" in result.lower()
        
        except Exception as e:
            print(f"LLM评估出错: {e}")
            return False
    
    def evaluate_single_question(
        self, 
        data_id,
        question_data,
        use_llm: bool = True
    ) -> Dict[str, Any]:
        """
        评估单个问题
        
        Args:
            question_data: 问题数据
            use_llm: 是否使用LLM评估
            
        Returns:
            评估结果
        """
        question = question_data.get("question", "")
        correct_answer = question_data.get("correct_answer", "")
        generated_answer = question_data.get("generated_answer", "")
        symbolic_answer = question_data.get("symbolic_answer", "")
        # 如果上述都不为空进行评测，如果为空直接最后一步
        # EM评估
        em_textual_label = 1 if self.exact_match(generated_answer, correct_answer) else 0
        em_symbolic_label = 1 if self.exact_match(symbolic_answer, correct_answer) else 0
        
        # LLM评估
        llm_textual_label = 0
        llm_symbolic_label = 0
        
        if use_llm and self.client:
            llm_textual_label = 1 if self.llm_judge(question, generated_answer, correct_answer) else 0
            llm_symbolic_label = 1 if self.llm_judge(question, symbolic_answer, correct_answer) else 0
        
        # 构建结果
        result = {
            "question_index": data_id[0],
            "table_id": data_id[1],
            "question": question,
            "correct_answer": correct_answer,
            "generated_answer": generated_answer,
            "symbolic_answer": symbolic_answer,
            "extra_answer": question_data.get("extra_answer", ""),
            "EM_symbolic_label": em_symbolic_label,
            "EM_textual_label": em_textual_label,
            "LLM_symbolic_label": llm_symbolic_label,
            "LLM_textual_label": llm_textual_label
        }
        
        return result
    
    def evaluate_dataset(
        self,
        input_file: str,
        output_dir: str = "baseline_judge_res",
        use_llm: bool = True
    ) -> Dict[str, float]:
        """
        评估整个数据集
        
        Args:
            input_file: 输入JSON文件路径
            output_dir: 输出目录
            use_llm: 是否使用LLM评估
            
        Returns:
            评估指标字典
        """
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 读取输入数据
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取所有问题
        questions = []
        data_id_list = []
        if isinstance(data, dict):
            # 从table_results中提取所有表格的results
            table_results = data.get("table_results", [])
            for table_result in table_results:
                # 每个表格的results包含该表格的所有问题
                data_index = table_result.get("data_index")
                table_uid = table_result.get("table_uid")
                table_questions = table_result.get("results", [])
                questions.append(table_questions)
                data_id_list.append([data_index,table_uid])
        elif isinstance(data, list):
            # 如果是列表，直接使用
            questions = data
        
        print(f"📊 从输入文件中提取了 {len(questions)} 个问题")
        print(data_id_list)
        # 评估每个问题
        results = []
        for i, question_data in enumerate(questions):
            print(f"评估问题 {i+1}/{len(questions)}...")
            if question_data == []:
                continue
            result = self.evaluate_single_question(data_id_list[i], question_data[0], use_llm=use_llm)
            results.append(result)
        
        # 统计准确率
        total = len(results)
        em_textual_correct = sum(r["EM_textual_label"] for r in results)
        em_symbolic_correct = sum(r["EM_symbolic_label"] for r in results)
        llm_textual_correct = sum(r["LLM_textual_label"] for r in results)
        llm_symbolic_correct = sum(r["LLM_symbolic_label"] for r in results)
        
        # 计算最大准确率（任一方法正确即算正确）
        em_max_correct = sum(
            1 for r in results 
            if r["EM_textual_label"] == 1 or r["EM_symbolic_label"] == 1
        )
        llm_max_correct = sum(
            1 for r in results 
            if r["LLM_textual_label"] == 1 or r["LLM_symbolic_label"] == 1
        )
        
        # 计算准确率
        metrics = {
            "total_questions": total,
            "EM_textual_accuracy": em_textual_correct / total if total > 0 else 0,
            "EM_symbolic_accuracy": em_symbolic_correct / total if total > 0 else 0,
            "EM_max_accuracy": em_max_correct / total if total > 0 else 0,
            "LLM_textual_accuracy": llm_textual_correct / total if total > 0 else 0,
            "LLM_symbolic_accuracy": llm_symbolic_correct / total if total > 0 else 0,
            "LLM_max_accuracy": llm_max_correct / total if total > 0 else 0,
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
        print("评估结果统计")
        print("="*50)
        print(f"总问题数: {total}")
        print(f"\nEM评估:")
        print(f"  Textual准确率: {metrics['EM_textual_accuracy']:.2%} ({em_textual_correct}/{total})")
        print(f"  Symbolic准确率: {metrics['EM_symbolic_accuracy']:.2%} ({em_symbolic_correct}/{total})")
        print(f"  最大准确率: {metrics['EM_max_accuracy']:.2%} ({em_max_correct}/{total})")
        
        if use_llm:
            print(f"\nLLM评估:")
            print(f"  Textual准确率: {metrics['LLM_textual_accuracy']:.2%} ({llm_textual_correct}/{total})")
            print(f"  Symbolic准确率: {metrics['LLM_symbolic_accuracy']:.2%} ({llm_symbolic_correct}/{total})")
            print(f"  最大准确率: {metrics['LLM_max_accuracy']:.2%} ({llm_max_correct}/{total})")
        
        print(f"\n结果已保存到: {output_dir}/")
        print("="*50)
        
        return metrics


def main():
    """主函数示例"""
    import argparse
    
    parser = argparse.ArgumentParser(description='表格问答评估工具')
    parser.add_argument('--input', '-i', required=True, help='输入JSON文件路径')
    parser.add_argument('--output', '-o', default='judge_res', help='输出目录')
    parser.add_argument('--model', '-m', default='deepseek-v3-250324', 
                        help='模型名称 (默认: deepseek-v3-250324)')
    parser.add_argument('--no-llm', action='store_true', help='不使用LLM评估')
    
    args = parser.parse_args()
    
    # 创建评估器
    evaluator = TableQAEvaluator(
        model=args.model if not args.no_llm else None
    )
    
    # 执行评估
    evaluator.evaluate_dataset(
        input_file=args.input,
        output_dir=args.output,
        use_llm=not args.no_llm
    )


if __name__ == "__main__":
    main()
