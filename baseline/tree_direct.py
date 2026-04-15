
"""
Tree-Structured Direct Baseline
在生成树形结构表格后，直接将树结构与问题一起发送给模型回答。
"""

import json
import os
import sys
import time
import re
from datetime import datetime

# 将 pipeline 目录加入路径，便于导入 tableqa/mymodel 等模块
current_dir = os.path.dirname(os.path.abspath(__file__))
pipeline_dir = os.path.dirname(current_dir)
sys.path.append(pipeline_dir)

from astra_config import get_local_model_base_url
from model_clients import ModelClient, OpenaimodelClient
from tableqa import TreeTableCache, sample_from_dataset
from table2tree import table2tree_rule, table2tree_llm


def tree_direct_answer(question: str, tree_table, client, model_type="opensource"):
    """直接基于树形表格回答问题"""
    if isinstance(tree_table, str):
        tree_table_str = tree_table
    else:
        tree_table_str = json.dumps(tree_table, ensure_ascii=False, indent=2, default=str)

    prompt = f"""
你是一名高水平的表格分析专家。你的任务是基于以下表格回答问题。

# 注意事项：

1. 请将最终答案用方括号括起来，例如：[答案]。
2. **务必注意问题所要求的答案类型。**
    - 如果问题以 **"Which"** 或 **"What"** 开头（例如："Which item?"、"What category?"），你的答案必须是*名称或描述*（例如："Sell Product A"），**而不是**与其关联的数值。
    - 如果问题以 **"How much"**、**"What is the value"** 或 **"How many"** 开头，则答案必须是*数值*（例如："120000"）。
3. **仅当**答案是数值类型（根据规则2判断）时，你必须检查是否存在相关的"单位"（例如："万"、"百万"），并提供最终经过换算的数值结果。

## 树结构表格:
{tree_table_str}

## 问题:
{question}

## 最终答案:
"""
    print(prompt)
    try:
        if model_type == "opensource":
            return client.test_generate_stream(prompt, max_length=16384, temperature=0.3)
        else:
            return client.generate(prompt, max_length=2000, temperature=0.3)
    except Exception as e:
        print(f"❌ 生成答案时出错: {e}")
        return f"ERROR: {str(e)}"


def load_or_build_tree_table(table, sheet, cache_manager: TreeTableCache, config):
    """从缓存加载或者重新生成树形表格"""
    tree_table = None

    if not config["force_generate_tree"]:
        if cache_manager.has_cached_tree(table):
            tree_table, row_h, col_h = cache_manager.load_tree_table(table)
            if tree_table:
                return tree_table
            print("⚠️  缓存存在但加载失败，将重新生成树形结构。")

    print("📝 未找到缓存或需要重新生成，开始构建树形表格...")
    generation_start = time.time()

    if config["table2_tree_method"] == "rule":
        tree_table = table2tree_rule(
            table,
            config["model_name_table2tree"],
            config["temperature_rule"],
            config["model_type_treecons"],
        )
    else:
        tree_table_v1, tree_table_v2 = table2tree_llm(
            sheet,
            table,
            config["model_name_table2tree"],
            config["temperature_rule"],
            config["model_type_treecons"],
            config["table2_tree_mode"],
        )
        tree_table = tree_table_v1

    generation_time = time.time() - generation_start
    print(f"✅ 树形表格生成完成，耗时 {generation_time:.2f}s，根节点数量: {len(tree_table) if tree_table else 0}")

    cache_manager.save_tree_table(table, tree_table, row_h=[], col_h=[])
    return tree_table


def process_single_sample(index, dataset_name, client, model_type, cache_manager, tree_config):
    """对单个样本进行树结构直接问答"""
    print(f"\n{'='*60}")
    print(f"🔢 处理数据索引: {index} (数据集: {dataset_name})")

    try:
        sample_data, whole_paragraph, table, questions, answers, table_uid, sheet = sample_from_dataset(
            index, dataset_name
        )

        tree_table = load_or_build_tree_table(table, sheet, cache_manager, tree_config)

        if not tree_table:
            raise RuntimeError("树形表格生成失败，无法继续问答。")

        results = []
        start_time = time.time()

        for q_idx, (question, correct_answer) in enumerate(zip(questions, answers)):
            print(f"\n{'-'*40}")
            print(f"📋 问题 {q_idx + 1}/{len(questions)}: {question}")
            print(f"🎯 正确答案: {correct_answer}")

            question_start = time.time()
            generated_answer = tree_direct_answer(question, tree_table, client, model_type)
            question_time = time.time() - question_start

            matches = re.findall(r"\[(.*?)\]", generated_answer or "")
            extracted_answer = matches[-1] if matches else ""

            print(f"✅ 生成答案: {generated_answer}")
            print(f"📦 提取答案: {extracted_answer}")
            print(f"⏱️  耗时: {question_time:.2f}秒")

            results.append(
                {
                    "question_index": q_idx,
                    "question": question,
                    "correct_answer": correct_answer,
                    "generated_answer": generated_answer,
                    "extracted_answer": extracted_answer,
                    "generation_time": question_time,
                }
            )

        total_time = time.time() - start_time
        print(f"\n✅ 样本 {index} 处理完成，总耗时: {total_time:.2f}秒")

        return {
            "data_index": index,
            "table_uid": table_uid,
            "total_time": total_time,
            "questions_count": len(questions),
            "results": results,
        }

    except Exception as e:
        print(f"❌ 处理样本 {index} 时出错: {e}")
        return {
            "data_index": index,
            "error": str(e),
            "results": [],
        }


def main():
    """树结构直接问答主流程"""
    dataset_name = "aitqa"
    model_type = "opensource"  # "opensource" or "oai"
    model_name = "qwen3-8b-instruct"

    # 处理范围
    start_index = 0
    end_index = 386

    # 树结构构建相关配置
    tree_config = {
        "table2_tree_method": "llm_based",  # "rule" or "llm_based"
        "table2_tree_mode": "normal",
        "model_name_table2tree": "deepseek-v3-250324",
        "model_type_treecons": "oai",
        "temperature_rule": 0.3,
        "force_generate_tree": False,
    }

    print("🚀 Tree Direct Baseline 开始运行")
    print(f"📊 数据集: {dataset_name}")
    print(f"🤖 模型类型: {model_type} ({model_name})")
    print(f"🌲 Tree配置: {tree_config['table2_tree_method']} / {tree_config['model_name_table2tree']}")
    print(f"📈 处理范围: {start_index} - {end_index}")

    # 初始化模型客户端
    if model_type == "opensource":
        client = ModelClient(base_url=get_local_model_base_url("http://localhost:8002"))
    else:
        client = OpenaimodelClient(model=model_name)

    cache_manager = TreeTableCache()

    # 结果输出目录
    record_dir = os.path.join(pipeline_dir, "record")
    os.makedirs(record_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    result_file = os.path.join(
        record_dir,
        f"tree_direct_baseline_{dataset_name}_{start_index}-{end_index}_{timestamp}.json",
    )

    all_results = []
    batch_start_time = time.time()

    for index in range(start_index, end_index + 1):
        result = process_single_sample(
            index=index,
            dataset_name=dataset_name,
            client=client,
            model_type=model_type,
            cache_manager=cache_manager,
            tree_config=tree_config,
        )
        all_results.append(result)

    batch_total_time = time.time() - batch_start_time

    output_data = {
        "method": "tree_direct_baseline",
        "dataset": dataset_name,
        "model_type": model_type,
        "model_name": model_name,
        "tree_config": tree_config,
        "batch_info": {
            "start_index": start_index,
            "end_index": end_index,
            "total_time": batch_total_time,
            "processed_samples": len(all_results),
            "total_questions": sum(r.get("questions_count", 0) for r in all_results),
        },
        "results": all_results,
    }

    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print("🎉 Tree Direct Baseline 处理完成！")
    print(f"   - 样本数量: {len(all_results)}")
    print(f"   - 总耗时: {batch_total_time:.2f}秒")
    print(f"   - 平均每样本耗时: {batch_total_time / len(all_results):.2f}秒")
    print(f"   - 结果已保存: {result_file}")


if __name__ == "__main__":
    main()
