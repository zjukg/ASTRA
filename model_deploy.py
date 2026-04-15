import os

import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
from pydantic import BaseModel
import argparse
from threading import Thread
import time


class MultiGPUModelService:
    """多GPU模型服务"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device_map = None
        self.enable_thinking = True
    
    def load_model(self, model_path: str, model_name: str, use_multi_gpu: bool = True, gpu_id: int = 0):
        """加载模型到GPU
        
        Args:
            model_path: 模型路径
            model_name: 模型名称
            use_multi_gpu: 是否使用多GPU，默认True
            gpu_id: 单GPU模式下使用的GPU ID，默认0
        """
        
        print(f"🚀 开始加载模型: {model_name}")
        self.show_gpu_info()
        
        try:
            # 加载分词器
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path, 
                trust_remote_code=True
            )
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # 根据配置选择加载方式
            if use_multi_gpu:
                print("📊 使用多GPU模式")
                # 计算每个GPU的最大内存使用
                num_gpus = torch.cuda.device_count()
                max_memory_per_gpu = "35GiB"
                max_memory = {i: max_memory_per_gpu for i in range(num_gpus)}
                
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    device_map="auto",
                    max_memory=max_memory,
                    torch_dtype=torch.float16,
                    trust_remote_code=True,
                    offload_folder="./offload",
                    offload_state_dict=True,
                    low_cpu_mem_usage=True
                )
            else:
                print(f"🎯 使用单GPU模式 (GPU {gpu_id})")
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    device_map=f"cuda:{gpu_id}",  # 指定单个GPU
                    torch_dtype=torch.float16,
                    trust_remote_code=True,
                    low_cpu_mem_usage=True
                )
            
            self.model.eval()
            self.device_map = getattr(self.model, 'hf_device_map', None)
            
            print("✅ 模型加载完成")
            self.show_model_distribution()
            self.show_gpu_info()
            
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            raise e
    
    def show_gpu_info(self):
        """显示GPU信息"""
        if torch.cuda.is_available():
            print("🖥️  GPU状态:")
            for i in range(torch.cuda.device_count()):
                allocated = torch.cuda.memory_allocated(i) / 1024**3
                cached = torch.cuda.memory_reserved(i) / 1024**3
                total = torch.cuda.get_device_properties(i).total_memory / 1024**3
                print(f"  GPU {i}: {allocated:.1f}GB / {total:.1f}GB (已分配/总容量)")
    
    def show_model_distribution(self):
        """显示模型分布"""
        if self.device_map:
            print("📊 模型层分布:")
            device_count = {}
            for layer, device in self.device_map.items():
                device_count[device] = device_count.get(device, 0) + 1
            
            for device, count in device_count.items():
                print(f"  {device}: {count} 层")
    def generate(self, messages, max_length: int = 100, temperature: float = 0.7):
        try:
            # 应用聊天模板并编码输入
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            # Tokenize 输入
            inputs = self.tokenizer(text, return_tensors="pt")
            
            # 将输入移动到第一个设备（通常是cuda:0）
            first_device = next(iter(self.model.parameters())).device
            inputs = {k: v.to(first_device) for k, v in inputs.items()}

            # 标准模式：平衡质量和速度
            generation_kwargs = {
                "max_length": max_length,
                "temperature": temperature,
                "top_p": 0.95,
                "repetition_penalty": 1.1
            }
            generation_kwargs.update(inputs)
            
            # 生成
            with torch.no_grad():
                outputs = self.model.generate(**generation_kwargs)
            
            # 解码输出
            generated_text = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
            return generated_text
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")
    def generate_stream(self, messages, max_length: int = 16384, temperature: float = 0.7):
        """流式生成文本"""
        try:
            # 应用聊天模板并编码输入
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
                # enable_thinking=False
            )
            
            # Tokenize 输入
            inputs = self.tokenizer(text, return_tensors="pt")
            
            # 将输入移动到第一个设备
            first_device = next(iter(self.model.parameters())).device
            inputs = {k: v.to(first_device) for k, v in inputs.items()}
            
            # 创建流式生成器
            streamer = TextIteratorStreamer(
                self.tokenizer, 
                timeout=60.0, 
                skip_prompt=True, 
                skip_special_tokens=True
            )
            
            # 生成参数
            generation_kwargs = dict(
                **inputs,
                streamer=streamer,
                max_length=max_length,
                temperature=temperature,
                repetition_penalty=1.2,
                top_p=0.95,
            )
            
            # 在单独线程中生成
            thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
            thread.start()
            
            # 流式返回结果
            for new_text in streamer:
                if new_text:
                    yield new_text
                    
        except Exception as e:
            yield f"流式生成失败: {str(e)}"
model_service = MultiGPUModelService()
import json
# FastAPI应用
app = FastAPI(title="多GPU模型部署服务", version="1.0.0")

class TextInput(BaseModel):
    messages: list[dict]
    max_length: int = 100
    temperature: float = 0.7

class StreamTextInput(BaseModel):
    messages: list[dict]
    max_length: int = 100
    temperature: float = 0.7

@app.get("/")
def read_root():
    return {"message": "多GPU模型服务运行中"}

@app.get("/gpu_status")
def get_gpu_status():
    """获取GPU状态"""
    if not torch.cuda.is_available():
        return {"error": "CUDA不可用"}
    
    gpu_info = []
    for i in range(torch.cuda.device_count()):
        allocated = torch.cuda.memory_allocated(i) / 1024**3
        total = torch.cuda.get_device_properties(i).total_memory / 1024**3
        gpu_info.append({
            "gpu_id": i,
            "name": torch.cuda.get_device_name(i),
            "allocated_gb": round(allocated, 2),
            "total_gb": round(total, 2),
            "usage_percent": round(allocated / total * 100, 1)
        })
    
    return {"gpus": gpu_info, "device_map": model_service.device_map}

@app.post("/generate")
async def generate_text(text_input: TextInput):
    """生成文本（非流式）- 推荐使用 /generate_stream 避免超时"""
    if model_service.model is None:
        raise HTTPException(status_code=503, detail="模型未加载")
    
    # 对于大输入或大max_length的警告
    if len(text_input.messages) > 1000 or text_input.max_length > 500:
        print(f"⚠️  警告：大输入({len(text_input.messages)}字符)或大max_length({text_input.max_length})可能导致超时，建议使用 /generate_stream")
    
    try:
        start_time = time.time()
        generated_text = model_service.generate(
            text_input.messages,
            text_input.max_length,
            text_input.temperature,
        )
        generation_time = time.time() - start_time
        
        return JSONResponse({
            "prompt": text_input.messages,
            "generated_text": generated_text,
            "generation_time": round(generation_time, 2),
            "warning": "如遇超时，请使用 /generate_stream 端点" if generation_time > 25 else None
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_stream")
async def generate_text_stream(text_input: StreamTextInput):
    """流式生成文本 - 避免超时的推荐方法"""
    if model_service.model is None:
        raise HTTPException(status_code=503, detail="模型未加载")
    
    def generate():
        try:
            # 发送开始标记
            yield f"data: {json.dumps({'type': 'start', 'prompt': text_input.messages})}\n\n"
            
            # 流式生成
            full_text = ""
            for chunk in model_service.generate_stream(
                text_input.messages,
                text_input.max_length,
                text_input.temperature
            ):
                full_text += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'text': chunk, 'full_text': full_text})}\n\n"
            
            # 发送结束标记
            yield f"data: {json.dumps({'type': 'end', 'full_text': full_text})}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/plain; charset=utf-8",
        }
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default="Qwen2.5-7B-Instruct")
    parser.add_argument("--model_path", type=str, default="", help="Local model path.")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8002)
    parser.add_argument("--multi_gpu", default=False, help="使用多GPU模式")
    parser.add_argument("--gpu_id", type=int, default=1, help="单GPU模式下使用的GPU ID")
    args = parser.parse_args()
    
    env_key = f"ASTRA_MODEL_PATH_{args.model_name.upper().replace('.', '_').replace('-', '_')}"
    model_path = args.model_path or os.environ.get(env_key) or os.environ.get("ASTRA_MODEL_PATH", "")
    if not model_path:
        raise ValueError(
            "No local model path configured. Pass --model_path or set "
            f"{env_key} / ASTRA_MODEL_PATH."
        )
    
    # 加载模型
    model_service.load_model(
        model_path,
        args.model_name,
        use_multi_gpu=args.multi_gpu,
        gpu_id=args.gpu_id
    )
    
    # 启动服务（增加超时配置）
    import uvicorn
    print(f"🚀 启动服务: http://{args.host}:{args.port}")
    print("📚 API端点:")
    print("  - /generate        - 标准生成（可能超时）")
    print("  - /generate_stream - 流式生成（推荐，避免超时）")
    print("  - /gpu_status      - GPU状态监控")
    
    # 配置更长的超时时间
    uvicorn.run(
        app, 
        host=args.host, 
        port=args.port,
        timeout_keep_alive=300,  # Keep-alive 超时：5分钟
        timeout_graceful_shutdown=60,  # 优雅关闭超时：1分钟
        limit_max_requests=1000,  # 最大请求数
        limit_concurrency=10,     # 并发限制
        access_log=True
    )
