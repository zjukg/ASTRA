import requests
import json
import time
import sys

import openai
from openai import OpenAI
import time
import os
from urllib.request import getproxies
from pathlib import Path

# 加载 .env 文件
def load_env():
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()
# 清除所有的网络代理
# 清除所有代理环境变量
proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']
for var in proxy_vars:
    if var in os.environ:
        del os.environ[var]
        print(f"已清除环境变量: {var}")

# 设置requests库不使用代理
os.environ['no_proxy'] = '*'
os.environ['NO_PROXY'] = '*'

# 验证代理设置
print("当前系统代理设置:", getproxies())

# 为huggingface transformers设置不使用代理
os.environ['TRANSFORMERS_OFFLINE'] = '0'  # 允许在线下载，但不使用代理
class OpenaimodelClient :
    def __init__(self, model):
        if model == "deepseek-v3-250324" or model == "deepseek-r1-250120":
            print("volces")
            base_url = "https://ark.cn-beijing.volces.com/api/v3"
            api_key = os.environ.get("VOLCES_API_KEY", "")
        elif model == "deepseek-chat" or model ==  "deepseek-reasoner":
            print("deepseek")
            base_url = "https://api.deepseek.com"
            api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        elif model == "deepseek-v3" or model == "deepseek-v3.1" or model == "deepseek-v3.2-exp" or model == "deepseek-r1" or model == "deepseek-r1-0528":
            print("aliyun")
            base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            api_key = os.environ.get("ALIYUN_API_KEY", "")
        else:
            print("openai-compatible")
            base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
            api_key = os.environ.get("OPENAI_API_KEY", "")

        if not api_key:
            raise ValueError(f"API key not found for model {model}. Please set the appropriate environment variable in .env file.")

        client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.client = client
    def generate(self, prompt: str, max_length: int = 16384, temperature: float = 0.3, timeout: int = 30000):
        if "deepseek-chat" in self.model:
            max_length = 8192
        else:
            max_length = 16384
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_length,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
class ModelClient:
    def __init__(self, base_url: str = "http://localhost:8000"): # 默认 8000 现在部署了 8002为 Qwen2.5_14B
        self.base_url = base_url
        
    def test_generate(self, prompt: str, max_length: int = 100, temperature: float = 0.7, timeout: int = 300):
        """标准生成方法 - 可能超时"""
        print(f"🔥 标准生成 (timeout={timeout}s)")
        messages = [
            {"role": "system", "content": "你是一个专业的数据分析专家（Data Analyst），擅长处理和分析结构化表格数据。你的任务是根据用户提供的表格内容，准确回答用户的问题"},
            {"role": "user", "content": prompt}
        ]
        try:
            response = requests.post(
                f"{self.base_url}/generate",
                json={
                    "messages": messages,
                    "max_length": max_length,
                    "temperature": temperature
                },
                timeout=timeout  # 设置客户端超时
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 生成成功 (耗时: {result.get('generation_time', 'unknown')}s)")
                print(f"📝 结果: {result['generated_text'][:200]}...")
                if result.get('warning'):
                    print(f"⚠️  {result['warning']}")
                return result
            else:
                print(f"❌ 请求失败: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"❌ 请求超时 ({timeout}s)，建议使用流式生成")
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            
        return None
    
    def test_generate_stream(self, prompt: str, max_length: int = 8192, temperature: float = 0.3, timeout: int = 600, 
                           stop_on_json_repeat: bool = True, json_repeat_count: int = 2):
        """流式生成方法 - 避免超时，支持JSON重复检测停止"""
        print(f"🌊 流式生成 (timeout={timeout}s, stop_on_json_repeat={stop_on_json_repeat})")
        messages = [
            {"role": "system", "content": "你是一个专业的数据分析专家（Data Analyst），擅长处理和分析结构化表格数据。你的任务是根据用户提供的表格内容，准确回答用户的问题"},
            {"role": "user", "content": prompt}
        ]
        try:
            response = requests.post(
                f"{self.base_url}/generate_stream",
                json={
                    "messages": messages,
                    "max_length": max_length,
                    "temperature": temperature
                },
                stream=True,  # 启用流式接收
                timeout=timeout
            )
            
            if response.status_code == 200:
                print("✅ 开始流式接收:")
                full_text = ""
                start_time = time.time()
                json_code_block_count = 0  # 计数器，统计 ```json 的出现次数
                
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_str = line[6:]  # 移除 'data: ' 前缀
                            
                            if data_str == '[DONE]':
                                break
                                
                            try:
                                data = json.loads(data_str)
                                
                                if data['type'] == 'start':
                                    print(f"📝 开始生成，提示: {str(data['prompt'])[:100]}...")
                                    
                                elif data['type'] == 'chunk':
                                    # 实时打印生成的文本块
                                    print(data['text'], end='', flush=True)
                                    full_text = data['full_text']
                                    
                                    # 检测 ```json 的出现次数
                                    if stop_on_json_repeat:
                                        json_code_block_count += data['text'].count('```json')
                                        
                                        # 如果达到指定的重复次数，主动停止
                                        if json_code_block_count >= json_repeat_count:
                                            generation_time = time.time() - start_time
                                            print(f"\n🛑 检测到 ```json 出现 {json_code_block_count} 次，主动停止生成")
                                            print(f"✅ 生成完成 (耗时: {generation_time:.2f}s)")
                                            print(f"📊 总长度: {len(full_text)} 字符")
                                            return full_text
                                    
                                elif data['type'] == 'end':
                                    generation_time = time.time() - start_time
                                    print(f"\n✅ 生成完成 (耗时: {generation_time:.2f}s)")
                                    print(f"📊 总长度: {len(full_text)} 字符")
                                    return full_text
                                    
                                elif data['type'] == 'error':
                                    print(f"\n❌ 生成错误: {data['error']}")
                                    return None
                                    
                            except json.JSONDecodeError as e:
                                print(f"\n❌ JSON解析错误: {e}")
                                
            else:
                print(f"❌ 请求失败: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"❌ 流式请求也超时了 ({timeout}s)，请检查模型性能")
        except Exception as e:
            print(f"❌ 流式请求异常: {e}")
            
        return None
    
    def test_generate_stream_advanced(self, prompt: str, max_length: int = 2048, temperature: float = 0.3, timeout: int = 600, 
                                     stop_on_json_repeat: bool = True, json_repeat_count: int = 3):
        """高级流式生成方法 - 更精确的JSON代码块检测"""
        print(f"🌊 高级流式生成 (timeout={timeout}s, stop_on_json_repeat={stop_on_json_repeat})")
        
        try:
            response = requests.post(
                f"{self.base_url}/generate_stream",
                json={
                    "prompt": prompt,
                    "max_length": max_length,
                    "temperature": temperature
                },
                stream=True,  # 启用流式接收
                timeout=timeout
            )
            
            if response.status_code == 200:
                print("✅ 开始流式接收:")
                full_text = ""
                start_time = time.time()
                json_code_block_count = 0
                buffer = ""  # 缓冲区，用于处理跨chunk的模式匹配
                
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_str = line[6:]  # 移除 'data: ' 前缀
                            
                            if data_str == '[DONE]':
                                break
                                
                            try:
                                data = json.loads(data_str)
                                
                                if data['type'] == 'start':
                                    print(f"📝 开始生成，提示: {data['prompt']}...")
                                    
                                elif data['type'] == 'chunk':
                                    # 实时打印生成的文本块
                                    chunk_text = data['text']
                                    print(chunk_text, end='', flush=True)
                                    full_text = data['full_text']
                                    
                                    # 高级JSON代码块检测
                                    if stop_on_json_repeat:
                                        # 将当前chunk加入缓冲区
                                        buffer += chunk_text
                                        
                                        # 保持缓冲区大小合理，只保留最后20个字符用于模式匹配
                                        if len(buffer) > 20:
                                            buffer = buffer[-20:]
                                        
                                        # 在完整文本中计算```json的出现次数（更准确）
                                        import re
                                        json_blocks = re.findall(r'```json', full_text)
                                        json_code_block_count = len(json_blocks)
                                        
                                        # 如果达到指定的重复次数，主动停止
                                        if json_code_block_count >= json_repeat_count:
                                            generation_time = time.time() - start_time
                                            print(f"\n🛑 检测到 ```json 代码块出现 {json_code_block_count} 次，主动停止生成")
                                            print(f"✅ 生成完成 (耗时: {generation_time:.2f}s)")
                                            print(f"📊 总长度: {len(full_text)} 字符")
                                            
                                            # 尝试清理输出，移除最后一个不完整的重复部分
                                            cleaned_text = self._clean_repeated_json_output(full_text, json_repeat_count)
                                            return cleaned_text
                                    
                                elif data['type'] == 'end':
                                    generation_time = time.time() - start_time
                                    print(f"\n✅ 生成完成 (耗时: {generation_time:.2f}s)")
                                    print(f"📊 总长度: {len(full_text)} 字符")
                                    return full_text
                                    
                                elif data['type'] == 'error':
                                    print(f"\n❌ 生成错误: {data['error']}")
                                    return None
                                    
                            except json.JSONDecodeError as e:
                                print(f"\n❌ JSON解析错误: {e}")
                                
            else:
                print(f"❌ 请求失败: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"❌ 流式请求也超时了 ({timeout}s)，请检查模型性能")
        except Exception as e:
            print(f"❌ 流式请求异常: {e}")
    def _clean_repeated_json_output(self, text: str, max_json_blocks: int = 2):
        """清理重复的JSON输出，只保留前N个JSON代码块"""
        import re
        
        # 找到所有```json代码块的位置
        json_block_starts = []
        for match in re.finditer(r'```json', text):
            json_block_starts.append(match.start())
        
        if len(json_block_starts) <= max_json_blocks:
            return text
        
        # 找到第max_json_blocks个```json之后的位置，并截断
        cutoff_position = json_block_starts[max_json_blocks - 1]
        
        # 寻找这个JSON代码块的结束位置
        remaining_text = text[cutoff_position:]
        end_match = re.search(r'```\s*$|```\s+', remaining_text)
        
        if end_match:
            final_cutoff = cutoff_position + end_match.end()
            cleaned_text = text[:final_cutoff]
            print(f"🧹 清理后的文本长度: {len(cleaned_text)} (原长度: {len(text)})")
            return cleaned_text
        else:
            # 如果找不到结束标记，找到下一个```json开始之前的位置
            next_json_start = json_block_starts[max_json_blocks] if len(json_block_starts) > max_json_blocks else len(text)
            cleaned_text = text[:next_json_start].rstrip()
            print(f"🧹 清理后的文本长度: {len(cleaned_text)} (原长度: {len(text)})")
            return cleaned_text    
        return None
    
