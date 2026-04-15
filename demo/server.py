"""
ASTRA Demo Server - FastAPI backend with REST and WebSocket endpoints.
"""
import sys
import os
import json
import asyncio
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline_wrapper import preprocess_upload, build_tree_stepwise, DemoTreeQA


class SessionState:
    """Holds the current session state (table, tree, QA engine)."""
    def __init__(self):
        self.table = None
        self.sheet = None
        self.tree_table = None
        self.model_name = os.environ.get("ASTRA_MODEL_NAME", "deepseek-v3-250324")
        self.model_type = "oai"
        self.api_key = os.environ.get("ASTRA_API_KEY", "")
        self.base_url = os.environ.get("ASTRA_BASE_URL", "")
        self.temperature = 0.3
        self.tree_mode = "normal"
        self.using_embedding = False
        self.embedding_model_name = ""
        self.embedding_api_key = ""
        self.embedding_base_url = ""
        self.qa_engine = None

session = SessionState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("ASTRA Demo Server starting...")
    yield
    print("ASTRA Demo Server shutting down...")

app = FastAPI(title="ASTRA Demo", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConfigUpdate(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_name: Optional[str] = None
    model_type: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: Optional[float] = None
    tree_mode: Optional[str] = None
    using_embedding: Optional[bool] = None
    embedding_model_name: Optional[str] = None
    embedding_api_key: Optional[str] = None
    embedding_base_url: Optional[str] = None


@app.get("/api/config")
async def get_config():
    return {
        "model_name": session.model_name,
        "model_type": session.model_type,
        "api_key": session.api_key,
        "base_url": session.base_url,
        "temperature": session.temperature,
        "tree_mode": session.tree_mode,
        "using_embedding": session.using_embedding,
        "embedding_model_name": session.embedding_model_name,
        "embedding_api_key": session.embedding_api_key,
        "embedding_base_url": session.embedding_base_url,
    }


@app.post("/api/config")
async def update_config(config: ConfigUpdate):
    if config.model_name is not None:
        session.model_name = config.model_name
    if config.model_type is not None:
        session.model_type = config.model_type
    if config.api_key is not None:
        session.api_key = config.api_key
    if config.base_url is not None:
        session.base_url = config.base_url
    if config.temperature is not None:
        session.temperature = config.temperature
    if config.tree_mode is not None:
        session.tree_mode = config.tree_mode
    if config.using_embedding is not None:
        session.using_embedding = config.using_embedding
    if config.embedding_model_name is not None:
        session.embedding_model_name = config.embedding_model_name
    if config.embedding_api_key is not None:
        session.embedding_api_key = config.embedding_api_key
    if config.embedding_base_url is not None:
        session.embedding_base_url = config.embedding_base_url
    return {"status": "ok"}


@app.post("/api/upload")
async def upload_table(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        table, sheet = preprocess_upload(file_bytes, file.filename)
        session.table = table
        session.sheet = sheet
        session.tree_table = None
        
        return {
            "status": "ok",
            "filename": file.filename,
            "table": table,
            "rows": len(table),
            "cols": len(table[0]) if table else 0,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/upload-text")
async def upload_table_text(payload: dict):
    """Accept table as JSON text (for pasting list-of-lists or markdown)."""
    try:
        format_type = payload.get("format", "json")
        content = payload.get("content", "")
        
        if format_type == "json":
            data = json.loads(content)
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                table = data
            elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                headers = list(data[0].keys())
                table = [headers] + [[row.get(h, '') for h in headers] for row in data]
            else:
                table = data
        elif format_type == "markdown":
            from pipeline_wrapper import parse_markdown_table
            table = parse_markdown_table(content)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        session.table = table
        session.sheet = None
        session.tree_table = None
        
        return {
            "status": "ok",
            "table": table,
            "rows": len(table),
            "cols": len(table[0]) if table else 0,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/session")
async def get_session():
    return {
        "has_table": session.table is not None,
        "has_tree": session.tree_table is not None,
        "table_shape": [len(session.table), len(session.table[0])] if session.table else None,
        "table": session.table,
        "tree_table": make_json_serializable(session.tree_table) if session.tree_table else None,
    }


def make_json_serializable(obj):
    """Recursively convert non-serializable types."""
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(v) for v in obj]
    elif isinstance(obj, (int, float, str, bool)) or obj is None:
        return obj
    else:
        return str(obj)


@app.websocket("/ws/build-tree")
async def ws_build_tree(websocket: WebSocket):
    await websocket.accept()
    try:
        config_msg = await websocket.receive_text()
        config = json.loads(config_msg)
        
        model_name = config.get("model_name", session.model_name)
        model_type = config.get("model_type", session.model_type)
        api_key = config.get("api_key", session.api_key)
        base_url = config.get("base_url", session.base_url)
        temperature = config.get("temperature", session.temperature)
        tree_mode = config.get("tree_mode", session.tree_mode)
        
        if session.table is None:
            await websocket.send_json({"stage": "error", "status": "failed", "data": {"error": "No table uploaded"}})
            await websocket.close()
            return
        
        table = session.table
        sheet = session.sheet
        
        for step in build_tree_stepwise(table, sheet, model_name, temperature, model_type, tree_mode,
                                        api_key=api_key, base_url=base_url):
            serializable_step = make_json_serializable(step)
            await websocket.send_json(serializable_step)
            
            if step.get("stage") == "tree_construction" and step.get("status") == "completed":
                session.tree_table = step["data"]["tree_table"]
            
            await asyncio.sleep(0.05)
        
        await websocket.send_json({"stage": "done", "status": "completed", "data": None})
        
    except WebSocketDisconnect:
        print("Client disconnected from build-tree")
    except Exception as e:
        try:
            await websocket.send_json({"stage": "error", "status": "failed", "data": {"error": str(e)}})
        except:
            pass


@app.websocket("/ws/qa")
async def ws_qa(websocket: WebSocket):
    await websocket.accept()
    try:
        config_msg = await websocket.receive_text()
        config = json.loads(config_msg)
        
        question = config.get("question", "")
        model_name = config.get("model_name", session.model_name)
        model_type = config.get("model_type", session.model_type)
        api_key = config.get("api_key", session.api_key)
        base_url = config.get("base_url", session.base_url)
        using_embedding = config.get("using_embedding", session.using_embedding)
        embedding_model_name = config.get("embedding_model_name", session.embedding_model_name)
        embedding_api_key = config.get("embedding_api_key", session.embedding_api_key) or api_key
        embedding_base_url = config.get("embedding_base_url", session.embedding_base_url) or base_url
        enable_symbolic = config.get("enable_symbolic", True)
        
        if session.tree_table is None:
            await websocket.send_json({"stage": "error", "status": "failed", "data": {"error": "No tree built yet"}})
            await websocket.close()
            return
        
        if not session.qa_engine or session.qa_engine.tree_qa.model_name != model_name:
            session.qa_engine = DemoTreeQA(
                model_type=model_type,
                model_name=model_name,
                api_key=api_key,
                base_url=base_url,
                using_embedding=using_embedding,
                embedding_model_name=embedding_model_name,
                embedding_api_key=embedding_api_key,
                embedding_base_url=embedding_base_url,
            )
        
        for step in session.qa_engine.qa_stepwise(
            session.tree_table, session.table, question
        ):
            serializable_step = make_json_serializable(step)
            await websocket.send_json(serializable_step)
            await asyncio.sleep(0.05)
        
        if enable_symbolic:
            for step in session.qa_engine.symbolic_qa_stepwise(
                session.tree_table, question
            ):
                serializable_step = make_json_serializable(step)
                await websocket.send_json(serializable_step)
                await asyncio.sleep(0.05)
        
        await websocket.send_json({"stage": "done", "status": "completed", "data": None})
        
    except WebSocketDisconnect:
        print("Client disconnected from qa")
    except Exception as e:
        try:
            await websocket.send_json({"stage": "error", "status": "failed", "data": {"error": str(e)}})
        except:
            pass


dist_dir = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.isdir(dist_dir):
    from fastapi.responses import FileResponse

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(dist_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_dir, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
