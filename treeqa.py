import json
import re
from typing import Any, Dict, List, Optional, Tuple

import sentence_transformers
import torch
import torch.nn.functional as F
from openai import OpenAI

from astra_config import get_default_embedding_path
from model_clients import ModelClient, OpenaimodelClient
from table2tree import normalize_tree_none_values
def extract_non_leaf_nodes(data, path=""):
    """
    递归提取树字典结构中的所有非叶子节点
    返回：[(路径, 键名, 值), ...]
    """
    non_leaf_nodes = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path} - {key}" if path else key
            
            # 如果值是字典类型，说明当前节点是非叶子节点
            if isinstance(value, dict):
                non_leaf_nodes.append((current_path, key, value))
                # 递归提取子节点
                non_leaf_nodes.extend(extract_non_leaf_nodes(value, current_path))
            elif isinstance(value, list):
                # 如果是列表，检查列表中是否有字典
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        list_path = f"{current_path}[{i}]"
                        non_leaf_nodes.append((list_path, f"{key}[{i}]", item))
                        non_leaf_nodes.extend(extract_non_leaf_nodes(item, list_path))
    
    return non_leaf_nodes

def extract_all_nodes(data, path=""):
    """
    递归提取树字典结构中的所有节点（包括叶子节点和非叶子节点）
    返回：[(路径, 键名, 值), ...]
    """
    all_nodes = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path} | {key}" if path else key
            
            # 如果值是字典类型，说明当前节点是非叶子节点
            if isinstance(value, dict):
                all_nodes.append((current_path, key, value))
                # 递归提取子节点
                all_nodes.extend(extract_all_nodes(value, current_path))
            elif isinstance(value, list):
                # 如果是列表，检查列表中是否有字典
                has_dict = any(isinstance(item, dict) for item in value)
                if has_dict:
                    # 包含字典的列表视为非叶子节点
                    all_nodes.append((current_path, key, value))
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            list_path = f"{current_path}[{i}]"
                            all_nodes.append((list_path, f"{key}[{i}]", item))
                            all_nodes.extend(extract_all_nodes(item, list_path))
                else:
                    # 不包含字典的列表视为叶子节点
                    all_nodes.append((current_path, key, value))
            else:
                # 其他类型的值都是叶子节点
                all_nodes.append((current_path, key, value))
                all_nodes.append((f"{current_path} | {value}", value, ""))  # 加入叶子节点
    
    return all_nodes

class TreeQA:
    """基于树形表格的问答系统"""
    
    def __init__(
        self,
        model_type="oai",
        model_name="deepseek-v3-250324",
        api_key="",
        base_url="",
        using_embedding=False,
        embedding_path=None,
        embedding_model_name="",
        embedding_api_key="",
        embedding_base_url="",
    ):
        self.model_type = model_type
        self.model_name = model_name
        self.using_embedding = using_embedding

        self.model_client = ModelClient()
        self.oaimodel_client = OpenaimodelClient(model=model_name, api_key=api_key, base_url=base_url)

        self.embedding_api_mode = bool(embedding_model_name)
        if using_embedding:
            if self.embedding_api_mode:
                self._embedding_client = OpenAI(
                    api_key=embedding_api_key or api_key,
                    base_url=embedding_base_url or base_url,
                )
                self._embedding_model_name = embedding_model_name
            else:
                resolved_embedding_path = embedding_path or get_default_embedding_path()
                if not resolved_embedding_path:
                    raise ValueError(
                        "Embedding retrieval is enabled but no embedding model path was provided. "
                        "Pass embedding_path or set ASTRA_EMBEDDING_MODEL_PATH."
                    )
                self.embedding_model = sentence_transformers.SentenceTransformer(
                    resolved_embedding_path
                )
            self.embedding_re_path = None
        
        print(f"TreeQA model_type={model_type}, model_name={model_name}, using_embedding={using_embedding}")

    def find_relevant_paths(self, tree_table: Dict[str, Any], original_table: List[List], 
                           question: str, embedding_path: List[str], llm_guide_path: str) -> List[List[str]]:
        """
        在树形表格中找到与问题相关的路径
        
        Args:
            tree_table: 树形表格结构
            original_table: 原始表格数据
            question: 用户问题
            embedding_path: 使用embedding模型找到的与问题相关的路径
        Returns:
            相关路径列表，每个路径是从根到叶子的节点序列
        """
        relevant_paths = []
        
        # 使用栈进行深度优先遍历
        # 栈中存储 (当前节点名称, 当前数据, 当前路径)
        stack = [("ROOT", tree_table, ["ROOT"])]
        num_count = 0
        while stack:
            current_node_name, current_data, current_path = stack.pop()
            num_count += 1
            # 如果当前数据是字典且包含子节点
            if isinstance(current_data, dict) and any(isinstance(v, dict) for v in current_data.values()):
                # 获取所有子节点
                child_nodes = {k: v for k, v in current_data.items() } #if isinstance(v, dict) or isinstance(v, str) or isinstance(v,)}
                if child_nodes:
                    # 使用LLM选择有用的子节点
                    print(f"------------------第 {num_count}轮 ------------------------\n")
                    print(child_nodes.keys())
                    print("------------------------------------------------------------\n")
                    selected_children = self._select_relevant_children(
                        current_node_name, child_nodes, question, current_path, embedding_path, llm_guide_path
                    )
                    
                    # 将选中的子节点添加到栈中
                    for child_name in selected_children:
                        if child_name in child_nodes:
                            new_path = current_path + [child_name]
                            stack.append((child_name, child_nodes[child_name], new_path))
            
            # 如果到达叶子节点（包含实际数据值）
            elif isinstance(current_data, dict) and all(not isinstance(v, dict) for v in current_data.values()):
                relevant_paths.append(current_path)
            elif isinstance(current_data, str) or current_data is None or isinstance(current_data, int) or isinstance(current_data, float):
                relevant_paths.append(current_path)
        
        return relevant_paths
    
    def _select_relevant_children(self, parent_node: str, child_nodes: Dict[str, Any], 
                                 question: str, current_path: List[str], embedding_path: List[str], llm_guide_path: str) -> List[str]:
        """
        使用LLM选择与问题相关的子节点
        
        Args:
            parent_node: 父节点名称
            child_nodes: 子节点字典
            question: 用户问题
            current_path: 当前路径
            
        Returns:
            选中的子节点名称列表
        """
        child_names = list(child_nodes.keys())
        # 构造选择提示词
        prompt = self._create_node_selection_prompt(parent_node, child_names, question, current_path, embedding_path, llm_guide_path)
        
        try:
            # 根据model_type选择调用哪个LLM
            if self.model_type == "oai":
                response = self.oaimodel_client.generate(
                    prompt, temperature=0.2, max_length=8192
                )
                # 对于oai模型，将响应转换为字符串
                response_text = "".join(list(response)) if hasattr(response, '__iter__') and not isinstance(response, str) else response
                print("---Model oai response:---",response_text)
            else:  # opensource
                response = self.model_client.test_generate_stream(
                    prompt, temperature=0.2, max_length=16384
                )
                response_text = response
            
            if response_text:
                # 解析LLM响应，提取选中的节点
                selected_nodes = self._parse_node_selection_response(response_text, child_names)
                print(f"🎯 节点选择: {parent_node} -> {selected_nodes}")
                return selected_nodes
        
        except Exception as e:
            print(f"❌ 节点选择失败: {e}")
        
        # 如果LLM调用失败，返回所有子节点（保守策略）
        return child_names
    
    
    def _create_node_selection_prompt(self, parent_node: str, child_names: List[str], 
                                    question: str, current_path: List[str], embedding_path: List[str], llm_guide_path: str) -> str:
        """创建节点选择提示词"""
        # 嵌入模型检索路径: {embedding_path} 先删除了
        path_str = " -> ".join(current_path)

        return f"""
        你是一名表格分析专家。请帮助我选择与问题最相关的子节点以进行后续搜索。

        **关键规则：**
        1.  **不要回答问题本身。** 你的唯一任务是选择下一步需要*搜索*的节点。
        2.  **不要使用任何外部知识或假设。** 仅根据节点名称与用户问题来判断。
        3.  **分析问题意图以决定搜索策略：**
            * **策略A（直接查找）**：如果问题询问具体命名的项目（例如：“‘Product Name - Potato Chips’ 的销售额是多少？”），仅选择这些特定节点。
            * **策略B（条件搜索）**：如果问题询问符合某一条件的项目（例如：“哪些产品的销售额 > 3800？”、“谁的分数最高？”、“列出所有项目...”），则**必须选择所有可用子节点**，因为无法在未展开前判断哪些符合条件。

        当前路径: {path_str}
        父节点: {parent_node}
        可用子节点: {', '.join(child_names)}
        用户问题: {question}
        LLM路径搜索指南: {llm_guide_path}

        请先分析子节点与父节点之间的关系，再判断哪些子节点可能包含回答问题所需的信息。
        仅选择最相关的子节点，避免选择过多无关节点。

        请按以下格式作答：
        Selected nodes: [node_name1, node_name2, ...]
        """
        # return f"""
        #     You are a table analysis expert. I need you to help select the child nodes most relevant to the question.

        #     **CRITICAL RULES:**
        #     1.  **DO NOT answer the question.** Your *only* job is to select the nodes to *search* next.
        #     2.  **DO NOT use any external knowledge or make assumptions.** Base your decision *only* on the node names and the user's question.
        #     3.  **Analyze the question's intent to decide your search strategy:**
        #         * **Strategy A (Direct Lookup):** If the question asks for specific, named items (e.g., "What are the sales for 'Product Name - Potato Chips'?"), select *only* those specific nodes from the `Available child nodes`.
        #         * **Strategy B (Conditional Search):** If the question asks for items that meet a **condition** (e.g., "Which products had sales > 3800?", "Who has the highest score?", "List all items..."), you **MUST select ALL available child nodes**. You cannot know which nodes meet the condition without looking inside each one.

        #     Current path: {path_str}
        #     Parent node: {parent_node}
        #     Available child nodes: {', '.join(child_names)}
        #     User question: {question}

        #     Please first reason the relationship between the child nodes and the parent node, then analyze which child nodes might contain information needed to answer the question. Only select the most relevant child nodes and avoid selecting too many irrelevant nodes.

        #     Please respond in the following format:
        #     Selected nodes: [node_name1, node_name2, ...]
        #     """
    
    def _parse_node_selection_response(self, response: str, available_nodes: List[str]) -> List[str]:
        """解析LLM的节点选择响应"""
        selected_nodes = []
        
        # 尝试找到选中的节点列表
        patterns = [
            r'Selected nodes[:：]\s*\[(.*?)\]',
            r'selected nodes[:：]\s*\[(.*?)\]',
            r'Nodes[:：]\s*\[(.*?)\]',
            r'nodes[:：]\s*\[(.*?)\]',
            r'\[(.*?)\]'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            if matches:
                # 解析节点名称
                node_text = matches[0]
                # 分割并清理节点名称
                nodes = [node.strip().strip('"\'') for node in node_text.split(',')]
                
                # 只保留有效的节点名称
                for node in nodes:
                    if node in available_nodes and node not in selected_nodes:
                        selected_nodes.append(node)
                
                if selected_nodes:
                    break
        
        # 如果没有解析到节点，尝试直接匹配可用节点
        if not selected_nodes:
            for node in available_nodes:
                if node in response:
                    selected_nodes.append(node)
        
        # 如果仍然没有选中任何节点，返回所有节点（保守策略）
        return selected_nodes if selected_nodes else available_nodes
    def embedding_revelant_paths(self, tree_table: Dict[str, Any], original_table: List[List], 
                                 question: str) -> List[List[str]]:
        """
        使用embedding模型找到与问题相关的路径
        """
        non_leaf_nodes = extract_all_nodes(tree_table)
        print(f"提取到 {len(non_leaf_nodes)} 个非叶子节点:\n")
        for i, (path, key, _) in enumerate(non_leaf_nodes[:3]):  # 只显示前2个
            print(f"{i+1}. 路径: {path}")
            print(f"   键名: {key}\n")
        node_texts = [path for path, _, _ in non_leaf_nodes]
        input_texts = [question] + node_texts

        if self.embedding_api_mode:
            resp = self._embedding_client.embeddings.create(
                model=self._embedding_model_name, input=input_texts
            )
            raw = [item.embedding for item in sorted(resp.data, key=lambda x: x.index)]
            embeddings = torch.tensor(raw, dtype=torch.float32)
        else:
            embeddings = self.embedding_model.encode(input_texts, normalize_embeddings=True)
            embeddings = torch.tensor(embeddings, dtype=torch.float32)

        embeddings = F.normalize(embeddings, p=2, dim=1)

        # 计算query与所有节点的相似度
        # query是第一个embedding，节点是剩余的embeddings
        query_embedding = embeddings[0:1]  # shape: [1, dim]
        node_embeddings = embeddings[1:]   # shape: [num_nodes, dim]

        # 计算相似度分数
        scores = (query_embedding @ node_embeddings.T) * 100  # shape: [1, num_nodes]
        scores = scores.squeeze(0)  # shape: [num_nodes]

        # 获取Top-K个最相关的节点
        K = 5  # 可以调整K值
        top_k_scores, top_k_indices = torch.topk(scores, min(K, len(scores)))
        
        print(f"\n与query最相关的Top-{K}个节点：\n")
        print(f"Query: {question}\n")
        print("="*80)

        for rank, (idx, score) in enumerate(zip(top_k_indices.tolist(), top_k_scores.tolist()), 1):
            path, key, value = non_leaf_nodes[idx]
            print(f"\nRank {rank}: 相似度分数 = {score:.2f}")
            print(f"路径: {path}")
            print(f"键名: {key}")
            
            # 显示该节点包含的部分信息
            if isinstance(value, dict):
                print(f"子键数量: {len(value)}")
                # 显示前3个子键
                sub_keys = list(value.keys())[:3]
                if sub_keys:
                    print(f"部分子键: {', '.join(sub_keys)}")
            print("-"*80)

        top_k_results = [(non_leaf_nodes[idx], score) for idx, score in zip(top_k_indices.tolist(), top_k_scores.tolist())]
        # print(f"⭐嵌入模型检索路径: {top_k_results}")
        return top_k_results

    def plan_path_guide(self, tree_table, question):
        Path_search_guide_prompt = f"""
        # Role
        你是一个处理复杂表格数据的专家。该表格已被转换为具有语义层级的JSON树结构。

        # Task
        你的任务是根据用户的【查询问题】和提供的【树结构骨架】，制定一个“节点搜索策略”。
        **注意：你不需要回答问题，只需要告诉我在树中应该如何一步步找到答案。**

        # Input Data
        ## User Query
        {question}

        ## Tree Skeleton (JSON Schema)
        {tree_table}
        *(注意：这里只传入包含层级Key的精简JSON，不要传入底层的具体数值列表，以节省Token并突出结构)*

        # Instruction
        请分析树的层级含义（例如：第一层是年份，第二层是地区，第三层是指标等），结合用户问题，生成一段简短的【搜索导航指南】。

        指南应包含：
        1. **关键路径预测**：为了回答问题，我们需要依次进入哪些层级？
        2. **关键词提示**：在每一层中，应该重点关注哪些关键词？
        3. **逻辑约束**：是否有跨层级的逻辑（例如：需要对比两个不同年份的数据）？

        # Output Format
        请仅输出一段清晰的导航指南，例如：
        "为了回答‘2023年华东地区的总营收’，搜索策略如下：
        1. 在根节点下，首先寻找与‘时间’或‘年份’相关的分支，定位到包含‘2023’的节点。
        2. 在该时间节点下，寻找‘地区’或‘分部’相关的分支，定位到‘华东’。
        3. 最后在‘华东’节点下，寻找具体的财务指标分支，锁定‘总营收’或‘Revenue’字段。"
        """
        if self.model_type == "oai":
            response = self.oaimodel_client.generate(Path_search_guide_prompt, temperature=0.7)
        else:  # opensource
            response = self.model_client.test_generate_stream(Path_search_guide_prompt, temperature=0.7)
        
        full_llm_output = "".join(list(response)) 
        print("⭐LLM_Guide PATH:\n")
        print(full_llm_output)
        print("⭐LLM_Guide PATH------------------------------------------------------\n")
        return full_llm_output

    def process_question(self, tree_table: Dict[str, Any], original_table: List[List], 
                        question: str, whole_paragraph: str) -> Dict[str, Any]:
        """
        处理问题并返回相关路径和数据
        
        Args:
            tree_table: 树形表格结构
            original_table: 原始表格数据
            question: 用户问题
            
        Returns:
            包含相关路径和答案的字典
        """
        print(f"🔍 开始处理问题: {question}")
        
        # 标准化树形表格中的None值，将None转换为字符串"None"
        print("🔧 标准化树形表格中的None值...")
        tree_table = normalize_tree_none_values(tree_table)
        
        print(f"📊 树形表格根节点数量: {len(tree_table)}")
        # 是否使用embedding
        embedding_path = []
        if self.using_embedding:
            top_k_results = self.embedding_revelant_paths(tree_table, original_table, question)
            # print("------------------------------------------------------")
            # print(top_k_results)
            # print("------------------------------------------------------")
            for item in top_k_results:
                path, _ = item
                embedding_path.append(path[0])
        print(f"⭐找到的embedding_path{embedding_path}")
        self.embedding_re_path = embedding_path
        # 找到相关路径
        llm_guide_path = self.plan_path_guide(tree_table, question)
        relevant_paths = self.find_relevant_paths(tree_table, original_table, question, embedding_path, llm_guide_path)
        
        print(f"🎯 找到 {len(relevant_paths)} 条相关路径")
        
        # 汇总结果
        result = {
            "question": question,
            "relevant_paths": relevant_paths,
            "path_details": []
        }
        
        # 为每条路径收集详细信息
        for path in relevant_paths:
            path_detail = {
                "path": path,
                "data": self._get_path_data(tree_table, path)
            }
            result["path_details"].append(path_detail)
            print(f"📍 路径: {' -> '.join(path)}")
        print(f"找到相关路径数量: {len(result['relevant_paths'])}")
                
        final_paths = []
        for i, path_detail in enumerate(result['path_details'], 1):
            path_str = ' -> '.join(path_detail['path'])
            data_str = json.dumps(path_detail['data'], ensure_ascii=False, indent=2, default=str)
            final_paths.append(f"{path_str} : {data_str}")
        
        # 获取最终答案
        final_answer = self.get_final_answer(whole_paragraph, question, final_paths)
        
        return result, final_answer
    
    def _get_path_data(self, tree_table: Dict[str, Any], path: List[str]) -> Any:
        """根据路径获取对应的数据"""
        current_data = tree_table
        
        # 跳过ROOT节点，从第二个节点开始
        for node in path[1:]:
            if isinstance(current_data, dict) and node in current_data:
                current_data = current_data[node]
            else:
                return None
        
        return current_data

    def get_final_answer(self, whole_paragraph: str, 
                        question: str, final_paths: List[str]) -> str:
        """根据路径获取最终答案"""
        # finalQA_prompt = f"""
        # You are a highly skilled table analysis expert. Your task is to answer the question based on the reasoning pahts below and text.
        # # Attetion : 

        #     1. Please output your final answer enclosed in brackets, for example: [answer].
        #     2. **Crucially, pay close attention to the *type* of answer the question requires.**
        #         - If the question asks **"Which"** or **"What"** (e.g., "Which item?", "What category?"), your answer must be the *name or description* (e.g., "Sell Product A"), **NOT** the numerical value associated with it.
        #         - If the question asks **"How much"**, **"What is the value"**, or **"How many"**, your answer must be the *numerical value* (e.g., "120000").
        #     3. **Only if** the answer is a numerical value (as per rule 2), you MUST check if there is an associated "Unit" (e.g., "Ten thousand", "Million") and provide the final, correctly calculated value.
        
        # ## Reasoning Paths:
        # {final_paths}
        # ## Text:
        # {whole_paragraph}
        # ## Question:
        # {question}
        # ## Final Answer:
        # """
        finalQA_prompt = f"""
        你是一名高水平的表格分析专家。你的任务是基于以下推理路径和文本回答问题。

        # 注意事项：

        1. 请将最终答案用方括号括起来，例如：[答案]。
        2. **务必注意问题所要求的答案类型。**
            - 如果问题以 **“Which”** 或 **“What”** 开头（例如：“Which item?”、“What category?”），你的答案必须是*名称或描述*（例如：“Sell Product A”），**而不是**与其关联的数值。
            - 如果问题以 **“How much”**、**“What is the value”** 或 **“How many”** 开头，则答案必须是*数值*（例如：“120000”）。
        3. **仅当**答案是数值类型（根据规则2判断）时，你必须检查是否存在相关的“单位”（例如：“万”、“百万”），并提供最终经过换算的数值结果。
        ## 推理路径:
        {final_paths}

        ## 文本:
        {whole_paragraph}

        ## 问题:
        {question}

        ## 最终答案:
        """

        print("-----"*10,"finalQA_prompt","-----"*10)
        print(finalQA_prompt)
        print("-----"*10,"finalQA_prompt","-----"*10)
        
        # 根据model_type选择调用哪个LLM
        if self.model_type == "oai":
            response = self.oaimodel_client.generate(finalQA_prompt, temperature=0.7)
        else:  # opensource
            response = self.model_client.test_generate_stream(finalQA_prompt, temperature=0.7)
        
        full_llm_output = "".join(list(response)) 
        return full_llm_output

    def symbolic_tree_qa(self, tree_table: Dict[str, Any], original_table: List[List], 
                        question: str, max_iter_num: int = 3) -> Dict[str, Any]:
        """基于符号化树形表格的问答"""
        tree_str = json.dumps(tree_table, indent=2, ensure_ascii=False)
        last_error = None
        last_code = None
        
        # 循环最多 max_iter_num 次
        for attempt in range(max_iter_num):
            try:
                # 第一次使用原始prompt，后续使用包含错误信息的prompt
                if attempt == 0:
                    prompt = self._create_symbolic_tree_prompt(tree_str, question)
                else:
                    # 创建包含错误反馈的prompt
                    prompt = self._create_retry_prompt(tree_str, question, last_code, last_error, attempt)
                
                # 调用LLM
                if self.model_type == "oai":
                    response = self.oaimodel_client.generate(prompt, temperature=0.7)
                else:
                    response = self.model_client.test_generate_stream(prompt, temperature=0.7)
                
                print(f"----------------- symbolic reasoning response (attempt {attempt + 1}) ------------------")
                print(response)
                print(f"----------------- symbolic reasoning response (attempt {attempt + 1}) ------------------")
                
                # 提取代码
                match = re.search(r"<python_code>(.*?)</python_code>", response, re.DOTALL | re.IGNORECASE)
                if not match:
                    last_error = "LLM did not return code in the expected <python_code> tags."
                    last_code = response
                    continue  # 重试
                
                extracted_code = match.group(1).strip()
                extracted_code = "\n".join([line for line in extracted_code.splitlines() if not line.strip().startswith('#')])
                
                if not extracted_code:
                    last_error = "LLM returned empty <python_code> tags."
                    last_code = ""
                    continue  # 重试
                
                # 执行代码
                answer = self._safe_eval(extracted_code, tree_table)
                print("-----------------------------symbolic reasoning answer -----------------------")
                print(answer)
                print("-----------------------------symbolic reasoning answer -----------------------")
                
                # 成功执行，返回结果
                return {
                    "answer": answer,
                    "generated_code": extracted_code,
                    "error": None
                }
                
            except Exception as e:
                # 记录错误信息，准备重试
                last_error = str(e)
                last_code = extracted_code if 'extracted_code' in locals() else None
                print(f"Attempt {attempt + 1} failed: {last_error}")
                
                # 如果是最后一次尝试，返回错误
                if attempt == max_iter_num - 1:
                    return {
                        "error": f"An unexpected error occurred after {max_iter_num} attempts: {e}", 
                        "generated_code": last_code, 
                        "answer": None
                    }
        
        # 理论上不会到达这里，但为了安全添加
        return {
            "error": f"An unexpected error occurred: {last_error}", 
            "generated_code": last_code, 
            "answer": None
        }    
    def _create_symbolic_tree_prompt(self, tree_table: str, 
                                    question: str) -> str:
        """创建符号化树形表格提示词"""
        # Symbolic_prompt = f"""
        # You are an expert Python programmer specializing in data extraction from nested dictionary structures.
        # Your task is to write a safe Python script to answer a question based on a given 'tree_table' (a Python dictionary).

        # # Instructions:
        # 1.  You will be given a dictionary (as a string) which will be available in the execution context as the variable `tree_table`.
        # 2.  You will be given a `question`.
        # 3.  Your script must process the `tree_table` to find the answer. You can use loops, 'if' statements, and variable assignments.
        # 4.  Your script **MUST** assign the final answer to a variable named `final_answer`.
        # 5.  You MUST enclose your Python script within `<python_code>` and `</python_code>` tags.

        # # Security & Safety Constraints (CRITICAL):
        # * **DO NOT** use `import`, `eval`, 'exec', `open`, or any file/system operations (e.g., `os`, `sys`, `subprocess`).
        # * **DO NOT** use `print`.
        # * **DO NOT** access `__builtins__` or `__globals__` outside of the allowed list.
        # * **[FIX] DO NOT** repeat the `tree_table` data or the `question` in your code block. Start writing code immediately.
        
        # # --- [START MODIFICATION] ---
        
        # * **[FIX] ONLY** use basic dictionary/list access (`[]`, `.get()`), loops (`for`, `if`), and the safe built-in functions: 
        #     `sum`, `len`, `int`, `float`, `str`, `list`, `dict`, `set`, `min`, `max`, `round`, `sorted`, `next`, `abs`, `tuple`, `range`, `isinstance`, `iter`, `any`, `all`, `zip`, `enumerate`, `reversed`, `type`.
        # * **Additionally, you can safely use standard methods** of these types (e.g., `.append()`, `.split()`, `.strip()`, `.keys()`, `.values()`, `.items()`, `.startswith()`, `.endswith()`).
        
        # # --- [END MODIFICATION] ---

        # * Any attempt to violate these rules will be rejected.

        # # Answer Type Guidance (Pay close attention):
        # * If the question asks **"Which"** or **"What"** (e.g., "Which item?"), the `final_answer` should be the *string value* (e.g., `final_answer = 'Sell Product A'`).
        # * If the question asks **"How much"**, **"What is the value"**, or **"How many"**, the `final_answer` should be the *numerical value* (e.g., `final_answer = 120000` or `final_answer = 5`).

        # ## Tree Table (as Python Dictionary String):
        # {tree_table}

        # ## Question:
        # {question}

        # ## Your Python Code:        
        
        # """
        Symbolic_prompt = f"""
        你是一名精通 Python 编程的数据提取专家，擅长从嵌套字典结构中提取信息。  
        你的任务是编写一个安全的 Python 脚本，根据给定的 `tree_table`（Python 字典）回答问题。

        # 任务说明：
        1.  你将获得一个以字符串形式提供的字典，在执行环境中该变量名为 `tree_table`。
        2.  你将获得一个 `question`（问题）。
        3.  你的脚本必须解析 `tree_table`，找到问题的答案。可以使用循环、if 语句和变量赋值。
        4.  你的脚本**必须**将最终答案赋值给名为 `final_answer` 的变量。
        5.  你**必须**将 Python 代码包裹在 `<python_code>` 与 `</python_code>` 标签内。

        # 安全与合规约束（关键要求）：
        * **禁止**使用 `import`、`eval`、`exec`、`open` 或任何文件/系统操作（例如 `os`、`sys`、`subprocess`）。
        * **禁止**使用 `print`。
        * **禁止**访问 `__builtins__` 或 `__globals__` 之外的内容。
        * **[修正要求] 禁止**在代码块中重复粘贴 `tree_table` 或 `question` 的内容。请直接开始编写代码。

        # --- [允许操作范围] ---

        * **[修正要求] 仅允许**使用以下安全操作：
        - 基本的字典/列表访问 (`[]`, `.get()`)、循环 (`for`, `if`)；
        - 以下安全内建函数：`sum`, `len`, `int`, `float`, `str`, `list`, `dict`, `set`, `min`, `max`, `round`, `sorted`, `next`, `abs`, `tuple`, `range`, `isinstance`, `iter`, `any`, `all`, `zip`, `enumerate`, `reversed`, `type`。
        * **此外，可安全使用以下类型的标准方法：**
        `.append()`, `.split()`, `.strip()`, `.keys()`, `.values()`, `.items()`, `.startswith()`, `.endswith()`。

        # --- [END] ---

        * 任何违反上述规则的尝试都会被拒绝。

        # 答案类型指导（请特别注意）：
        * 如果问题以 **“Which”** 或 **“What”** 开头（例如：“Which item?”），则 `final_answer` 应为字符串值  
        （例如：`final_answer = 'Sell Product A'`）。
        * 如果问题以 **“How much”**、**“What is the value”** 或 **“How many”** 开头，则 `final_answer` 应为数值  
        （例如：`final_answer = 120000` 或 `final_answer = 5`）。

        ## Tree Table（以 Python 字典字符串形式提供）:
        {tree_table}

        ## 问题:
        {question}

        ## 你的 Python 代码:
        """

        return Symbolic_prompt
    def _create_retry_prompt(self, tree_table: str, question: str, 
                         previous_code: str, error_message: str, 
                         attempt: int) -> str:
        """创建包含错误反馈的重试prompt"""
        retry_prompt = f"""
        你是一名精通 Python 编程的数据提取专家，擅长从嵌套字典结构中提取信息。  
        你的任务是编写一个安全的 Python 脚本，根据给定的 `tree_table`（Python 字典）回答问题。

        **重要提示：你之前生成的代码执行失败了（这是第 {attempt + 1} 次尝试）。请仔细阅读错误信息并修正代码。**

        ## 之前的代码：
        {previous_code if previous_code else "无"}
            ## 错误信息：
        {error_message}

        # 任务说明：
        1.  你将获得一个以字符串形式提供的字典，在执行环境中该变量名为 `tree_table`。
        2.  你将获得一个 `question`（问题）。
        3.  你的脚本必须解析 `tree_table`，找到问题的答案。可以使用循环、if 语句和变量赋值。
        4.  你的脚本**必须**将最终答案赋值给名为 `final_answer` 的变量。
        5.  你**必须**将 Python 代码包裹在 `<python_code>` 与 `</python_code>` 标签内。

        # 安全与合规约束（关键要求）：
        * **禁止**使用 `import`、`eval`、`exec`、`open` 或任何文件/系统操作（例如 `os`、`sys`、`subprocess`）。
        * **禁止**使用 `print`。
        * **禁止**访问 `__builtins__` 或 `__globals__` 之外的内容。
        * **[修正要求] 禁止**在代码块中重复粘贴 `tree_table` 或 `question` 的内容。请直接开始编写代码。

        # --- [允许操作范围] ---

        * **[修正要求] 仅允许**使用以下安全操作：
        - 基本的字典/列表访问 (`[]`, `.get()`)、循环 (`for`, `if`)；
        - 以下安全内建函数：`sum`, `len`, `int`, `float`, `str`, `list`, `dict`, `set`, `min`, `max`, `round`, `sorted`, `next`, `abs`, `tuple`, `range`, `isinstance`, `iter`, `any`, `all`, `zip`, `enumerate`, `reversed`, `type`。
        * **此外，可安全使用以下类型的标准方法：**
        `.append()`, `.split()`, `.strip()`, `.keys()`, `.values()`, `.items()`, `.startswith()`, `.endswith()`。

        # --- [END] ---

        * 任何违反上述规则的尝试都会被拒绝。

        # 答案类型指导（请特别注意）：
        * 如果问题以 **"Which"** 或 **"What"** 开头（例如："Which item?"），则 `final_answer` 应为字符串值  
        （例如：`final_answer = 'Sell Product A'`）。
        * 如果问题以 **"How much"**、**"What is the value"** 或 **"How many"** 开头，则 `final_answer` 应为数值  
        （例如：`final_answer = 120000` 或 `final_answer = 5`）。

        ## Tree Table（以 Python 字典字符串形式提供）:
        {tree_table}

        ## 问题:
        {question}

        ## 请根据错误信息修正代码，并再次提供你的 Python 代码:
        """
        
        return retry_prompt
    def _safe_eval(self, code: str, tree_table: Dict[str, Any]) -> Any:
        """在一个受限的沙盒中安全地执行代码。"""
        
        # 1. [FIX] 使用更智能的正则表达式检查恶意关键词
        #    这个模式 \b(keyword)\b 会匹配独立的单词，
        #    避免误杀 "Evaluation" (eval) 或 "positively" (os)
        DANGEROUS_KEYWORDS = ['import', 'exec', 'open', '__', 'os', 'sys', 'subprocess', 'eval', 'globals', 'locals', 'lambda']
        # 构建正则表达式: \b(import|exec|open|...)\b
        pattern = r"\b(" + "|".join(re.escape(k) for k in DANGEROUS_KEYWORDS) + r")\b"
        
        match = re.search(pattern, code)
        if match:
            keyword_found = match.group(1) # 获取匹配到的关键字
            raise Exception(f"Security violation: Dangerous keyword '{keyword_found}' found in code.")

        # 2. [FIX] 创建一个更完整的、安全的执行环境
        safe_builtins = {
            "sum": sum,
            "len": len,
            "int": int,
            "float": float,
            "str": str,
            "list": list,
            "dict": dict,
            "None": None,
            "True": True,
            "False": False,
            "range": range,
            "isinstance": isinstance,

            "iter": iter,       # <--- 修复你当前问题的关键
            "any": any,         # 检查序列中是否有 True (e.g., any(x > 10 for x in...))
            "all": all,         # 检查序列中是否都为 True
            "zip": zip,         # 用于并行迭代
            "enumerate": enumerate, # 用于带索引的循环
            "reversed": reversed, # 用于反向迭代
            "type": type,       # 用于安全的类型检查 (虽然 isinstance 更好)
            # --- 新增的安全函数 ---
            "set": set,
            "min": min,
            "max": max,
            "round": round,
            "sorted": sorted,
            "next": next,  # 非常有用，但要小心
            "abs": abs,
            "tuple": tuple,
            
            # ".get": dict.get  <-- 这个是多余的, dict() 已经包含了 .get
        }
        
        # 将 tree_table 注入到 'globals' 作用域中
        # safe_globals = {
        #     "__builtins__": safe_builtins,
        #     "tree_table": tree_table 
        # }
        execution_context = {
            "__builtins__": safe_builtins,
            "tree_table": tree_table 
        }
        # 创建一个字典来捕获 exec 创建的局部变量
        # my_locals = {}
        
        try:
            # 在受限的 globals 和 my_locals 中执行
            exec(code, execution_context) #safe_globals, my_locals)
            
            # 检查约定的变量是否存在于局部作用域中
            if 'final_answer' not in execution_context:
                raise Exception("Code execution failed: Script did not assign a value to 'final_answer'.")
                
            # 返回捕获到的值
            return execution_context['final_answer']
            
        except Exception as e:
            # 重新引发异常，以便上层捕获
            # 保持原始异常信息
            raise e        
def main():
    """测试TreeQA功能"""
    # 这里可以添加测试代码
    pass


if __name__ == "__main__":
    main()
