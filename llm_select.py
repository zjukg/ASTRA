from model_clients import OpenaimodelClient, ModelClient
from tableqa import sample_from_dataset
import json

file_1 = "judge_res/evaluation_results_mmqa_200.json"

model_1 = OpenaimodelClient(model="gpt-4o-mini")
results = []
correct_count = 0
total_count = 0
# 只有一个答案正确时的统计
only_one_correct_total = 0
only_one_correct_selected = 0
only_one_correct_wrong = 0

with open(file_1, "r") as f:
    data_1 = json.load(f)
for index in range(len(data_1)):
    sample_data, whole_paragraph, table, questions, answers, table_uid, sheet= sample_from_dataset(index,"mmqa")
    data = data_1[index]
    question = data["question"]
    symbolic = data["LLM_symbolic_label"]
    textual = data["LLM_textual_label"]
    answerA = data["symbolic_answer"]
    answerB = data["extra_answer"]
    selector_prompt = f"""
    你是一个严谨的数据验证助手，专注于处理复杂的JSON树结构表格数据。你的任务是根据给定的表格事实，判断哪一个候选答案是正确的。
    # 表格：
    {table}
    # 问题:
    {question}
    # 答案A:
    {answerA}
    # 答案B:
    {answerB}

    #输出要求：
    请不要输出任何解释、标点符号或分析过程。仅输出一个字符："A" 或 "B"。
    
    # 你认为正确的答案：

    """

    response = model_1.generate(selector_prompt, temperature=0.7)

    full_llm_output = "".join(list(response)).strip()
    print(f"Index {index}: 选择 = {full_llm_output}")
    
    # 判断正确性：选A由symbolic决定，选B由textual决定
    if "A" in full_llm_output.upper():
        is_correct = symbolic  # answerA是符号推理，正确性由symbolic_label决定
    else:
        is_correct = textual   # answerB是文本推理，正确性由textual_label决定
    
    total_count += 1
    if is_correct:
        correct_count += 1
    
    # 统计只有一个答案正确的情况
    if symbolic != textual:  # 只有一个答案正确（异或关系）
        only_one_correct_total += 1
        if is_correct:
            only_one_correct_selected += 1
        else:
            only_one_correct_wrong += 1
    
    result = {
        "select" : full_llm_output,
        "symbolic" : symbolic,
        "textual" : textual,
        "is_correct" : is_correct
    }
    results.append(result)
    
    # 实时打印当前准确率
    current_accuracy = correct_count / total_count * 100
    print(f"当前准确率: {correct_count}/{total_count} = {current_accuracy:.2f}%")

# 计算最终准确率
final_accuracy = correct_count / total_count * 100 if total_count > 0 else 0
only_one_correct_accuracy = only_one_correct_selected / only_one_correct_total * 100 if only_one_correct_total > 0 else 0
print(f"\n===== 最终结果 =====")
print(f"总样本数: {total_count}")
print(f"正确数: {correct_count}")
print(f"准确率: {final_accuracy:.2f}%")
print(f"\n===== 只有一个答案正确时的表现 =====")
print(f"只有一个答案正确的样本数: {only_one_correct_total}")
print(f"选对的次数: {only_one_correct_selected}")
print(f"选错的次数: {only_one_correct_wrong}")
print(f"选对准确率: {only_one_correct_accuracy:.2f}%")

output_file = "judge_res/selector_results2.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# 保存汇总信息
summary = {
    "total_count": total_count,
    "correct_count": correct_count,
    "accuracy": final_accuracy,
    "only_one_correct_total": only_one_correct_total,
    "only_one_correct_selected": only_one_correct_selected,
    "only_one_correct_wrong": only_one_correct_wrong,
    "only_one_correct_accuracy": only_one_correct_accuracy
}
summary_file = "judge_res/selector_summary.json"
with open(summary_file, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f"结果已保存到: {output_file}")
print(f"汇总信息已保存到: {summary_file}")
