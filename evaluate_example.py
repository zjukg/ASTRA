"""
评估使用示例
"""
from evaluate import TableQAEvaluator


# 示例1: 使用EM评估（不需要模型）
def example_em_only():
    """仅使用精确匹配评估"""
    evaluator = TableQAEvaluator()
    
    metrics = evaluator.evaluate_dataset(
        input_file="results/qa_results.json",  # 你的输入文件路径
        output_dir="judge_res",
        use_llm=False  # 不使用LLM评估
    )
    
    print("评估完成！")
    return metrics


# 示例2: 使用EM和LLM评估（使用deepseek-v3）
def example_with_llm_deepseek():
    """使用EM和LLM评估，使用DeepSeek模型"""
    evaluator = TableQAEvaluator(
        model="deepseek-v3-250324"  # 使用DeepSeek V3模型
    )
    
    metrics = evaluator.evaluate_dataset(
        input_file="results/qa_results.json",  # 你的输入文件路径
        output_dir="judge_res",
        use_llm=True  # 使用LLM评估
    )
    
    print("评估完成！")
    return metrics


# 示例3: 使用其他模型
def example_with_other_model():
    """使用其他模型进行评估"""
    evaluator = TableQAEvaluator(
        model="gpt-4"  # 或其他支持的模型
    )
    
    metrics = evaluator.evaluate_dataset(
        input_file="results/qa_results.json",
        output_dir="judge_res",
        use_llm=True
    )
    
    return metrics


if __name__ == "__main__":
    # 运行仅EM评估的示例
    print("运行EM评估示例...")
    example_em_only()
    
    # 如果需要LLM评估，取消下面的注释
    # print("\n运行LLM评估示例（DeepSeek）...")
    # example_with_llm_deepseek()

