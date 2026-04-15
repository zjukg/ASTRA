export interface StepMessage {
  stage: string;
  status: 'running' | 'completed' | 'failed' | 'in_progress';
  data: Record<string, any> | null;
}

export interface NavigationStep {
  step: number;
  current_node: string;
  current_path: string[];
  available_children: string[];
  selected_children: string[];
  rejected_children: string[];
}

export interface PathDetail {
  path: string[];
  data: any;
}

export interface TopKNode {
  path: string;
  key: string;
  score: number;
}

export interface TreeNode {
  name: string;
  children?: TreeNode[];
  value?: any;
  isLeaf?: boolean;
  highlight?: 'selected' | 'rejected' | 'current' | 'evidence' | 'embedding' | null;
}

export interface SessionConfig {
  model_name: string;
  model_type: string;
  api_key: string;
  base_url: string;
  temperature: number;
  tree_mode: string;
  using_embedding: boolean;
  embedding_model_name: string;
  embedding_api_key: string;
  embedding_base_url: string;
}
