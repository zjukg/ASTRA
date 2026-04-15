"""
Tree Quality Evaluator - 树形表格质量评测模块

该模块用于评估从原始表格转换为树形结构的质量
主要评测指标：
1. 信息覆盖率（Information Coverage Rate）
2. 结构定位准确率（Structural Positioning Accuracy）
3. 树结构统计（Tree Structure Statistics）
4. 路径一致性（Path Consistency）
"""

import json
import re
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict


class TreeQualityEvaluator:
    """树形表格质量评估器"""
    
    def __init__(self, handle_combined_keys=True):
        """
        初始化评估器
        
        Args:
            handle_combined_keys: 是否处理组合键（如 "Header1 - Value1"）
                                  对于 LLM_based 方法生成的树，应设置为 True
        """
        self.metrics = {}
        self.handle_combined_keys = handle_combined_keys
        
    def evaluate(self, original_table: List[List[str]], tree_table: Dict[str, Any]) -> Dict[str, Any]:
        """
        全面评估树形表格质量
        
        Args:
            original_table: 原始表格（二维列表）
            tree_table: 树形表格结构
            
        Returns:
            包含所有评测指标的字典
        """
        print("\n" + "="*60)
        print("🔍 开始树形表格质量评估")
        print("="*60)
        
        # 1. 信息覆盖率
        coverage_metrics = self.calculate_information_coverage(original_table, tree_table)
        
        # 2. 结构定位准确率
        positioning_metrics = self.calculate_structural_positioning(original_table, tree_table)
        
        # 3. 树结构统计
        structure_metrics = self.calculate_tree_statistics(tree_table)
        
        # 4. 路径一致性
        path_metrics = self.calculate_path_consistency(original_table, tree_table)
        
        # 汇总所有指标
        all_metrics = {
            "coverage": coverage_metrics,
            "positioning": positioning_metrics,
            "structure": structure_metrics,
            "path_consistency": path_metrics,
            "overall_score": self._calculate_overall_score(
                coverage_metrics, positioning_metrics, path_metrics
            )
        }
        
        # 打印评估报告
        self.print_evaluation_report(all_metrics)
        
        return all_metrics
    
    def calculate_information_coverage(self, original_table: List[List[str]], 
                                       tree_table: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算信息覆盖率
        
        检查原始表格中有多少比例的单元格信息被包含在树中
        """
        print("\n📊 计算信息覆盖率...")
        
        # 提取原始表格中所有非空单元格的内容
        original_cells = set()
        total_cells = 0
        non_empty_cells = 0
        
        for row in original_table:
            for cell in row:
                total_cells += 1
                cell_str = str(cell).strip()
                if cell_str and cell_str != "":
                    original_cells.add(cell_str)
                    non_empty_cells += 1
        
        # 提取树中所有的值
        tree_values = set()
        self._extract_all_values(tree_table, tree_values)
        
        # 计算覆盖率
        covered_cells = original_cells.intersection(tree_values)
        coverage_rate = len(covered_cells) / len(original_cells) if original_cells else 0
        
        # 找出未覆盖的单元格
        missing_cells = original_cells - tree_values
        
        # 找出树中多余的值（不在原表格中）
        extra_values = tree_values - original_cells
        
        metrics = {
            "total_cells": total_cells,
            "non_empty_cells": non_empty_cells,
            "original_unique_values": len(original_cells),
            "tree_unique_values": len(tree_values),
            "covered_values": len(covered_cells),
            "missing_values": len(missing_cells),
            "extra_values": len(extra_values),
            "coverage_rate": coverage_rate,
            "missing_cells_list": list(missing_cells)[:10],  # 只保留前10个示例
            "extra_values_list": list(extra_values)[:10]
        }
        
        print(f"   ✓ 原表格唯一值数量: {len(original_cells)}")
        print(f"   ✓ 树中唯一值数量: {len(tree_values)}")
        print(f"   ✓ 覆盖的值数量: {len(covered_cells)}")
        print(f"   ✓ 信息覆盖率: {coverage_rate:.2%}")
        
        return metrics
    
    def calculate_structural_positioning(self, original_table: List[List[str]], 
                                         tree_table: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算结构定位准确率
        
        检查树中的路径是否与原表格的行列关系一致
        路径中的父节点应该与叶子节点在同行或同列
        """
        print("\n🎯 计算结构定位准确率...")
        
        # 构建原表格的值到位置的映射
        value_to_positions = self._build_value_position_map(original_table)
        
        # 获取所有路径
        all_paths = []
        self._extract_all_paths(tree_table, [], all_paths)
        
        total_paths = len(all_paths)
        valid_paths = 0
        invalid_paths_details = []
        
        for path in all_paths:
            if len(path) < 2:  # 路径太短，跳过
                continue
            
            # 检查路径的结构定位准确性
            is_valid, reason = self._validate_path_positioning(path, value_to_positions)
            
            if is_valid:
                valid_paths += 1
            else:
                if len(invalid_paths_details) < 5:  # 只保留前5个无效路径示例
                    invalid_paths_details.append({
                        "path": path,
                        "reason": reason
                    })
        
        positioning_accuracy = valid_paths / total_paths if total_paths > 0 else 0
        
        metrics = {
            "total_paths": total_paths,
            "valid_paths": valid_paths,
            "invalid_paths": total_paths - valid_paths,
            "positioning_accuracy": positioning_accuracy,
            "invalid_paths_examples": invalid_paths_details
        }
        
        print(f"   ✓ 总路径数量: {total_paths}")
        print(f"   ✓ 有效路径数量: {valid_paths}")
        print(f"   ✓ 结构定位准确率: {positioning_accuracy:.2%}")
        
        return metrics
    
    def calculate_tree_statistics(self, tree_table: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算树结构统计信息
        """
        print("\n📈 计算树结构统计...")
        
        total_nodes = 0
        leaf_nodes = 0
        max_depth = 0
        depth_distribution = defaultdict(int)
        branching_factors = []
        
        def traverse(node, depth=0):
            nonlocal total_nodes, leaf_nodes, max_depth
            
            total_nodes += 1
            max_depth = max(max_depth, depth)
            depth_distribution[depth] += 1
            
            if isinstance(node, dict):
                children_count = 0
                has_children = False
                
                for key, value in node.items():
                    if isinstance(value, (dict, list)):
                        has_children = True
                        children_count += 1
                        if isinstance(value, dict):
                            traverse(value, depth + 1)
                        elif isinstance(value, list):
                            for item in value:
                                traverse(item, depth + 1)
                    elif isinstance(value, dict):
                        has_children = True
                        children_count += 1
                        traverse(value, depth + 1)
                
                if has_children and children_count > 0:
                    branching_factors.append(children_count)
                
                if not has_children:
                    leaf_nodes += 1
            elif isinstance(node, list):
                for item in node:
                    traverse(item, depth)
            else:
                leaf_nodes += 1
        
        if isinstance(tree_table, list):
            for root in tree_table:
                traverse(root, 0)
        else:
            traverse(tree_table, 0)
        
        avg_branching = sum(branching_factors) / len(branching_factors) if branching_factors else 0
        
        metrics = {
            "total_nodes": total_nodes,
            "leaf_nodes": leaf_nodes,
            "internal_nodes": total_nodes - leaf_nodes,
            "max_depth": max_depth,
            "avg_branching_factor": avg_branching,
            "depth_distribution": dict(depth_distribution)
        }
        
        print(f"   ✓ 总节点数: {total_nodes}")
        print(f"   ✓ 叶子节点数: {leaf_nodes}")
        print(f"   ✓ 最大深度: {max_depth}")
        print(f"   ✓ 平均分支因子: {avg_branching:.2f}")
        
        return metrics
    
    def calculate_path_consistency(self, original_table: List[List[str]], 
                                   tree_table: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算路径一致性
        
        检查路径中的所有节点是否都能在原表格中找到，并且保持了合理的层次关系
        支持组合键的拆分验证
        """
        print("\n🔗 计算路径一致性...")
        
        value_to_positions = self._build_value_position_map(original_table)
        all_paths = []
        self._extract_all_paths(tree_table, [], all_paths)
        
        consistent_paths = 0
        total_paths = len(all_paths)
        inconsistent_examples = []
        
        for path in all_paths:
            # 检查路径中的所有值是否都在原表格中（支持组合键拆分）
            path_consistent = True
            
            for node in path[1:]:  # 跳过ROOT
                node_str = str(node).strip()
                if not node_str:
                    continue
                
                # 获取节点的所有可能形式（包括拆分后的部分）
                node_forms = self._split_combined_key(node_str)
                
                # 至少有一种形式存在于原表格中
                exists = any(form in value_to_positions for form in node_forms)
                
                if not exists:
                    path_consistent = False
                    if len(inconsistent_examples) < 3:  # 只保留前3个示例
                        inconsistent_examples.append({
                            "path": path,
                            "missing_node": node_str
                        })
                    break
            
            if path_consistent:
                consistent_paths += 1
        
        consistency_rate = consistent_paths / total_paths if total_paths > 0 else 0
        
        metrics = {
            "total_paths": total_paths,
            "consistent_paths": consistent_paths,
            "inconsistent_paths": total_paths - consistent_paths,
            "consistency_rate": consistency_rate,
            "inconsistent_examples": inconsistent_examples
        }
        
        print(f"   ✓ 路径一致性: {consistency_rate:.2%}")
        
        return metrics
    
    def _split_combined_key(self, key: str) -> List[str]:
        """
        拆分组合键
        
        对于 LLM_based 方法，键可能是 "Header1 - Value1" 格式
        返回拆分后的各部分，同时也保留完整的键
        
        Args:
            key: 可能包含 " - " 的键
            
        Returns:
            包含原始键和拆分部分的列表
        """
        parts = [key]  # 首先保留完整的键
        
        if self.handle_combined_keys and " - " in key:
            # 拆分键，去除前后空格
            split_parts = [part.strip() for part in key.split(" - ") if part.strip()]
            parts.extend(split_parts)
        
        return parts
    
    def _extract_all_values(self, node: Any, values: Set[str]):
        """递归提取树中所有的值，支持组合键拆分"""
        if isinstance(node, dict):
            for key, value in node.items():
                # 添加key（包括拆分后的部分）
                if str(key).strip():
                    key_str = str(key).strip()
                    # 添加所有形式的key
                    for part in self._split_combined_key(key_str):
                        if part:
                            values.add(part)
                
                # 递归处理value
                if isinstance(value, (dict, list)):
                    self._extract_all_values(value, values)
                else:
                    # 添加叶子节点的值
                    if str(value).strip():
                        values.add(str(value).strip())
        elif isinstance(node, list):
            for item in node:
                self._extract_all_values(item, values)
        else:
            if str(node).strip():
                values.add(str(node).strip())
    
    def _build_value_position_map(self, table: List[List[str]]) -> Dict[str, List[Tuple[int, int]]]:
        """构建值到位置的映射"""
        value_map = defaultdict(list)
        
        for row_idx, row in enumerate(table):
            for col_idx, cell in enumerate(row):
                cell_str = str(cell).strip()
                if cell_str:
                    value_map[cell_str].append((row_idx, col_idx))
        
        return value_map
    
    def _extract_all_paths(self, node: Any, current_path: List[str], all_paths: List[List[str]]):
        """递归提取所有从根到叶子的路径"""
        if isinstance(node, dict):
            has_dict_child = False
            for key, value in node.items():
                new_path = current_path + [str(key)]
                if isinstance(value, dict):
                    has_dict_child = True
                    self._extract_all_paths(value, new_path, all_paths)
                elif isinstance(value, list):
                    has_dict_child = True
                    for item in value:
                        self._extract_all_paths(item, new_path, all_paths)
                else:
                    # 叶子节点
                    all_paths.append(new_path + [str(value)])
            
            # 如果没有字典子节点，这本身就是一个路径
            if not has_dict_child and current_path:
                all_paths.append(current_path)
        elif isinstance(node, list):
            for item in node:
                self._extract_all_paths(item, current_path, all_paths)
        else:
            if current_path:
                all_paths.append(current_path + [str(node)])
    
    def _validate_path_positioning(self, path: List[str], 
                                   value_map: Dict[str, List[Tuple[int, int]]]) -> Tuple[bool, str]:
        """
        验证路径的结构定位是否正确（优化版 - 交叉点验证）
        
        新的验证逻辑：
        - 从ROOT开始遍历路径，维护一个"已验证节点集合"
        - 中间节点：与集合中**任意一个节点**在同行或同列即可
        - 叶子节点（最后一个节点）：必须同时满足行维度和列维度约束（交叉点验证）
        
        交叉点验证原理：
        表格中的数据值是多个维度的交叉点，必须同时满足：
        - 与路径中至少一个"行维度节点"在同一行
        - 与路径中至少一个"列维度节点"在同一列
        
        示例：
        表格: Year(0,0) | Q1(0,1) | Q2(0,2)
              2018(1,0) | 212(1,1)| 225(1,2)
        
        路径1: Year → 2018 → Q1 → 212
        - 2018(1,0)确定行=1, Q1(0,1)确定列=1
        - 212在(1,1) ✅ 同时满足行列约束
        
        路径2: Year → 2018 → Q1 → 225
        - 2018(1,0)确定行=1, Q1(0,1)确定列=1  
        - 225在(1,2) ❌ 不在列1上，验证失败！
        """
        # 跳过ROOT和空值
        valid_nodes = [node for node in path if node != "ROOT" and str(node).strip()]
        
        if len(valid_nodes) < 2:
            return True, "路径太短"
        
        # 对于LLM_based的扁平结构（3个节点：行标题 -> 列标题[组合] -> 数据值）
        # 只验证最后一对节点的位置关系
        if self.handle_combined_keys and len(valid_nodes) == 3:
            # 只检查倒数第二个节点（列标题或组合键）和最后一个节点（数据值）
            parent = str(valid_nodes[-2]).strip()
            child = str(valid_nodes[-1]).strip()
            
            # 获取parent的所有部分（如果是组合键则拆分，否则就是自己）
            parent_forms = self._split_combined_key(parent)
            
            # 获取这些部分的位置
            parent_all_positions = []
            for form in parent_forms:
                if form in value_map:
                    parent_all_positions.extend(value_map[form])
            
            # 获取叶子值的位置
            child_all_positions = value_map.get(child, [])
            
            # 如果找不到位置，跳过
            if not parent_all_positions or not child_all_positions:
                return True, "位置信息不完整"
            
            # 如果parent是组合键，检查其任一部分是否与叶子值在同一列
            # 如果parent不是组合键，检查是否在同行或同列
            if " - " in parent:
                # 组合键：检查是否在同一列
                parent_cols = set(col for _, col in parent_all_positions)
                child_cols = set(col for _, col in child_all_positions)
                
                if parent_cols & child_cols:
                    return True, "路径有效"
                else:
                    return False, f"组合键 '{parent}' 与数据值 '{child}' 不在同一列"
            else:
                # 非组合键：检查同行或同列
                for p_row, p_col in parent_all_positions:
                    for c_row, c_col in child_all_positions:
                        if p_row == c_row or p_col == c_col:
                            return True, "路径有效"
                return False, f"节点 '{parent}' 与 '{child}' 不在同行或同列"
        
        # ========== 对于其他结构，使用新的集合验证逻辑 ==========
        
        # 获取所有节点的位置信息
        node_positions_list = []  # [(node_name, [positions])]
        
        for node in valid_nodes:
            node_str = str(node).strip()
            node_forms = self._split_combined_key(node_str)
            
            # 收集该节点所有形式的位置
            all_positions = []
            for form in node_forms:
                if form in value_map:
                    all_positions.extend(value_map[form])
            
            node_positions_list.append((node_str, all_positions))
        
        # 如果第一个节点没有位置信息，可能是创造的分类节点，跳过它
        if not node_positions_list[0][1]:
            # 从第二个节点开始（如果存在）
            node_positions_list = node_positions_list[1:]
            if len(node_positions_list) < 2:
                return True, "有效节点太少"
        
        # 初始化：第一个有位置信息的节点加入已验证集合
        verified_set = [node_positions_list[0]]  # [(node_name, [positions])]
        
        # 逐个验证后续节点
        for i in range(1, len(node_positions_list)):
            current_node, current_positions = node_positions_list[i]
            
            # 如果当前节点没有位置信息，可能是创造的节点
            if not current_positions:
                # 对于没有位置的节点，允许通过（可能是分类节点）
                # 但不加入验证集合
                continue
            
            # 检查当前节点是否与已验证集合中的任意节点在同行或同列
            found_connection = False
            connection_type = ""
            
            for verified_node, verified_positions in verified_set:
                # 检查当前节点与已验证节点的位置关系
                for curr_row, curr_col in current_positions:
                    for ver_row, ver_col in verified_positions:
                        if curr_row == ver_row or curr_col == ver_col:
                            found_connection = True
                            connection_type = f"与 '{verified_node}' "
                            connection_type += "同行" if curr_row == ver_row else "同列"
                            break
                    if found_connection:
                        break
                if found_connection:
                    break
            
            # 如果标准检查没有找到连接，且启用了组合键处理
            # 检查是否是组合键的特殊情况
            if not found_connection and self.handle_combined_keys:
                # 检查已验证集合中是否有组合键
                for verified_node, verified_positions in verified_set:
                    if " - " in verified_node:
                        # 组合键：检查是否在同一列
                        verified_cols = set(col for _, col in verified_positions)
                        current_cols = set(col for _, col in current_positions)
                        
                        if verified_cols & current_cols:
                            found_connection = True
                            connection_type = f"与组合键 '{verified_node}' 同列"
                            break
            
            if not found_connection:
                # 如果没有找到连接，返回失败
                verified_names = [name for name, _ in verified_set]
                return False, f"节点 '{current_node}' 与已验证集合 {verified_names} 中任何节点都不在同行或同列"
            
            # 将当前节点加入已验证集合
            verified_set.append((current_node, current_positions))
        
        # ========== 交叉点验证：对叶子节点进行额外检查 ==========
        # 叶子节点必须同时满足行维度和列维度约束
        if len(verified_set) >= 3:  # 至少有3个节点才需要交叉点验证
            leaf_node, leaf_positions = verified_set[-1]  # 最后一个节点是叶子
            non_leaf_nodes = verified_set[:-1]  # 前面的都是非叶子节点
            
            # 检查叶子节点是否满足交叉点约束
            is_valid_intersection, intersection_reason = self._validate_intersection_constraint(
                leaf_node, leaf_positions, non_leaf_nodes
            )
            
            if not is_valid_intersection:
                return False, intersection_reason
        
        return True, "路径有效（集合验证+交叉点验证通过）"
    
    def _validate_intersection_constraint(self, 
                                         leaf_node: str, 
                                         leaf_positions: List[Tuple[int, int]], 
                                         non_leaf_nodes: List[Tuple[str, List[Tuple[int, int]]]]) -> Tuple[bool, str]:
        """
        验证叶子节点的交叉点约束（改进版 - 增加直接父节点约束）
        
        叶子节点（数据值）必须满足两层约束：
        
        1. **直接父节点约束**（最重要）：
           - 叶子节点的直接父节点（路径倒数第二个节点）必须与叶子节点在同一行或同一列
           - 这确保了父子关系的紧密性，防止路径过于冗长
        
        2. **增强的交叉点约束**：
           - 如果父节点与叶子同行（父节点是行标识），则必须有**其他节点**与叶子同列
           - 如果父节点与叶子同列（父节点是列标识），则必须有**其他节点**与叶子同行
        
        Args:
            leaf_node: 叶子节点名称
            leaf_positions: 叶子节点的所有位置 [(row, col), ...]
            non_leaf_nodes: 非叶子节点列表 [(node_name, [positions]), ...]
            
        Returns:
            (是否有效, 原因说明)
        
        示例（错误 - 缺少独立列标识）：
            路径: ... → Jamaica(5,0) → 31.2(5,3)
            - 直接父节点Jamaica与31.2同行 ✓
            - 但路径中缺少与31.2同列(col=3)的独立标识 ❌
            - 验证失败！应该包含列标题如"Secondary Applicants"
        """
        if not leaf_positions or not non_leaf_nodes:
            return True, "位置信息不完整"
        
        # ========== 第一层验证：直接父节点约束 ==========
        direct_parent_node, direct_parent_positions = non_leaf_nodes[-1]
        
        # 检查直接父节点与叶子节点的位置关系
        direct_parent_valid = False
        for leaf_row, leaf_col in leaf_positions:
            for parent_row, parent_col in direct_parent_positions:
                if parent_row == leaf_row or parent_col == leaf_col:
                    direct_parent_valid = True
                    break
            if direct_parent_valid:
                break
        
        if not direct_parent_valid:
            leaf_pos_str = ", ".join([f"({r},{c})" for r, c in leaf_positions])
            parent_pos_str = ", ".join([f"({r},{c})" for r, c in direct_parent_positions])
            return False, (f"直接父节点约束失败：'{direct_parent_node}'{parent_pos_str} "
                          f"与叶子节点'{leaf_node}'{leaf_pos_str}既不同行也不同列")
        
        # ========== 第二层验证：增强的交叉点约束 ==========
        for leaf_row, leaf_col in leaf_positions:
            # 收集所有与叶子同行的节点（行维度标识）
            row_identifiers = []  # [(node_name, node_position, is_direct_parent)]
            for i, (node_name, node_positions) in enumerate(non_leaf_nodes):
                for node_row, node_col in node_positions:
                    if node_row == leaf_row:
                        is_direct_parent = (i == len(non_leaf_nodes) - 1)
                        row_identifiers.append((node_name, (node_row, node_col), is_direct_parent))
                        break
            
            # 收集所有与叶子同列的节点（列维度标识）
            col_identifiers = []  # [(node_name, node_position, is_direct_parent)]
            for i, (node_name, node_positions) in enumerate(non_leaf_nodes):
                for node_row, node_col in node_positions:
                    if node_col == leaf_col:
                        is_direct_parent = (i == len(non_leaf_nodes) - 1)
                        col_identifiers.append((node_name, (node_row, node_col), is_direct_parent))
                        break
            
            # 检查是否同时有行列标识
            has_row_identifier = len(row_identifiers) > 0
            has_col_identifier = len(col_identifiers) > 0
            
            if not (has_row_identifier and has_col_identifier):
                continue  # 这个位置不满足交叉点约束，尝试下一个位置
            
            # 增强约束：至少有一个维度标识不是直接父节点
            parent_in_row = any(is_parent for _, _, is_parent in row_identifiers)
            parent_in_col = any(is_parent for _, _, is_parent in col_identifiers)
            has_non_parent_row = any(not is_parent for _, _, is_parent in row_identifiers)
            has_non_parent_col = any(not is_parent for _, _, is_parent in col_identifiers)
            
            # 如果直接父节点与叶子同行，则必须有其他节点与叶子同列（反之亦然）
            if parent_in_row and not parent_in_col:
                # 父节点在行维度，必须有独立的列维度标识
                if has_non_parent_col:
                    col_id = [name for name, pos, is_p in col_identifiers if not is_p][0]
                    return True, f"叶子节点 '{leaf_node}'({leaf_row},{leaf_col}) 是有效交叉点（行by父节点，列by {col_id}）"
            elif parent_in_col and not parent_in_row:
                # 父节点在列维度，必须有独立的行维度标识
                if has_non_parent_row:
                    row_id = [name for name, pos, is_p in row_identifiers if not is_p][0]
                    return True, f"叶子节点 '{leaf_node}'({leaf_row},{leaf_col}) 是有效交叉点（列by父节点，行by {row_id}）"
            elif not parent_in_row and not parent_in_col:
                # 直接父节点既不与叶子同行也不同列（理论上不应到此）
                return True, f"叶子节点 '{leaf_node}'({leaf_row},{leaf_col}) 是有效交叉点（独立行列标识）"
            # else: 父节点同时在行列维度中，继续检查下一个位置
        
        # 如果所有位置都不满足增强的交叉点约束，返回失败
        leaf_pos_str = ", ".join([f"({r},{c})" for r, c in leaf_positions])
        
        # 分析为什么失败
        for leaf_row, leaf_col in leaf_positions:
            row_nodes = [name for name, pos in non_leaf_nodes for r, c in pos if r == leaf_row]
            col_nodes = [name for name, pos in non_leaf_nodes for r, c in pos if c == leaf_col]
            
            if not row_nodes:
                error_msg = (f"交叉点约束失败：叶子节点 '{leaf_node}'{leaf_pos_str} "
                           f"在路径中找不到同行的节点（行={leaf_row}）")
            elif not col_nodes:
                error_msg = (f"交叉点约束失败：叶子节点 '{leaf_node}'{leaf_pos_str} "
                           f"在路径中找不到同列的节点（列={leaf_col}）")
            else:
                # 有行列标识，但不满足增强约束
                is_parent_row = direct_parent_node in row_nodes
                is_parent_col = direct_parent_node in col_nodes
                
                if is_parent_row and not [n for n in col_nodes if n != direct_parent_node]:
                    error_msg = (f"交叉点约束失败：叶子节点 '{leaf_node}'{leaf_pos_str} "
                               f"的直接父节点'{direct_parent_node}'在同一行，但缺少独立的列标识。"
                               f"可能路径过于冗长，缺少明确的列维度指示符。")
                elif is_parent_col and not [n for n in row_nodes if n != direct_parent_node]:
                    error_msg = (f"交叉点约束失败：叶子节点 '{leaf_node}'{leaf_pos_str} "
                               f"的直接父节点'{direct_parent_node}'在同一列，但缺少独立的行标识。"
                               f"可能路径过于冗长，缺少明确的行维度指示符。")
                else:
                    error_msg = (f"交叉点约束失败：叶子节点 '{leaf_node}'{leaf_pos_str} "
                               f"不满足增强的交叉点约束（同行节点：{row_nodes}，同列节点：{col_nodes}）")
            
            return False, error_msg
        
        # 默认错误信息
        error_msg = f"交叉点约束失败：叶子节点 '{leaf_node}'{leaf_pos_str} 未能通过验证"
        return False, error_msg
    
    def _calculate_overall_score(self, coverage: Dict, positioning: Dict, 
                                 path_consistency: Dict) -> float:
        """
        计算综合质量分数
        
        权重分配：
        - 信息覆盖率: 40%
        - 结构定位准确率: 35%
        - 路径一致性: 25%
        """
        coverage_score = coverage.get("coverage_rate", 0) * 0.4
        positioning_score = positioning.get("positioning_accuracy", 0) * 0.35
        consistency_score = path_consistency.get("consistency_rate", 0) * 0.25
        
        overall = coverage_score + positioning_score + consistency_score
        
        return round(overall, 4)
    
    def print_evaluation_report(self, metrics: Dict[str, Any]):
        """打印评估报告"""
        print("\n" + "="*60)
        print("📋 树形表格质量评估报告")
        if self.handle_combined_keys:
            print("   (启用组合键处理 - 适用于 LLM_based 方法)")
        print("="*60)
        
        # 1. 信息覆盖率
        cov = metrics["coverage"]
        print(f"\n【信息覆盖率】")
        print(f"  • 原表格唯一值: {cov['original_unique_values']}")
        print(f"  • 树中唯一值: {cov['tree_unique_values']}")
        print(f"  • 覆盖率: {cov['coverage_rate']:.2%}")
        if cov['missing_values'] > 0:
            print(f"  ⚠ 缺失值数量: {cov['missing_values']}")
            if cov['missing_cells_list']:
                print(f"  ⚠ 缺失值示例: {cov['missing_cells_list'][:3]}")
        
        # 2. 结构定位准确率
        pos = metrics["positioning"]
        print(f"\n【结构定位准确率】")
        print(f"  • 总路径数: {pos['total_paths']}")
        print(f"  • 有效路径数: {pos['valid_paths']}")
        print(f"  • 定位准确率: {pos['positioning_accuracy']:.2%}")
        
        # 3. 树结构统计
        struct = metrics["structure"]
        print(f"\n【树结构统计】")
        print(f"  • 总节点数: {struct['total_nodes']}")
        print(f"  • 叶子节点数: {struct['leaf_nodes']}")
        print(f"  • 最大深度: {struct['max_depth']}")
        print(f"  • 平均分支因子: {struct['avg_branching_factor']:.2f}")
        
        # 4. 路径一致性
        path = metrics["path_consistency"]
        print(f"\n【路径一致性】")
        print(f"  • 一致路径数: {path['consistent_paths']}/{path['total_paths']}")
        print(f"  • 一致性率: {path['consistency_rate']:.2%}")
        
        # 5. 综合评分
        print(f"\n【综合质量评分】")
        print(f"  ⭐ 综合得分: {metrics['overall_score']:.2%}")
        
        # 质量等级
        score = metrics['overall_score']
        if score >= 0.9:
            grade = "优秀 (Excellent)"
        elif score >= 0.8:
            grade = "良好 (Good)"
        elif score >= 0.7:
            grade = "中等 (Fair)"
        elif score >= 0.6:
            grade = "及格 (Pass)"
        else:
            grade = "需改进 (Needs Improvement)"
        
        print(f"  📊 质量等级: {grade}")
        print("="*60)


def evaluate_tree_quality(original_table: List[List[str]], 
                         tree_table: Dict[str, Any],
                         handle_combined_keys: bool = True) -> Dict[str, Any]:
    """
    便捷函数：评估树形表格质量
    
    Args:
        original_table: 原始表格
        tree_table: 树形表格
        handle_combined_keys: 是否处理组合键（如 "Header - Value"）
                            对于 LLM_based 方法应设置为 True（默认）
        
    Returns:
        评估指标字典
    """
    evaluator = TreeQualityEvaluator(handle_combined_keys=handle_combined_keys)
    return evaluator.evaluate(original_table, tree_table)


def batch_evaluate(table_tree_pairs: List[Tuple[List[List[str]], Dict[str, Any]]],
                  handle_combined_keys: bool = True) -> Dict[str, Any]:
    """
    批量评估多个表格-树对
    
    Args:
        table_tree_pairs: [(原始表格, 树形表格), ...]
        handle_combined_keys: 是否处理组合键（如 "Header - Value"）
        
    Returns:
        批量评估统计结果
    """
    evaluator = TreeQualityEvaluator(handle_combined_keys=handle_combined_keys)
    all_results = []
    
    for idx, (table, tree) in enumerate(table_tree_pairs):
        print(f"\n{'='*60}")
        print(f"评估第 {idx + 1}/{len(table_tree_pairs)} 个表格")
        print(f"{'='*60}")
        
        result = evaluator.evaluate(table, tree)
        all_results.append(result)
    
    # 计算平均指标
    avg_metrics = {
        "total_evaluated": len(all_results),
        "avg_coverage_rate": sum(r["coverage"]["coverage_rate"] for r in all_results) / len(all_results),
        "avg_positioning_accuracy": sum(r["positioning"]["positioning_accuracy"] for r in all_results) / len(all_results),
        "avg_consistency_rate": sum(r["path_consistency"]["consistency_rate"] for r in all_results) / len(all_results),
        "avg_overall_score": sum(r["overall_score"] for r in all_results) / len(all_results),
        "individual_results": all_results
    }
    
    print("\n" + "="*60)
    print("📊 批量评估汇总")
    print("="*60)
    print(f"评估样本数: {avg_metrics['total_evaluated']}")
    print(f"平均信息覆盖率: {avg_metrics['avg_coverage_rate']:.2%}")
    print(f"平均结构定位准确率: {avg_metrics['avg_positioning_accuracy']:.2%}")
    print(f"平均路径一致性: {avg_metrics['avg_consistency_rate']:.2%}")
    print(f"平均综合得分: {avg_metrics['avg_overall_score']:.2%}")
    print("="*60)
    
    return avg_metrics


if __name__ == "__main__":
    # 测试示例
    print("树形表格质量评测模块")
    print("可以通过导入此模块使用 evaluate_tree_quality() 函数")

