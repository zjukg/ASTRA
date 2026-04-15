# -------------------------------------------- 提示工程设计分步转化 -------------------------------------
# HEADER_ANALYSIS_PROMPT = """
# You are an expert data analyst specializing in parsing complex table structures.

# Your task is to analyze the initial rows of the provided table to determine the single, canonical header for each column. You must follow these rules with extreme precision:

# 1.  **Strict Wording Preservation**: You MUST preserve the original wording from the table cells. DO NOT invent new names or summaries (e.g., if a cell is "Total Students", the header must contain "Total Students", not "Total Students Metrics").
# 2.  **Hierarchical Combination**: If information is spread across multiple header rows, combine them using the format: `[Lower-level Header] - [Higher-level Header]`. The part before the " - " MUST be the exact text from the most specific (usually lowest) header row.
# 3.  **Exact Column Match**: The number of strings in your output array must exactly match the number of columns in the data rows.

# The table is provided as a JSON array of arrays.

# [INPUT TABLE]:
# {TABLE_AS_JSON_STRING}

# Your output MUST be a single, valid JSON array of strings, representing the normalized headers. Provide no explanations.

# [NORMALIZED HEADERS]:
# """
# HIERARCHY_VALUE_IDENTIFICATION_PROMPT = """
# You are an expert data architect analyzing a table's logical structure.

# You will be given a table and its normalized headers. Your task is to identify which columns serve as 'Hierarchy Keys' and which serve as 'Value Leaves'.

# Definitions:
# -   **Hierarchy Keys**: Columns used for grouping and creating nested levels. Their values often repeat in blocks.
# -   **Value Leaves**: The final data points associated with a specific hierarchy path.
# -   **Semantic Groups (Optional)**: If the 'Value Leaves' can be logically grouped under a common theme from a higher-level header, define these groups. **Crucially, the group names must be derived directly from the original table's headers.** Do not create new group names. If no such grouping exists, leave this empty.

# [INPUT TABLE]:
# {TABLE_AS_JSON_STRING}

# [NORMALIZED HEADERS]:
# {NORMALIZED_HEADERS_FROM_STEP_1}

# Your output MUST be a single, valid JSON object with the following structure. Adhere strictly to the provided header names.

# {{
#   "hierarchy_keys": ["header1", "header2", ...],
#   "value_leaves": ["header3", "header4", ...],
#   "semantic_groups": {{
#     "OriginalGroupName1": ["header_a", "header_b"]
#   }}
# }}

# Do not provide any explanations.

# [HIERARCHY DEFINITION]:
# """

# FINAL_JSON_TREE_CONSTRUCTION = """
# You are a highly skilled data transformation engine that converts tabular data into a nested JSON tree while preserving all semantic information.

# You will be given the original table, its normalized headers, and a hierarchy definition. You must construct the final JSON tree based on these inputs, following these critical rules:

# 1.  **Semantic Hierarchy Keys**: For each `hierarchy_key`, the key in the final JSON MUST be formatted as **`[Header Name] - [Cell Value]`**. You **must** use a " - " (space, hyphen, space) to separate the header name from the cell value (e.g., if the header is "Grade" and the value is "1", the JSON key must be "Grade - 1"). This ensures the meaning of the key is not lost.
# 2.  **Strict Name Preservation for Leaves**: The keys for the `value_leaves` in the final JSON MUST be the exact strings from the normalized headers. Do not alter or summarize them.
# 3.  **Structure Generation**:
#     - Iterate through the data rows (skipping headers).
#     - Use the formatted semantic hierarchy keys from Rule #1 to create or navigate the nested JSON structure.
#     - At the deepest level, create an object for the values.
#     - If `semantic_groups` is defined, use the group names (which must come from the original headers) as an additional layer of nesting.
#     - Populate the final object with key-value pairs from the `value_leaves` columns.
# 4.  **No Data Omission**: You must not omit any data cell content from the INPUT TABLE. All data must be populated into the generated tree.
# [INPUT TABLE]:
# {TABLE_AS_JSON_STRING}

# [NORMALIZED HEADERS]:
# {NORMALIZED_HEADERS_FROM_STEP_1}

# [HIERARCHY DEFINITION]:
# {HIERARCHY_DEFINITION_FROM_STEP_2}

# Your output MUST be a single, valid JSON object representing the entire table as a tree. Ensure all data types (numbers, strings) are correctly preserved. Do not provide any other text or explanations.

# [FINAL JSON TREE]:
# """
HEADER_ANALYSIS_PROMPT = """
你是一名专精于解析复杂表格结构的数据分析专家。

你的任务是分析所提供表格的前几行，确定每一列的唯一规范化表头。你必须严格遵守以下规则：

1.  **严格保留原始措辞**：你必须保留表格单元格中的原始文字。禁止创造新名称或摘要。
    （例如：如果单元格内容为“Total Students”，则表头必须包含“Total Students”，而不是“Total Students Metrics”。）
2.  **层级组合**：如果信息分布在多行表头中，请按如下格式进行组合：`[下层表头] - [上层表头]`。
    “ - ”前的部分必须是最具体层（通常是最下层）的原始文字。
3.  **列数严格匹配**：输出数组中的字符串数量必须与数据行中的列数完全一致。

表格以 JSON 数组的形式提供。

[输入表格]:
{TABLE_AS_JSON_STRING}

你的输出必须是一个单一、有效的 JSON 字符串数组，代表标准化表头。不要提供任何解释。

[规范化表头]:
"""

# HIERARCHY_VALUE_IDENTIFICATION_PROMPT = """
# 你是一名专注于表格逻辑结构分析的数据架构专家。

# 你将获得一个表格及其规范化表头。你的任务是识别哪些列属于“层级键（Hierarchy Keys）”，哪些属于“数值叶节点（Value Leaves）”。

# 定义：
# -   **层级键（Hierarchy Keys）**：用于分组并形成嵌套层次的列。其值通常在块状区域中重复。
# -   **数值叶节点（Value Leaves）**：对应某一特定层级路径的最终数据值。
# -   **语义组（可选）**：如果“数值叶节点”可根据高层表头的语义逻辑进行分组，请定义这些组。
#     **关键要求**：组名必须直接来源于原始表格表头，禁止创造新的组名。若不存在此类分组，则留空。

# [输入表格]:
# {TABLE_AS_JSON_STRING}

# [规范化表头]:
# {NORMALIZED_HEADERS_FROM_STEP_1}

# 你的输出必须是一个单一、有效的 JSON 对象，且严格遵循以下结构格式：

# {{
#   "hierarchy_keys": ["header1", "header2", ...],
#   "value_leaves": ["header3", "header4", ...],
#   "semantic_groups": {{
#     "OriginalGroupName1": ["header_a", "header_b"]
#   }}
# }}

# 不要提供任何解释。

# [层级定义]:
# """
##### ---------------------------------------------------------- 简单表格鉴别 --------------------------------
HIERARCHY_VALUE_IDENTIFICATION_PROMPT = """
你是一名专注于表格逻辑结构分析的数据架构专家。

你将获得一个表格及其规范化表头。你的任务是识别哪些列属于"层级键（Hierarchy Keys）"，哪些属于"数值叶节点（Value Leaves）"。

## 核心判断原则：

### 简单表格识别标准（优先判断）：
如果表格满足以下特征，则应视为**简单平面表格**：
1. 每行记录相对独立，列之间没有明显的父子包含关系
2. 大多数列的值在表格中很少重复或几乎不重复
3. 表格主要用于记录事务、日志、清单等平面数据

**对于简单表格的处理策略**：
- **只选择1个最主要的列作为 hierarchy_key**（通常是：时间列、ID列、编号列、序号列等唯一标识列）
- **所有其他列都应归类为 value_leaves**
- **不要强制创建多层嵌套结构**
- **对于多个简单表格，通过外键将其链接起来**

### 复杂表格识别标准：
如果表格具有以下特征，才应使用多层级结构：
1. 存在明显的分组层级关系（如：地区 > 城市 > 门店）
2. 某些列的值大量重复，形成分组块
3. 数据具有明确的聚合汇总关系
4. 具有多个简单表格，并且有明显主键外键关系

## 定义：
-   **层级键（Hierarchy Keys）**：用于分组并形成嵌套层次的列。
    - 对于简单表格：通常只有1个（如日期、ID、编号）
    - 对于复杂表格：可以有多个形成层级嵌套
-   **数值叶节点（Value Leaves）**：对应某一特定层级路径的最终数据值，包括所有描述性属性和数值数据。
-   **语义组（可选）**：如果"数值叶节点"可根据高层表头的语义逻辑进行分组，请定义这些组。
    **关键要求**：组名必须直接来源于原始表格表头，禁止创造新的组名。若不存在此类分组，则留空。

## 判断流程：
1. 首先判断是否为简单表格
2. 如果是简单表格，选择最主要的1个列作为 hierarchy_key
3. 如果是复杂表格，才选择多个列形成层级

[输入表格]:
{TABLE_AS_JSON_STRING}

[规范化表头]:
{NORMALIZED_HEADERS_FROM_STEP_1}

## 输出要求：
你的输出必须是一个单一、有效的 JSON 对象，且严格遵循以下结构格式：

{{
  "table_type": "simple" 或 "complex",
  "analysis_reason": "简要说明判断理由",
  "hierarchy_keys": ["header1", "header2", ...],
  "value_leaves": ["header3", "header4", ...],
  "semantic_groups": {{
    "OriginalGroupName1": ["header_a", "header_b"]
  }}
}}

**重要提示**：
- 如果 table_type 为 "simple"，hierarchy_keys 通常只应包含1个元素
- 不要为了创建层级而强行嵌套
- 优先保持数据结构的简洁性和可读性

不要提供JSON之外的任何解释。

[层级定义]:
"""

FINAL_JSON_TREE_CONSTRUCTION = """
你是一名高度专业的数据转换引擎，负责将表格数据转换为保留全部语义信息的嵌套 JSON 树。

你将获得原始表格、其规范化表头及层级定义。你必须基于这些输入构建最终的 JSON 树，严格遵循以下规则：

1.  **语义层级键**：对于每个 `hierarchy_key`，在最终 JSON 中的键必须采用格式 **`[表头名称] - [单元格值]`**。
    你必须使用“ - ”（空格、连字符、空格）作为分隔符。
    例如：若表头为“Grade”，单元格值为“1”，则 JSON 键应为 `"Grade - 1"`。
    这样可以确保键的语义不会丢失。
2.  **严格保留叶节点名称**：最终 JSON 中的 `value_leaves` 键必须与规范化表头完全一致，不得更改或摘要化。
3.  **结构生成规则**：
    - 逐行遍历数据（跳过表头行）。
    - 使用规则 #1 中的语义层级键，创建或进入对应的嵌套层级结构。
    - 在最深层创建一个用于存储数值的对象。
    - 如果定义了 `semantic_groups`，则使用来自原始表头的组名作为额外的嵌套层。
    - 在最终对象中填入来自 `value_leaves` 列的键值对。
4.  **禁止遗漏数据**：不得遗漏输入表格中的任何数据单元格内容，所有数据都必须被写入生成的树结构中。
特别注意：
- 如果 hierarchy_keys 只有1个元素，则只创建一层嵌套
- 该层之下的所有数据应平铺在同一个对象中，不要继续嵌套
[输入表格]:
{TABLE_AS_JSON_STRING}

[规范化表头]:
{NORMALIZED_HEADERS_FROM_STEP_1}

[层级定义]:
{HIERARCHY_DEFINITION_FROM_STEP_2}

你的输出必须是一个单一、有效的 JSON 对象，完整表示整个表格的树结构。
确保所有数据类型（数字、字符串）均被正确保留。
不要输出任何其他文本或解释。

[最终 JSON 树]:
"""
# -------------------------------------- 提示工程分步转化增强版 ----------------------------------------------
HEADER_ANALYSIS_PROMPT_ENHANCED = """
你是一名专门解析复杂与非规则表格结构的资深数据分析专家。

⚠️ **重要格式说明**：
输入表格使用了特殊的“单元格位置标注”格式，用以明确单元格的对齐与合并信息。  
每个单元格以位置标识开头，例如 `A1`、`B2` 或 `A1:C1`。  
- 示例：`A1:C1 招标说明` 表示内容 “招标说明” 跨越了第 1 行的 A 到 C 列（即合并单元格）。
- 你必须利用这些位置信息，正确识别并对齐多行表头。
- 大多数合并单元格通常是表头。
你的任务是分析表格的表头行，并生成每列对应的标准化表头。

请严格遵守以下规则：

1. **严格保留原文（Strict wording preservation）**：  
   必须保留表头中的原始文字，不得改写或摘要。

2. **层级组合规则（Hierarchical combination）**：  
   如果表头跨越多行（例如 A1:C1, A2:C2, A3:C3），  
   则按以下格式组合：`[下层表头] - [上层表头]`。

3. **精确列匹配（Exact column match）**：  
   输出数组的长度必须与数据列数量完全一致。

输入表格以 Markdown 样式提供，并带有单元格位置标识（例如 `A1`, `B2`, `A1:C1`）。  
请将合并单元格（如 `A1:C1`）视为同时适用于所有包含的列。

[输入表格]:
{TABLE_AS_JSON_STRING}

你的输出必须是一个单一、有效的 JSON 字符串数组，代表最终的标准化表头。

[标准化表头]:
"""

HIERARCHY_VALUE_IDENTIFICATION_PROMPT_ENHANCED = """
你是一名擅长分析表格逻辑结构的数据架构专家。

**重要：特殊表格格式说明**
输入表格采用特殊的 Markdown 格式，每个单元格都带有位置标识符（例如 "A1"、"B2:B4"）。  
在分析表格结构时，请关注位置标识符后的实际内容，而不是标识符本身。

你将获得一个表格及其标准化表头。你的任务是识别哪些列属于 “层次键（Hierarchy Keys）”，哪些列属于 “值叶节点（Value Leaves）”。

定义如下：
- **层次键（Hierarchy Keys）**：用于分组和建立嵌套层级的列。其值通常在多个行块中重复出现。
- **值叶节点（Value Leaves）**：与某个层次路径对应的最终数据列。
- **语义分组（Semantic Groups，可选）**：如果值叶节点能根据上层表头逻辑上归属于某个公共主题，请定义这些分组。  
  **注意：组名必须直接来源于原始表格表头，不能创造新的组名。**  
  若不存在此类分组，请保持为空。

[输入表格]:
{TABLE_AS_JSON_STRING}

[标准化表头]:
{NORMALIZED_HEADERS_FROM_STEP_1}

你的输出必须是一个单一、有效的 JSON 对象，结构如下（请严格使用原始表头名称）：

{{
  "hierarchy_keys": ["header1", "header2", ...],
  "value_leaves": ["header3", "header4", ...],
  "semantic_groups": {{
    "原始分组名称1": ["header_a", "header_b"]
  }}
}}

不要提供任何解释性文字。

[层次定义]:
"""

FINAL_JSON_TREE_CONSTRUCTION_ENHANCED = """
你是一名高水平的数据转换引擎，能够将表格数据转换为嵌套的 JSON 树结构，并完整保留语义信息。

**重要：特殊表格格式说明**
输入表格采用一种特殊的 Markdown 格式，每个单元格都带有位置标识符：
- 单个单元格： "A1"、"B2"、"C3"
- 合并单元格： "A1:C1"、"A2:A4"

在处理过程中，请提取实际内容（即位置标识符后的文本）用于树结构的语义理解。

**优化：基于位置的输出**
为减少 token 消耗，最终输出中请仅使用单元格的**位置标识符**（而非实际内容）作为值引用。  
即在树结构中引用数据所在的位置，而不是重复存储数据内容。

例如，不要输出：
{{
  "年级 - 1": {{
    "班级 - A": {{
      "学生总数": 30
    }}
  }}
}}

而应输出：
{{
  "年级 - 1": {{
    "班级 - A": {{
      "学生总数": "C5"
    }}
  }}
}}

其中 "C5" 是包含数值 30 的单元格位置标识符。

你将获得原始表格、其标准化表头，以及层次定义。你需要根据这些输入生成最终的 JSON 树，遵循以下规则：

1. **语义层次键（Semantic Hierarchy Keys）**：
   对于每个 `hierarchy_key`，最终 JSON 中的键必须格式化为 **`[表头名称] - [单元格值]`**。
   必须使用 " - "（即空格-连字符-空格）连接，例如：
   若表头为“年级”，单元格值为“1”，则键应为 `"年级 - 1"`。
   这样可以确保语义不会丢失。

2. **叶节点键名严格保持（Strict Name Preservation for Leaves）**：
   对于 `value_leaves` 中的键名，必须与标准化表头字符串完全一致，不能修改、缩写或翻译。

3. **值使用位置引用（Position References for Values）**：
   在最终的 JSON 树中，所有值都必须为单元格位置标识符（如 "A4"、"B12"、"C5:C7"），
   而非实际单元格内容。  
   这将显著减少 token 消耗。

4. **结构生成规则（Structure Generation）**：
   - 遍历数据行（跳过表头行）。
   - 使用规则 #1 生成的语义层次键来构建或导航嵌套的 JSON 层级。
   - 在最深层级创建包含值对象的字典。
   - 若定义了 `semantic_groups`，则使用组名（必须来源于原始表头）作为额外一层嵌套。
   - 在最终对象中填充键值对：键来自 `value_leaves`，值为单元格位置标识符。

5. **禁止数据遗漏（No Data Omission）**：
   不能遗漏输入表格中的任何数据单元格位置。  
   所有数据单元格的位置标识符都必须出现在生成的树中。

[输入表格]:
{TABLE_AS_JSON_STRING}

[标准化表头]:
{NORMALIZED_HEADERS_FROM_STEP_1}

[层次定义]:
{HIERARCHY_DEFINITION_FROM_STEP_2}

你的输出必须是一个单一、有效的 JSON 对象，完整表示整个表格的树结构（基于位置引用）。  
不要输出任何解释性文字或附加信息。

[最终 JSON 树]:
"""

# -------------------------------------- 提示工程分步转化增强版 ----------------------------------------------
# ------------------------------------- 输出结构再进行脚本转化 -----------------------------------------------
GET_Hierarchy_Prompt = """
You are a highly skilled table analysis expert. Your task is to analyze a given table, formatted as a list of lists, and extract its hierarchical structure.
Your goal is to generate two separate JSON objects: one representing the row hierarchy and one for the column hierarchy.Output Structure Rules:
1. In each JSON object, the keys represent parent headers.
2. The values are lists of strings, where each string is a direct child header of the corresponding key.
3. If a header has no sub-headers (i.e., it is a leaf node), it should be a key with an empty list [] as its value.
4. The output should only reflect the parent-child relationships of the headers, not the data cells.
## Demonstration:
   # Table: [
    ["", "Financial Performance", "", "Operational Metrics", ""],
    ["", "Revenue ($M)", "Profit ($M)", "Active Users (k)", "Uptime (%)"],
    ["Q1 2024", 150, 40, 1200, 99.9],
    ["Q2 2024", 175, 45, 1250, 99.8]
]
   # Row Hierarchy Output:
   ```json
    {{
        "Q1 2024": [],
        "Q2 2024": []
    }}
    ```
   # Column Hierarchy Output:
   ```json
    {{
        "Financial Performance": [
            "Revenue ($M)",
            "Profit ($M)"
        ],
        "Operational Metrics": [
            "Active Users (k)",
            "Uptime (%)"
        ]
    }}
    ```
Now, please process the following table and generate its row and column hierarchy without explanation.
## Table: {table}
"""

GET_Hierarchy_Prompt_oai = """
You are a highly skilled table analysis expert. Your task is to analyze a given table, formatted as a list of lists, and extract its hierarchical structure.
Your goal is to generate two separate JSON objects: one representing the row hierarchy and one for the column hierarchy.Output Structure Rules:
1. In each JSON object, the keys represent parent headers.
2. The values are lists of strings, where each string is a direct child header of the corresponding key.
3. If a header has no sub-headers (i.e., it is a leaf node), it should be a key with an empty list [] as its value.
4. The output should only reflect the parent-child relationships of the headers, not the data cells.
5. Add the "row" or "col" before the json block.
## Demonstration:
   User : # Table: [
    ["", "Financial Performance", "", "Operational Metrics", ""],
    ["", "Revenue ($M)", "Profit ($M)", "Active Users (k)", "Uptime (%)"],
    ["Q1 2024", 150, 40, 1200, 99.9],
    ["Q2 2024", 175, 45, 1250, 99.8]
]
   Assistant: # Row Hierarchy Output:
   ```json
    {{
        "Q1 2024": [],
        "Q2 2024": []
    }}
    ```
   # Column Hierarchy Output:
   ```json
    {{
        "Financial Performance": [
            "Revenue ($M)",
            "Profit ($M)"
        ],
        "Operational Metrics": [
            "Active Users (k)",
            "Uptime (%)"
        ]
    }}
    ```
Now, please process the following table and generate its row and column hierarchy without explanation.
## Table: {table}
"""
# -------------------------------------- 表格+文本 to 三元组图谱 --------------------------------------------------

GET_KEY_ENTITY_PROMPT = """
You are an expert in Natural Language Understanding (NLU). Your task is to extract the key entities from the user's question. Key entities are the specific concepts, items, or categories that are the primary focus of the question.

[USER QUESTION]:
{USER_QUESTION}

Your output MUST be a single, valid JSON object containing a list of strings. Do not provide any explanations.

{{
  "entities": ["entity1", "entity2", ...]
}}
"""

RELEVANT_TEXT_EXTRACTION_PROMPT = """
You are an information retrieval expert. Your task is to extract all sentences from the provided paragraph that are relevant to the given list of key entities.

Follow these rules:
1.  Read through the `PARAGRAPH_TEXT`.
2.  For each sentence, check if it contains or discusses any of the `KEY_ENTITIES`.
3.  Return only the sentences that are directly relevant.

[PARAGRAPH_TEXT]:
{PARAGRAPH_TEXT}

[KEY_ENTITIES]:
{ENTITIES_FROM_STEP_1}

Your output MUST be a single, valid JSON object containing a list of the extracted sentences. If no relevant sentences are found, return an empty list. Do not provide explanations.

{{
  "snippets": [
    "Relevant sentence one...",
    "Relevant sentence two..."
  ]
}}
"""

FUSED_SEMANTIC_TRIPLE_EXTRACTION_PROMPT = """
You are a senior knowledge graph engineer. Your task is to synthesize information from MULTIPLE sources to build a comprehensive set of semantic triples about a set of key entities.

You will be given four sources of information:
1.  `STRUCTURED_JSON_DATA`: A pre-processed, structured version of the table. Use this as your PRIMARY source for hierarchical relationships and numerical facts.
2.  `ORIGINAL_TABLE`: The raw table data. Use this as a REFERENCE to verify structure, check for details missed in the JSON, and understand the original context.
3.  `RELEVANT_TEXT_SNIPPETS`: Sentences extracted from a descriptive paragraph. Use this to find additional relationships, definitions, or context that are NOT in the table.
4.  `KEY_ENTITIES`: The focus of your investigation.

Your instructions are:
1.  **Prioritize Sources**: Trust the facts and numbers in `STRUCTURED_JSON_DATA` first. Use `ORIGINAL_TABLE` to resolve any ambiguities. Use `RELEVANT_TEXT_SNIPPETS` to add new, supplementary facts. If there is a direct conflict between the text and the table, the table data takes precedence.
2.  **Generate Triples**: Create triples in the format `[Subject, Predicate, Object]` for all facts you can find about the `KEY_ENTITIES`.
    - Derive relationships from the JSON's nested structure (e.g., `["Grade 2", "has subgroup", "Female"]`).
    - Derive relationships from the text (e.g., `["Grade 2", "is located in", "East Wing"]` if the text mentions it).
    - Use natural, human-readable predicates.
3.  **Structure the Output**: Organize the final list of triples under their primary subject entity to form a "semantic tree".

[STRUCTURED_JSON_DATA]:
{JSON_TREE}

[ORIGINAL_TABLE_AS_JSON]:
{ORIGINAL_TABLE_AS_JSON}

[RELEVANT_TEXT_SNIPPETS]:
{SNIPPETS_FROM_STEP_2}

[KEY_ENTITIES]:
{ENTITIES_FROM_STEP_1}

Your output MUST be a single, valid JSON object representing the semantic tree. Provide no explanations.

[SEMANTIC TREE]:
"""

