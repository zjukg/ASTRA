
import re
import json
from typing import List, Dict, Any, Optional, Tuple
import openpyxl
class TableToTreeConverter:
    """通用表格转层次化字典转换器"""
    
    def __init__(self):
        pass
    
    @staticmethod
    def is_likely_numeric(s):
        """判断一个字符串是否可能是数字或财务符号"""
        if not isinstance(s, str):
            return isinstance(s, (int, float))
        s = s.strip().replace(',', '').replace('$', '').replace('￥', '').replace('%', '')
        return bool(re.fullmatch(r'[\d\.]+|\([\d\.]+\)|-', s)) or s == ''
    
    @staticmethod
    def clean_value(value):
        """清理和转换数值"""
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            value = value.strip()
            if value == '' or value == '-':
                return value
            # 处理括号表示的负数
            if value.startswith('(') and value.endswith(')'):
                try:
                    return value  # 保持原格式
                except:
                    return value
            try:
                # 尝试转换为整数
                return int(value.replace(',', ''))
            except (ValueError, TypeError):
                try:
                    # 尝试转换为浮点数
                    return float(value.replace(',', ''))
                except (ValueError, TypeError):
                    return value
        return value
    
    def get_leaf_columns(self, col_h: Dict[str, List[str]]) -> List[str]:
        """从列层次结构中提取叶子节点列标题"""
        leaf_columns = []
        
        # 获取所有父节点和子节点
        all_children = set(child for children in col_h.values() for child in children)
        
        # 按顺序遍历并提取叶子节点
        for parent, children in col_h.items():
            if not children:  # 父节点没有子节点，它本身就是叶子
                if parent not in leaf_columns:
                    leaf_columns.append(parent)
            else:  # 有子节点，子节点就是叶子
                for child in children:
                    if child not in leaf_columns:
                        leaf_columns.append(child)
        
        return leaf_columns
    
    def find_data_start_column(self, table: List[List], column_headers: List[str]) -> int:
        """找到数据开始的列索引"""
        for row in table:
            try:
                return row.index(column_headers[0])
            except (ValueError, IndexError):
                continue
        # 默认从第1列开始（索引1）
        return 1
    
    def create_row_lookup(self, table: List[List]) -> Dict[str, List]:
        """创建行标题到行数据的映射"""
        return {str(row[0]).strip(): row for row in table if row and row[0]}
    
    def build_nested_structure(self, row_lookup: Dict[str, List], row_h: Dict[str, List[str]], 
                              column_headers: List[str], data_start_col: int) -> Dict[str, Any]:
        """递归构建嵌套字典结构"""
        
        def build_level(parent_data: Dict, keys_to_process: List[str]):
            for key in keys_to_process:
                # 情况A: key是父节点，有子节点
                if key in row_h and row_h[key]:
                    parent_data[key] = {}
                    build_level(parent_data[key], row_h[key])
                # 情况B: key是叶子节点，对应一行数据
                elif key in row_lookup:
                    data_row = row_lookup[key]
                    # 提取数据值
                    data_values = data_row[data_start_col : data_start_col + len(column_headers)]
                    
                    # 创建列名到值的映射
                    parent_data[key] = {
                        col_name: self.clean_value(data_values[i]) if i < len(data_values) else None
                        for i, col_name in enumerate(column_headers)
                    }
        
        # 找到顶级父节点（不是任何其他节点的子节点）
        all_children = set(child for children in row_h.values() for child in children)
        top_level_keys = [key for key in row_h.keys() if key not in all_children]
        
        result = {}
        build_level(result, top_level_keys)
        return result
    
    def convert_table(self, table: List[List], row_h: Dict[str, List[str]], 
                     col_h: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        将表格转换为层次化字典
        
        Args:
            table: 表格数据 (List[List] 格式)
            row_h: 行层次结构字典
            col_h: 列层次结构字典
            
        Returns:
            层次化的字典结构
        """
        
        # 1. 获取叶子列标题
        column_headers = self.get_leaf_columns(col_h)
        if not column_headers:
            raise ValueError("无法从列层次结构中提取有效的列标题")
        
        # 2. 找到数据开始的列索引
        data_start_col = self.find_data_start_column(table, column_headers)
        
        # 3. 创建行查找映射
        row_lookup = self.create_row_lookup(table)
        
        # 4. 构建嵌套结构
        result = self.build_nested_structure(row_lookup, row_h, column_headers, data_start_col)
        
        return result
class mytableconverter:
    """通用表格转层次化字典转换器 (修复版)"""
    def __init__(self):
        pass

    @staticmethod
    def is_likely_numeric(s):
        """判断一个字符串是否可能是数字或财务符号"""
        if not isinstance(s, str):
            return isinstance(s, (int, float))
        s = s.strip().replace(',', '').replace('$', '').replace('￥', '').replace('%', '')
        return bool(re.fullmatch(r'[\d\.]+|\([\d\.]+\)|-', s)) or s == ''

    @staticmethod
    def clean_value(value):
        """清理和转换数值"""
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            value = value.strip()
            if value == '' or value == '–': # 在第二个例子中是 '–' 而不是 '-'
                return value
            # 处理括号表示的负数
            if value.startswith('(') and value.endswith(')'):
                return value  # 保持原格式
            try:
                # 尝试转换为整数
                return int(value.replace(',', ''))
            except (ValueError, TypeError):
                try:
                    # 尝试转换为浮点数
                    return float(value.replace(',', ''))
                except (ValueError, TypeError):
                    return value
        return value

    def _get_full_column_headers(self, col_h: Dict[str, List[str]]) -> List[Tuple[str, ...]]:
        """
        从列层次结构中提取每个叶子节点的完整路径。
        例如：{'2019': ['$', '%']} -> [('2019', '$'), ('2019', '%')]
        """
        full_headers = []
        # 假设 col_h 的键（父节点）是有序的
        for parent, children in col_h.items():
            if children:
                for child in children:
                    full_headers.append((parent, child))
            else:
                # 如果父节点没有子节点，它本身就是完整路径
                full_headers.append((parent,))
        return full_headers

    def find_data_start_column(self, table: List[List], column_headers: List[str]) -> int:
        """找到数据开始的列索引"""
        # 使用叶子节点列来定位
        leaf_columns = [h[-1] for h in column_headers]
        if not leaf_columns:
            return 1 # 默认值

        for row in table:
            try:
                # 尝试找到第一个叶子节点列标题的位置
                return row.index(leaf_columns[0])
            except (ValueError, IndexError):
                continue
        # 默认从第1列开始（索引1）
        return 1

    def create_row_lookup(self, table: List[List], header_rows_count: int) -> Dict[str, List]:
        """创建行标题到行数据的映射，跳过表头行"""
        # 一个简单的启发式方法：表头之后是数据行
        data_rows = table[header_rows_count:]
        return {str(row[0]).strip(): row for row in data_rows if row and str(row[0]).strip()}

    def build_nested_structure(self, row_lookup: Dict[str, List], row_h: Dict[str, List[str]],
                               column_headers: List[Tuple[str, ...]], data_start_col: int) -> Dict[str, Any]:
        """递归构建嵌套字典结构"""

        def build_level(parent_data: Dict, keys_to_process: List[str]):
            for key in keys_to_process:
                # 情况A: key是父节点，有子节点
                if key in row_h and row_h.get(key):
                    parent_data[key] = {}
                    build_level(parent_data[key], row_h[key])
                # 情况B: key是叶子节点，对应一行数据
                elif key in row_lookup:
                    data_row = row_lookup[key]
                    data_values = data_row[data_start_col:]
                    
                    # 为这一行创建一个嵌套字典
                    row_data_nested = {}
                    
                    # 遍历每个列的完整路径和对应的数据值
                    for i, header_path in enumerate(column_headers):
                        if i >= len(data_values):
                            continue
                        
                        value = self.clean_value(data_values[i])
                        
                        # 使用一个指针来构建嵌套字典
                        current_level = row_data_nested
                        # 遍历路径中的所有部分，除了最后一个
                        for part in header_path[:-1]:
                            # 如果键不存在，则创建一个新字典
                            current_level = current_level.setdefault(part, {})
                        
                        # 在最深层级设置值
                        current_level[header_path[-1]] = value
                        
                    parent_data[key] = row_data_nested

        # 找到顶级父节点（不是任何其他节点的子节点）
        all_children = set(child for children in row_h.values() for child in children)
        top_level_keys = [key for key in row_h.keys() if key not in all_children]

        result = {}
        build_level(result, top_level_keys)
        return result

    def convert(self, original_table: List[List[str]], row_h: Dict[str, List[str]], col_h: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        执行转换的主方法。
        """
        # 1. 获取完整的、带层级的列标题
        full_column_headers = self._get_full_column_headers(col_h)
        
        # 2. 找到数据列的起始索引
        # 简单的启发式：计算可能的表头行数。这里假设表头是直到第一个数据行标题出现前的所有行。
        first_data_row_key = list(row_h.keys())[0]
        header_rows_count = 0
        for i, row in enumerate(original_table):
            if row and str(row[0]).strip() == first_data_row_key:
                header_rows_count = i
                break
        
        leaf_headers_for_search = [h[-1] for h in full_column_headers]
        data_start_col = self.find_data_start_column(original_table[:header_rows_count+1], leaf_headers_for_search)

        # 3. 创建行标题到数据的查找表
        row_lookup = self.create_row_lookup(original_table, header_rows_count)

        # 4. 构建最终的嵌套结构
        tree_table = self.build_nested_structure(row_lookup, row_h, full_column_headers, data_start_col)
        
        return tree_table
def extract_hierarchies(llm_output: str):
    """
    从LLM输出中提取行和列层次结构
    
    Args:
        llm_output (str): LLM的完整输出文本
        
    Returns:
        tuple: (row_hierarchy_json, column_hierarchy_json)
    """
    row_hierarchy = None
    column_hierarchy = None
    
    # 找到所有 ```json 代码块
    json_pattern = r'```json\s*(.*?)```'
    json_matches = re.findall(json_pattern, llm_output, re.DOTALL | re.IGNORECASE)
    
    # 找到所有 ```json 的位置
    json_positions = []
    for match in re.finditer(r'```json', llm_output, re.IGNORECASE):
        json_positions.append(match.start())
    
    # 遍历每个json块
    for i, json_text in enumerate(json_matches):
        try:
            # 解析JSON
            parsed_json = json.loads(json_text.strip())
            
            # 获取这个json块之前的文本（最多往前看500个字符）
            if i < len(json_positions):
                start_pos = max(0, json_positions[i] - 500)
                preceding_text = llm_output[start_pos:json_positions[i]].lower()
                
                # 检查是否是行层次结构
                if re.search(r'row', preceding_text) and row_hierarchy is None:
                    row_hierarchy = parsed_json
                    print(f"✅ 找到行层次结构 (第{i+1}个JSON块)")
                    
                # 检查是否是列层次结构  
                elif re.search(r'col', preceding_text) and column_hierarchy is None:
                    column_hierarchy = parsed_json
                    print(f"✅ 找到列层次结构 (第{i+1}个JSON块)")
                    
        except json.JSONDecodeError as e:
            print(f"⚠️ 第{i+1}个JSON块解析失败: {e}")
            continue
    
    return row_hierarchy, column_hierarchy

def normalize_tree_none_values(tree_table):
    """
    递归处理树形表格，将所有None值转换为字符串"None"
    
    Args:
        tree_table: 树形表格结构（可以是dict, list或其他类型）
        
    Returns:
        处理后的树形表格，所有None值都被替换为字符串"None"
    """
    if tree_table is None:
        return "None"
    
    if isinstance(tree_table, dict):
        # 递归处理字典的每个键值对
        normalized_dict = {}
        for key, value in tree_table.items():
            normalized_dict[key] = normalize_tree_none_values(value)
        return normalized_dict
    
    elif isinstance(tree_table, list):
        # 递归处理列表的每个元素
        return [normalize_tree_none_values(item) for item in tree_table]
    
    else:
        # 基本类型直接返回
        return tree_table

def print_tree(d, indent=0):
    """
    递归打印嵌套字典为树状结构
    :param d: dict 或基本类型
    :param indent: 缩进层级
    """
    for key, value in d.items():
        print('│   ' * indent + '├─ ' + str(key))
        if isinstance(value, dict):
            print_tree(value, indent + 1)
        else:
            print('│   ' * (indent + 1) + '├─ ' + str(value))
from model_clients import ModelClient, OpenaimodelClient
from prompt import GET_Hierarchy_Prompt_oai
# ------- 方案1 通过LLM提取树结构之后进行脚本提取转化为树 -------------
def table2tree_rule(table, model_name, temperature, model_type="oai"):
    """
    Input :
        table : 原始表格
        model_name : 模型名称
        temperature : 温度
        model_type : 模型类型 ("oai" 或 "opensource")
    Output :
        Tree_table : 树化表格
    """
    model = ModelClient()
    oaimodel = OpenaimodelClient(model = model_name)
    
    if model_type == "oai":
        response = oaimodel.generate(GET_Hierarchy_Prompt_oai.format(table=table), temperature=temperature)
        full_llm_output = response
    else:
        response = model.test_generate_stream_advanced(GET_Hierarchy_Prompt_oai.format(table=table), temperature=temperature)
        full_llm_output = "".join(list(response))
    
    print(full_llm_output)
    row_h, col_h = extract_hierarchies(full_llm_output)
    print(f"Row Hierarchy: {row_h}")
    print(f"Column Hierarchy: {col_h}")
    
    Tableconverter = mytableconverter()
    Tree_table = Tableconverter.convert(table, row_h, col_h)
    print(f"✅ 成功生成树形表格，根节点数量: {len(Tree_table)}")
    
    return Tree_table

# ------- 方案2 通过LLM进行三步操作提取树 -------------
def excel_to_markdown_with_cell_ref(sheet):
    """
    将Excel工作表转换为包含单元格位置的Markdown表格
    
    Args:
        sheet: openpyxl工作表对象
    
    Returns:
        str: Markdown格式的表格字符串
    """
    # 获取工作表的基本信息
    max_row = sheet.max_row
    max_col = sheet.max_column
    
    # 获取所有合并单元格信息
    merged_cells = {}
    for merged_range in sheet.merged_cells.ranges:
        # 将合并区域转换为字符串表示，如 "A1:B2"
        merged_ref = f"{get_column_letter(merged_range.min_col)}{merged_range.min_row}:{get_column_letter(merged_range.max_col)}{merged_range.max_row}"
        # 只记录左上角单元格的值
        top_left_cell = sheet.cell(merged_range.min_row, merged_range.min_col)
        merged_cells[merged_ref] = top_left_cell.value
    
    # 构建表格数据
    table_data = []
    for row in range(1, max_row + 1):
        row_data = []
        for col in range(1, max_col + 1):
            cell = sheet.cell(row, col)
            cell_ref = f"{get_column_letter(col)}{row}"
            
            # 检查当前单元格是否在某个合并区域内
            is_in_merged = False
            cell_value = None
            
            for merged_ref, value in merged_cells.items():
                start_ref, end_ref = merged_ref.split(':')
                start_col_str = ''.join(filter(str.isalpha, start_ref))
                start_row = int(''.join(filter(str.isdigit, start_ref)))
                end_col_str = ''.join(filter(str.isalpha, end_ref))
                end_row = int(''.join(filter(str.isdigit, end_ref)))
                
                start_col = openpyxl.utils.column_index_from_string(start_col_str)
                end_col = openpyxl.utils.column_index_from_string(end_col_str)
                
                if (start_row <= row <= end_row and start_col <= col <= end_col):
                    is_in_merged = True
                    # 如果是合并区域的左上角单元格
                    if row == start_row and col == start_col:
                        cell_value = f"{merged_ref} {value if value is not None else ''}"
                    break
            
            if not is_in_merged:
                cell_value = f"{cell_ref} {cell.value if cell.value is not None else ''}"
            
            row_data.append(cell_value if cell_value is not None else f"{cell_ref} ")
        
        table_data.append(row_data)
    
    # 生成Markdown表格
    markdown_lines = []
    
    # 表头行
    header_row = "| " + " | ".join(str(table_data[0][col]) for col in range(max_col)) + " |"
    markdown_lines.append(header_row)
    
    # 分隔线行
    separator_row = "| " + " | ".join(["---"] * max_col) + " |"
    markdown_lines.append(separator_row)
    
    # 数据行
    for row in range(1, len(table_data)):
        data_row = "| " + " | ".join(str(table_data[row][col]) for col in range(max_col)) + " |"
        markdown_lines.append(data_row)
    
    return "\n".join(markdown_lines)


def get_cell_position(row_idx: int, col_idx: int) -> str:
    """
    将 0-based 的行列索引转换为 Excel 单元格位置标识符 (例如: 0,0 -> A1)
    
    Args:
        row_idx: 行索引 (0-based)
        col_idx: 列索引 (0-based)
    
    Returns:
        Excel 格式的单元格位置 (如 "A1", "B2", "AA10")
    """
    col_letter = ''
    c = col_idx
    while c >= 0:
        col_letter = chr(c % 26 + ord('A')) + col_letter
        c = c // 26 - 1
    
    return f"{col_letter}{row_idx + 1}"


def format_table_with_positions(table: List[List]) -> str:
    """
    将表格格式化为带单元格位置标识的字符串，供 LLM 理解表格结构
    
    Args:
        table: 原始表格 (List[List] 格式)
    
    Returns:
        格式化的字符串，每个单元格带有位置标识
    
    Example output:
        | A1:      | B1: 2023 | C1: 2024 |
        | A2: 收入 | B2: 100  | C2: 200  |
    """
    if not table or not table[0]:
        return ""
    
    lines = []
    max_col = max(len(row) for row in table)
    
    for row_idx, row in enumerate(table):
        row_cells = []
        for col_idx in range(max_col):
            pos = get_cell_position(row_idx, col_idx)
            if col_idx < len(row):
                value = row[col_idx]
                if value is None:
                    value_str = ""
                else:
                    value_str = str(value)
                if len(value_str) > 50:
                    value_str = value_str[:47] + "..."
            else:
                value_str = ""
            row_cells.append(f"{pos}: {value_str}")
        lines.append("| " + " | ".join(row_cells) + " |")
    
    return "\n".join(lines)


from prompt import HEADER_ANALYSIS_PROMPT, HIERARCHY_VALUE_IDENTIFICATION_PROMPT, FINAL_JSON_TREE_CONSTRUCTION
from prompt import HEADER_ANALYSIS_PROMPT_ENHANCED, HIERARCHY_VALUE_IDENTIFICATION_PROMPT_ENHANCED, FINAL_JSON_TREE_CONSTRUCTION_ENHANCED
from prompt import CODE_BASED_TREE_CONSTRUCTION_PROMPT, CODE_BASED_TREE_CONSTRUCTION_RETRY_PROMPT

class llm_based_converter:
    def __init__(self, model_type, model_name, api_key="", base_url=""):
        self.model = ModelClient()
        self.oaimodel = OpenaimodelClient(model=model_name, api_key=api_key, base_url=base_url)
        self.model_type = model_type
        self.if_print_prompt = True

    def extract_response(self, response):
        return response.split("```json")[1].split("```")[0]

    def extract_after_think(self, response):
        """提取</think>标签之后的内容"""
        if "</think>" in response:
            think_end = response.find("</think>")
            if think_end != -1:
                content_after_think = response[think_end + len("</think>"):].strip()
                return content_after_think
        return response.strip()

    def header_analysis_norm_enhance(self, table, temperature):
        if self.if_print_prompt:
            print("**Header Analysis Enhance PROMPT**")
            print(HEADER_ANALYSIS_PROMPT_ENHANCED.format(TABLE_AS_JSON_STRING=table))
        if self.model_type == "oai":
            response = self.oaimodel.generate(HEADER_ANALYSIS_PROMPT_ENHANCED.format(TABLE_AS_JSON_STRING=table), temperature=temperature)
            full_llm_output = response
            print("---Header Analysis Enhance---")
            print(full_llm_output)
        else:
            response = self.model.test_generate_stream(HEADER_ANALYSIS_PROMPT_ENHANCED.format(TABLE_AS_JSON_STRING=table), temperature=temperature)
            full_llm_output = "".join(list(response)) 
            full_llm_output = self.extract_after_think(full_llm_output)
        return full_llm_output

    def hierarchy_definition_enhance(self, table, Normalized_headers, temperature):
        if self.if_print_prompt:
            print("**Hierarchy Definition Enhance PROMPT**")
            print(HIERARCHY_VALUE_IDENTIFICATION_PROMPT_ENHANCED.format(TABLE_AS_JSON_STRING=table, NORMALIZED_HEADERS_FROM_STEP_1=Normalized_headers))
        if self.model_type == "oai":
            response = self.oaimodel.generate(HIERARCHY_VALUE_IDENTIFICATION_PROMPT_ENHANCED.format(TABLE_AS_JSON_STRING=table, NORMALIZED_HEADERS_FROM_STEP_1=Normalized_headers), temperature=temperature)
            full_llm_output = response
            print("---Hierarchy Definition Enhance---")
            print(full_llm_output)
        else:
            response = self.model.test_generate_stream(HIERARCHY_VALUE_IDENTIFICATION_PROMPT_ENHANCED.format(TABLE_AS_JSON_STRING=table, NORMALIZED_HEADERS_FROM_STEP_1=Normalized_headers), temperature=temperature)
            full_llm_output = "".join(list(response)) 
            full_llm_output = self.extract_after_think(full_llm_output)
        return full_llm_output

    def final_json_tree_construction_enhance(self, table, Normalized_headers, Hierarchy_definition, temperature):
        if self.if_print_prompt:
            print("**Final JSON Tree Construction Enhance PROMPT**")
            print(FINAL_JSON_TREE_CONSTRUCTION_ENHANCED.format(TABLE_AS_JSON_STRING=table, NORMALIZED_HEADERS_FROM_STEP_1=Normalized_headers, HIERARCHY_DEFINITION_FROM_STEP_2=Hierarchy_definition))
        if self.model_type == "oai":
            response = self.oaimodel.generate(FINAL_JSON_TREE_CONSTRUCTION_ENHANCED.format(TABLE_AS_JSON_STRING=table, NORMALIZED_HEADERS_FROM_STEP_1=Normalized_headers, HIERARCHY_DEFINITION_FROM_STEP_2=Hierarchy_definition), temperature=temperature)
            full_llm_output = response
            print("---Final JSON Tree Construction Enhance---")
            print(full_llm_output)
        else:
            response = self.model.test_generate_stream(FINAL_JSON_TREE_CONSTRUCTION_ENHANCED.format(TABLE_AS_JSON_STRING=table, NORMALIZED_HEADERS_FROM_STEP_1=Normalized_headers, HIERARCHY_DEFINITION_FROM_STEP_2=Hierarchy_definition), temperature=temperature)
            full_llm_output = "".join(list(response)) 
            full_llm_output = self.extract_after_think(full_llm_output)
        return full_llm_output

    def header_analysis_norm(self, table, temperature):
        if self.if_print_prompt:
            print("**Header Analysis Normal PROMPT**")
            print(HEADER_ANALYSIS_PROMPT.format(TABLE_AS_JSON_STRING=table))
        if self.model_type == "oai":
            response = self.oaimodel.generate(HEADER_ANALYSIS_PROMPT.format(TABLE_AS_JSON_STRING=table), temperature=temperature)
            full_llm_output = response
            print("---Header Analysis Normal---")
            print(full_llm_output)
        else:
            response = self.model.test_generate_stream(HEADER_ANALYSIS_PROMPT.format(TABLE_AS_JSON_STRING=table), temperature=temperature)
            full_llm_output = "".join(list(response)) 
            full_llm_output = self.extract_after_think(full_llm_output)
        return full_llm_output
    
    def hierarchy_definition(self, table, Normalized_headers, temperature):
        if self.if_print_prompt:
            print("**Hierarchy Definition PROMPT**")
            print(HIERARCHY_VALUE_IDENTIFICATION_PROMPT.format(TABLE_AS_JSON_STRING=table, NORMALIZED_HEADERS_FROM_STEP_1=Normalized_headers))
        if self.model_type == "oai":
            response = self.oaimodel.generate(HIERARCHY_VALUE_IDENTIFICATION_PROMPT.format(TABLE_AS_JSON_STRING=table, NORMALIZED_HEADERS_FROM_STEP_1=Normalized_headers), temperature=temperature)
            full_llm_output = response
            print("---Hierarchy Definition---")
            print(full_llm_output)
        else:
            response = self.model.test_generate_stream(HIERARCHY_VALUE_IDENTIFICATION_PROMPT.format(TABLE_AS_JSON_STRING=table, NORMALIZED_HEADERS_FROM_STEP_1=Normalized_headers), temperature=temperature)
            full_llm_output = "".join(list(response)) 
            full_llm_output = self.extract_after_think(full_llm_output)
        return full_llm_output
    
    def final_json_tree_construction(self, table, Normalized_headers, Hierarchy_definition, temperature):
        if self.if_print_prompt:
            print("**Final JSON Tree Construction PROMPT**")
            print(FINAL_JSON_TREE_CONSTRUCTION.format(TABLE_AS_JSON_STRING=table, NORMALIZED_HEADERS_FROM_STEP_1=Normalized_headers, HIERARCHY_DEFINITION_FROM_STEP_2=Hierarchy_definition))
        if self.model_type == "oai":
            response = self.oaimodel.generate(FINAL_JSON_TREE_CONSTRUCTION.format(TABLE_AS_JSON_STRING=table, NORMALIZED_HEADERS_FROM_STEP_1=Normalized_headers, HIERARCHY_DEFINITION_FROM_STEP_2=Hierarchy_definition), temperature=temperature)
            full_llm_output = response
            print("---Final JSON Tree Construction---")
            print(full_llm_output)
        else:
            response = self.model.test_generate_stream(FINAL_JSON_TREE_CONSTRUCTION.format(TABLE_AS_JSON_STRING=table, NORMALIZED_HEADERS_FROM_STEP_1=Normalized_headers, HIERARCHY_DEFINITION_FROM_STEP_2=Hierarchy_definition), temperature=temperature)
            full_llm_output = "".join(list(response)) 
            full_llm_output = self.extract_after_think(full_llm_output)
        return full_llm_output

    def code_based_tree_construction(self, table, Normalized_headers, Hierarchy_definition, temperature, max_attempts=3):
        """
        使用代码生成方式构建树结构（PSS - Programmatic Structure Synthesis，适用于大型表格）
        
        Args:
            table: 原始表格 (List[List])
            Normalized_headers: 规范化表头 (JSON字符串或列表)
            Hierarchy_definition: 层次定义 (JSON字符串或字典)
            temperature: 温度参数
            max_attempts: 最大重试次数
        
        Returns:
            tree_result: 构建完成的树结构
        """
        # 解析 headers 和 hierarchy_def
        if isinstance(Normalized_headers, str):
            try:
                headers_list = json.loads(Normalized_headers)
            except json.JSONDecodeError:
                if "```json" in Normalized_headers:
                    headers_list = json.loads(Normalized_headers.split("```json")[1].split("```")[0].strip())
                else:
                    headers_list = json.loads(Normalized_headers.strip())
        else:
            headers_list = Normalized_headers
        
        if isinstance(Hierarchy_definition, str):
            try:
                hierarchy_def = json.loads(Hierarchy_definition)
            except json.JSONDecodeError:
                if "```json" in Hierarchy_definition:
                    hierarchy_def = json.loads(Hierarchy_definition.split("```json")[1].split("```")[0].strip())
                else:
                    hierarchy_def = json.loads(Hierarchy_definition.strip())
        else:
            hierarchy_def = Hierarchy_definition
        
        # 格式化表格为带位置标识的形式
        table_with_positions = format_table_with_positions(table)
        
        # 准备 prompt 参数
        headers_json = json.dumps(headers_list, ensure_ascii=False, indent=2)
        hierarchy_def_json = json.dumps(hierarchy_def, ensure_ascii=False, indent=2)
        
        error_history = []
        last_code = None
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                # 构建 prompt
                if attempt == 0:
                    prompt = CODE_BASED_TREE_CONSTRUCTION_PROMPT.format(
                        TABLE_WITH_POSITIONS=table_with_positions,
                        HEADERS_JSON=headers_json,
                        HIERARCHY_DEF_JSON=hierarchy_def_json
                    )
                else:
                    prompt = CODE_BASED_TREE_CONSTRUCTION_RETRY_PROMPT.format(
                        TABLE_WITH_POSITIONS=table_with_positions,
                        HEADERS_JSON=headers_json,
                        HIERARCHY_DEF_JSON=hierarchy_def_json,
                        PREVIOUS_CODE=last_code if last_code else "无",
                        ERROR_MESSAGE=last_error if last_error else "无"
                    )
                
                if self.if_print_prompt:
                    print(f"**Code-Based Tree Construction PROMPT (Attempt {attempt + 1})**")
                    print(prompt[:2000] + "..." if len(prompt) > 2000 else prompt)
                
                # 调用 LLM
                if self.model_type == "oai":
                    response = self.oaimodel.generate(prompt, temperature=temperature)
                    full_llm_output = response
                else:
                    response = self.model.test_generate_stream(prompt, temperature=temperature)
                    full_llm_output = "".join(list(response))
                    full_llm_output = self.extract_after_think(full_llm_output)
                
                print(f"---Code-Based Tree Construction Response (Attempt {attempt + 1})---")
                print(full_llm_output)
                
                # 提取代码：优先从 <python_code> 提取，若无则尝试 ```python
                extracted_code = None
                match = re.search(r"<python_code>(.*?)</python_code>", full_llm_output, re.DOTALL | re.IGNORECASE)
                if match:
                    extracted_code = match.group(1).strip()
                else:
                    code_block_match = re.search(r"```python\s*(.*?)```", full_llm_output, re.DOTALL | re.IGNORECASE)
                    if code_block_match:
                        extracted_code = code_block_match.group(1).strip()
                
                if not extracted_code:
                    last_error = "LLM 没有在 <python_code> 标签或 python 代码块中返回有效代码"
                    last_code = full_llm_output
                    error_history.append({"code": last_code, "error": last_error})
                    print(f"❌ Attempt {attempt + 1}: {last_error}")
                    continue
                
                # 移除注释行
                extracted_code = "\n".join([line for line in extracted_code.splitlines() if not line.strip().startswith('#')])
                
                if not extracted_code.strip():
                    last_error = "LLM 返回了空代码"
                    last_code = ""
                    error_history.append({"code": last_code, "error": last_error})
                    print(f"❌ Attempt {attempt + 1}: {last_error}")
                    continue
                
                last_code = extracted_code
                
                # 执行代码
                tree_result = execute_tree_building_code(
                    code=extracted_code,
                    raw_table=table,
                    headers=headers_list,
                    hierarchy_def=hierarchy_def
                )
                
                print(f"✅ Code-Based Tree Construction 成功 (Attempt {attempt + 1})")
                print(f"📊 树结构根节点数量: {len(tree_result) if isinstance(tree_result, dict) else 'N/A'}")
                
                return tree_result
                
            except Exception as e:
                last_error = str(e)
                error_history.append({"code": last_code, "error": last_error})
                print(f"❌ Attempt {attempt + 1} failed: {last_error}")
                
                if attempt == max_attempts - 1:
                    print(f"⚠️ 所有 {max_attempts} 次尝试均失败，返回空树")
                    return {}
        
        return {}

    def parse_json_with_merge(self, json_string):
        """
        解析包含重复key的JSON字符串，自动合并重复key
        """
        def merge_dicts(dict1, dict2):
            """递归合并两个字典"""
            result = dict1.copy()
            for key, value in dict2.items():
                if key in result:
                    if isinstance(result[key], dict) and isinstance(value, dict):
                        result[key] = merge_dicts(result[key], value)
                    # 如果不是字典，保留原值或选择其他策略
                else:
                    result[key] = value
            return result
        
        # 使用object_pairs_hook来处理重复key
        def object_pairs_hook(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    # 如果key已存在，合并值
                    if isinstance(result[key], dict) and isinstance(value, dict):
                        result[key] = merge_dicts(result[key], value)
                    else:
                        # 其他策略：可以选择保留第一个、最后一个，或创建列表
                        pass
                else:
                    result[key] = value
            return result
        
        return json.loads(json_string, object_pairs_hook=object_pairs_hook)

    def parse_json_with_merge_oai(self, oai_output):
        """
        简单处理OpenAI输出的JSON解析函数
        """
        # 提取JSON内容
        if "```json" in oai_output:
            json_content = oai_output.split("```json")[1].split("```")[0].strip()
        elif "```" in oai_output:
            json_content = oai_output.split("```")[1].strip()
        else:
            # 如果没有代码块标记，查找{}之间的内容
            start = oai_output.find('{')
            end = oai_output.rfind('}') + 1
            json_content = oai_output[start:end].strip()
        
        # 处理重复key的hook函数
        def object_pairs_hook(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    if isinstance(result[key], dict) and isinstance(value, dict):
                        # 合并字典
                        result[key].update(value)
                    else:
                        # 保留最后一个值
                        result[key] = value
                else:
                    result[key] = value
            return result
        def _deep_merge_dicts(dict1: dict, dict2: dict) -> dict:
            """
            递归地将 dict2 合并到 dict1 中。
            
            - 如果键只存在于一个字典中，则保留它。
            - 如果键在两个字典中都存在，并且值都是字典，则递归合并这两个子字典。
            - 如果键在两个字典中都存在，但值不是两个字典（例如，字符串、列表或一个字典一个列表），
            则将它们合并到一个列表中（以避免数据丢失）。
            """
            merged = dict1.copy()

            for key, value2 in dict2.items():
                if key in merged:
                    value1 = merged[key]
                    
                    # 检查我们是否可以递归合并
                    if isinstance(value1, dict) and isinstance(value2, dict):
                        merged[key] = _deep_merge_dicts(value1, value2)
                    
                    # 如果不能合并（例如，一个是 dict，另一个是 str，或者都是 str）
                    # 我们必须将它们放入一个列表中以保留所有数据。
                    else:
                        # 如果它还不是列表，请将其转换为列表
                        if not isinstance(value1, list):
                            merged[key] = [value1]
                        
                        # 如果 value2 本身是一个列表，则扩展它，否则附加它
                        if isinstance(value2, list):
                            merged[key].extend(value2)
                        else:
                            merged[key].append(value2)
                else:
                    # 键是全新的，直接添加
                    merged[key] = value2
                    
            return merged

        # ----------------------------------------------------------------------
        # 2. 你的新 object_pairs_hook
        # ----------------------------------------------------------------------
        def recursive_merge_hook(pairs: list) -> dict:
            """
            在 json.loads 期间调用的 Hook，用于执行深度合并。
            """
            result = {}
            for key, value in pairs:
                if key in result:
                    # 发现重复键！
                    # 检查我们是否可以深度合并
                    if isinstance(result[key], dict) and isinstance(value, dict):
                        result[key] = _deep_merge_dicts(result[key], value)
                    else:
                        # 无法深度合并（例如，一个是 dict，另一个是 str）
                        # 回退到列表策略以避免数据丢失
                        if not isinstance(result[key], list):
                            result[key] = [result[key]]
                        
                        if isinstance(value, list):
                            result[key].extend(value)
                        else:
                            result[key].append(value)
                else:
                    # 这是一个新键，只需添加它
                    result[key] = value
                    
            return result
        return json.loads(json_content, object_pairs_hook=recursive_merge_hook)

    # --------------------------根据规则根据前两步给出的headers和第一次层级进行构建 -------------------------------
    def merge_duplicate_keys(data_rows, hierarchy_keys):
        """
        处理重复key的情况，当出现重复时进行合并而不是替换
        """
        result = {}
        
        for row in data_rows:
            current_dict = result
            
            # 遍历层级键
            for i, key_name in enumerate(hierarchy_keys):
                # 构造语义化的key名称：[Header Name] [Cell Value]
                if row[i]:  # 如果值不为空
                    semantic_key = f"{key_name} {row[i]}"
                else:
                    semantic_key = f"{key_name} "
                
                # 如果这是最后一个层级键，需要处理record数据
                if i == len(hierarchy_keys) - 1:
                    if semantic_key not in current_dict:
                        current_dict[semantic_key] = {}
                    
                    # 这里处理record数据...
                    # （后续会完善）
                else:
                    # 中间层级，如果key不存在就创建
                    if semantic_key not in current_dict:
                        current_dict[semantic_key] = {}
                    current_dict = current_dict[semantic_key]
        
        return result

    # 更完整的合并函数
    def build_merged_tree(self, table_data, normalized_headers, hierarchy_def):
        """
        构建合并重复key的树形结构
        """
        hierarchy_keys = hierarchy_def["hierarchy_keys"]
        value_leaves = hierarchy_def["value_leaves"]
        semantic_groups = hierarchy_def.get("semantic_groups", {})
        
        result = {}
        
        # 跳过表头，从数据行开始处理
        data_rows = table_data[2:]  # 假设前两行是表头
        
        for row in data_rows:
            current_dict = result
            
            # 按层级键构建嵌套结构
            for i, key_name in enumerate(hierarchy_keys):
                key_idx = normalized_headers.index(key_name)
                cell_value = row[key_idx] if key_idx < len(row) else ""
                
                # 构造语义化的key
                if cell_value:
                    semantic_key = f"{key_name} {cell_value}"
                else:
                    semantic_key = f"{key_name} "
                
                # 如果key不存在，创建新的字典
                if semantic_key not in current_dict:
                    current_dict[semantic_key] = {}
                
                current_dict = current_dict[semantic_key]
            
            # 在最深层添加value_leaves数据
            for group_name, group_fields in semantic_groups.items():
                if group_name not in current_dict:
                    current_dict[group_name] = {}
                
                for field in group_fields:
                    if field in normalized_headers:
                        field_idx = normalized_headers.index(field)
                        if field_idx < len(row):
                            value = row[field_idx]
                            # 尝试转换为数字
                            try:
                                if '.' in value:
                                    value = float(value)
                                else:
                                    value = int(value)
                            except (ValueError, AttributeError):
                                pass  # 保持原始字符串
                            
                            current_dict[group_name][field] = value
        
        return result

import re
from copy import deepcopy
from openpyxl.utils.cell import range_boundaries

def is_cell_position(text):
    """
    支持可选的绝对引用符号$: 如 $A$1
    """
    return bool(re.match(r'^\$?[A-Z]+\$?[0-9]+$', text.strip().upper()))

def is_cell_range(text):
    """
    匹配区域引用: 如 A1:B9、$A$1:$C$3
    """
    return bool(re.match(r'^\$?[A-Z]+\$?[0-9]+:\$?[A-Z]+\$?[0-9]+$', text.strip().upper()))

def get_value_from_ref(ref, sheet, range_policy="merged_top_left"):
    """
    range_policy:
      - "merged_top_left": 若为合并区域或普通区域，均取左上角值（默认）
      - "matrix": 非合并区域返回二维列表
      - "flatten": 非合并区域返回一维扁平列表
    """
    ref_u = ref.strip().upper()

    # 单个单元格
    if is_cell_position(ref_u):
        try:
            return sheet[ref_u].value
        except Exception as e:
            print(f"警告: 无法读取单元格 {ref}: {e}")
            return ref

    # 区域引用
    if is_cell_range(ref_u):
        try:
            min_col, min_row, max_col, max_row = range_boundaries(ref_u)

            # 若该区域正好是合并区域，则返回左上角的值
            for mr in sheet.merged_cells.ranges:
                if range_boundaries(str(mr).upper()) == (min_col, min_row, max_col, max_row):
                    return sheet.cell(row=min_row, column=min_col).value

            # 非合并区域，按策略返回
            cells = sheet[ref_u]
            if range_policy == "matrix":
                if isinstance(cells, tuple) and cells and isinstance(cells[0], tuple):
                    return [[c.value for c in row] for row in cells]
                else:
                    return [c.value for c in cells]
            if range_policy == "flatten":
                if isinstance(cells, tuple) and cells and isinstance(cells[0], tuple):
                    return [c.value for row in cells for c in row]
                else:
                    return [c.value for c in cells]

            # 默认：左上角
            return sheet.cell(row=min_row, column=min_col).value

        except Exception as e:
            print(f"警告: 无法读取区域 {ref}: {e}")
            return ref

    # 非引用字符串原样返回
    return ref

def convert_cell_positions_to_values(data_dict, sheet, range_policy="merged_top_left"):
    """
    将叶子节点的 'A1' 或 'A1:C3' 等引用转换为实际值/区域值
    """
    result = deepcopy(data_dict)

    def recursive_convert(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                obj[k] = recursive_convert(v)
            return obj
        elif isinstance(obj, str):
            return get_value_from_ref(obj, sheet, range_policy=range_policy)
        else:
            return obj

    return recursive_convert(result)

from openpyxl.utils import get_column_letter, range_boundaries


def execute_tree_building_code(code: str, raw_table: List[List], headers: List[str], hierarchy_def: Dict[str, Any]) -> Dict[str, Any]:
    """
    安全执行 LLM 生成的树构建代码
    
    Args:
        code: LLM 生成的 Python 代码
        raw_table: 原始表格数据 (List[List])
        headers: 规范化表头列表
        hierarchy_def: 层次定义字典
    
    Returns:
        tree_result: 构建完成的树结构
    
    Raises:
        Exception: 代码执行错误或安全违规
    """
    # 安全检查：检查危险关键词
    DANGEROUS_KEYWORDS = ['import', 'exec', 'open', '__', 'os', 'sys', 'subprocess', 'eval', 'globals', 'locals', 'compile']
    pattern = r"\b(" + "|".join(re.escape(k) for k in DANGEROUS_KEYWORDS) + r")\b"
    
    match = re.search(pattern, code)
    if match:
        keyword_found = match.group(1)
        raise Exception(f"安全违规: 代码中发现危险关键词 '{keyword_found}'")
    
    # 创建安全的执行环境
    safe_builtins = {
        # 基本类型和转换
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        
        # 常量
        "None": None,
        "True": True,
        "False": False,
        
        # 迭代和范围
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "reversed": reversed,
        "sorted": sorted,
        "iter": iter,
        "next": next,
        
        # 长度和计数
        "len": len,
        "sum": sum,
        "min": min,
        "max": max,
        "abs": abs,
        "round": round,
        
        # 类型检查
        "isinstance": isinstance,
        "type": type,
        
        # 逻辑操作
        "any": any,
        "all": all,
        
        # 过滤和映射
        "filter": filter,
        "map": map,
    }
    
    # 创建执行上下文，注入预定义变量
    execution_context = {
        "__builtins__": safe_builtins,
        "raw_table": raw_table,
        "headers": headers,
        "hierarchy_def": hierarchy_def,
    }
    
    try:
        # 执行代码
        exec(code, execution_context)
        
        # 检查结果变量是否存在
        if 'tree_result' not in execution_context:
            raise Exception("代码执行完成，但未找到 'tree_result' 变量。请确保代码将最终结果赋值给 'tree_result'。")
        
        return execution_context['tree_result']
        
    except Exception as e:
        raise e


def estimate_tokens(text: Any, model: str = "gpt-4o") -> int:
    """计算/估算文本的 Token 数量"""
    if text is None:
        return 0
    text_str = str(text).strip()
    if not text_str:
        return 0
    try:
        import tiktoken
        if "gpt-4" in model.lower():
            encoding = tiktoken.encoding_for_model("gpt-4")
        elif "gpt-3.5" in model.lower():
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        else:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text_str))
    except Exception:
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text_str))
        english_chars = len(text_str) - chinese_chars
        return max(1, int(chinese_chars * 1.5 + english_chars * 0.25))


def calculate_table_characteristics(
    table: List[List], 
    gamma: int = 50, 
    model_name: str = "gpt-4o"
) -> Dict[str, Any]:
    """
    计算表格的统计特征与文本密度指标（对应 ASTRA 论文中 AdaSTR 的特征分析）
    
    Args:
        table: 原始表格（List[List]）
        gamma: 长单元格阈值（Token数），默认 50
        model_name: 用于计算 Token 的模型名称
        
    Returns:
        包含以下统计量的字典：
        - num_rows: 行数
        - num_cols: 最大列数
        - total_cells: 矩阵总单元格数 (num_rows * num_cols)
        - non_empty_cells: 非空单元格数 n
        - total_tokens: 估算的总 Token 数 S
        - avg_cell_tokens: 平均非空单元格 Token 长度 s_bar (文本密度指标)
        - long_cell_count: 超过 gamma 阈值的长单元格数量
        - long_cell_ratio: 长单元格占比 r_long (文本密度指标)
    """
    if not table or not isinstance(table, list):
        return {
            "num_rows": 0,
            "num_cols": 0,
            "total_cells": 0,
            "non_empty_cells": 0,
            "total_tokens": 0,
            "avg_cell_tokens": 0.0,
            "long_cell_count": 0,
            "long_cell_ratio": 0.0
        }
    
    num_rows = len(table)
    num_cols = max((len(r) for r in table if isinstance(r, list)), default=0)
    total_cells = num_rows * num_cols
    
    non_empty_cells = 0
    total_tokens = 0
    long_cell_count = 0
    
    for row in table:
        if not isinstance(row, list):
            continue
        for cell in row:
            if cell is not None and str(cell).strip() != "":
                cell_tokens = estimate_tokens(cell, model=model_name)
                non_empty_cells += 1
                total_tokens += cell_tokens
                if cell_tokens > gamma:
                    long_cell_count += 1
    
    avg_cell_tokens = (total_tokens / non_empty_cells) if non_empty_cells > 0 else 0.0
    long_cell_ratio = (long_cell_count / non_empty_cells) if non_empty_cells > 0 else 0.0
    
    return {
        "num_rows": num_rows,
        "num_cols": num_cols,
        "total_cells": total_cells,
        "non_empty_cells": non_empty_cells,
        "total_tokens": total_tokens,
        "avg_cell_tokens": round(avg_cell_tokens, 2),
        "long_cell_count": long_cell_count,
        "long_cell_ratio": round(long_cell_ratio, 4)
    }


def select_adaptive_tree_mode(
    table: List[List],
    sheet: Any = None,
    model_name: str = "gpt-4o",
    context_limit: int = 32768,
    alpha: float = 0.6,
    l_sys: int = 1500,
    reserved_gen_tokens: int = 2000,
    mu: float = 80.0,
    eta: float = 0.3,
    n_high: int = 1000,
    gamma: int = 50
) -> Tuple[str, Dict[str, Any]]:
    """
    根据表格规模与文本密度自适应选择建树模式 (DSP / SRE / PSS)
    
    决策规则（对应 ASTRA 论文 AdaSTR Decision Rules）：
    1. 计算可用推理预算 B = alpha * context_limit - l_sys - reserved_gen_tokens
    2. DSP (Direct Semantic Parsing, 即 "normal"):
       S <= B: 估算 Token 未超过预算，使用直接 LLM 生成以获得最大语义保真度。
    3. SRE (Symbolic Reference Encoding, 即 "enhanced"):
       S > B 且 n <= n_high 且 (s_bar > mu 或 r_long > eta):
       规模尚可但单元格文本密度高（富文本或长文本），使用单元格坐标引用 (A1:B2) 压缩上下文。
       注意：若 sheet is None（无法提取 openpyxl 单元格坐标与合并关系），则退回 "code_based"。
    4. PSS (Programmatic Structure Synthesis, 即 "code_based"):
       S > B 且 n > n_high:
       超大规模表格，使用代码生成 + 沙箱执行，避免生成长度截断。
    5. Fallback:
       若 S > B 但以上严格条件均未满足，默认走 "enhanced"（若 sheet 存在）或 "code_based"（若 sheet 为空）。
       
    Returns:
        (selected_mode, stats_dict)
    """
    stats = calculate_table_characteristics(table, gamma=gamma, model_name=model_name)
    S = stats["total_tokens"]
    n = stats["non_empty_cells"]
    s_bar = stats["avg_cell_tokens"]
    r_long = stats["long_cell_ratio"]
    
    # 预算 B
    l_safe = int(alpha * context_limit)
    B = max(1000, l_safe - l_sys - reserved_gen_tokens)
    stats["budget_B"] = B
    
    decision_reason = ""
    selected_mode = "normal"
    
    # 1. DSP (Default)
    if S <= B:
        selected_mode = "normal"
        decision_reason = f"Token 预算充足 (S={S} <= B={B})，采用 DSP (normal) 直接生成"
    # 2. SRE (Density-First)
    elif n <= n_high and (s_bar > mu or r_long > eta):
        if sheet is not None:
            selected_mode = "enhanced"
            decision_reason = f"高文本密度且规模适中 (S={S} > B={B}, n={n} <= {n_high}, s_bar={s_bar} > {mu} 或 r_long={r_long:.2%} > {eta:.0%})，采用 SRE (enhanced) 坐标引用编码"
        else:
            selected_mode = "code_based"
            decision_reason = f"检测到高文本密度 (S={S} > B={B}, s_bar={s_bar}, r_long={r_long:.2%})，但无 openpyxl sheet，自动转用 PSS (code_based)"
    # 3. PSS (Scale-First)
    elif n > n_high:
        selected_mode = "code_based"
        decision_reason = f"超大规模表格 (S={S} > B={B}, n={n} > n_high={n_high})，采用 PSS (code_based) 程序化结构合成"
    # 4. Fallback Edge Case
    else:
        if sheet is not None:
            selected_mode = "enhanced"
            decision_reason = f"超预算边界样本 (S={S} > B={B})，兜底采用 SRE (enhanced)"
        else:
            selected_mode = "code_based"
            decision_reason = f"超预算边界样本 (S={S} > B={B}) 且无 sheet，兜底采用 PSS (code_based)"
            
    stats["decision_reason"] = decision_reason
    stats["selected_mode"] = selected_mode
    return selected_mode, stats


def table2tree_llm(sheet, table, model_name, temperature, model_type, table2_tree_mode):
    """
    Input :
        sheet : 原始表格的sheet (可为 None)
        table : 原始表格 (List[List] 格式)
        model_name : 模型名称
        temperature : 温度
        model_type : 使用开源还是闭源模型 ("oai" 或 "opensource")
        table2_tree_mode : 表格转树形结构模式
            - "normal": 标准模式，LLM 直接生成 JSON 树 (DSP)
            - "enhanced": 增强模式，使用单元格位置标识，适用于有合并单元格的表格 (SRE)
            - "code_based": 代码生成模式，LLM 生成代码构建树，适用于大型表格 (PSS)
            - "adaptive": 自适应模式，根据行列数、单元格规模与文本密度自动选择 DSP/SRE/PSS
    Output :
        Tree_table_v1, Tree_table_v2 : 树化表格
    """
    converter = llm_based_converter(model_type, model_name)
    Tree_table_v1 = None
    Tree_table_v2 = None
    
    actual_mode = table2_tree_mode.lower()
    if actual_mode == "adaptive":
        selected_mode, stats = select_adaptive_tree_mode(
            table=table, sheet=sheet, model_name=model_name
        )
        print(f"\n🧠 [AdaSTR 自适应建树决策] 表格规模: {stats['num_rows']}行 x {stats['num_cols']}列, "
              f"非空单元格: {stats['non_empty_cells']}, 估算 Token: {stats['total_tokens']}/{stats['budget_B']}, "
              f"平均单元格 Token: {stats['avg_cell_tokens']}, 长单元格比率: {stats['long_cell_ratio']:.2%}")
        print(f"👉 决策结果: {stats['selected_mode'].upper()} | 原因: {stats['decision_reason']}")
        actual_mode = selected_mode
        
    if actual_mode == "normal":
        try:
            Normalized_headers = converter.header_analysis_norm(table, temperature)
            Hierarchy_definition = converter.hierarchy_definition(table, Normalized_headers, temperature)
            Final_json_tree = converter.final_json_tree_construction(table, Normalized_headers, Hierarchy_definition, temperature)
            if model_type == "oai":
                Tree_table_v1 = converter.parse_json_with_merge_oai(Final_json_tree)
            else:
                Tree_table_v1 = converter.parse_json_with_merge(Final_json_tree)
            Tree_table_v2 = None
        except Exception as e:
            if table2_tree_mode.lower() == "adaptive":
                print(f"⚠️ normal (DSP) 模式生成失败: {e}，自动降级至 code_based (PSS) 重试...")
                actual_mode = "code_based"
            else:
                raise e

    if actual_mode == "enhanced":
        if sheet is None:
            if table2_tree_mode.lower() == "adaptive":
                print(f"⚠️ enhanced 模式需要 sheet 对象但传入为 None，自动转用 code_based (PSS)...")
                actual_mode = "code_based"
            else:
                raise ValueError("enhanced 模式需要提供 sheet 对象")
        else:
            try:
                markdown_table = excel_to_markdown_with_cell_ref(sheet)
                Normalized_headers = converter.header_analysis_norm_enhance(markdown_table, temperature)
                Hierarchy_definition = converter.hierarchy_definition_enhance(markdown_table, Normalized_headers, temperature)
                Final_json_tree = converter.final_json_tree_construction_enhance(markdown_table, Normalized_headers, Hierarchy_definition, temperature)
                if model_type == "oai":
                    Tree_table_v1 = converter.parse_json_with_merge_oai(Final_json_tree)
                else:
                    Tree_table_v1 = converter.parse_json_with_merge(Final_json_tree)
                Tree_table_v1 = convert_cell_positions_to_values(Tree_table_v1, sheet)
            except Exception as e:
                if table2_tree_mode.lower() == "adaptive":
                    print(f"⚠️ enhanced (SRE) 模式生成失败: {e}，自动降级至 code_based (PSS) 重试...")
                    actual_mode = "code_based"
                else:
                    raise e
                    
    if actual_mode == "code_based":
        print("🔧 使用 code_based (PSS) 模式：LLM 将生成代码来构建树结构")
        Normalized_headers = converter.header_analysis_norm(table, temperature)
        Hierarchy_definition = converter.hierarchy_definition(table, Normalized_headers, temperature)
        Tree_table_v1 = converter.code_based_tree_construction(
            table=table,
            Normalized_headers=Normalized_headers,
            Hierarchy_definition=Hierarchy_definition,
            temperature=temperature
        )
        Tree_table_v2 = None
        
    return Tree_table_v1, Tree_table_v2
