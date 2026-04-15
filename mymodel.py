import requests
import json
import time
import sys

import openai
from openai import OpenAI
import time
import os
from urllib.request import getproxies
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
    def __init__(self, model, api_key="", base_url=""):
        self.model = model
        self.client = OpenAI(base_url=base_url, api_key=api_key)
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
    def __init__(self, base_url: str = "http://localhost:8002"): # 默认 8000 qwen3 现在部署了 8002为 Qwen2.5_14B
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
        
