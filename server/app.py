import time
import asyncio
import uvicorn
import gradio as gr
import os
import sys
import json
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder

# Ensure root imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.environment import LLMDebugEnv
from models import DebugAction

# --- GLOBAL STATE ---
env = LLMDebugEnv()
activity_logs = []
current_ui_state = {
    "task": "Waiting for Agent to connect...",
    "initial_code": "# Original buggy code will appear here...",
    "current_code": "# AI's live edits will appear here..."
}

def add_log(message: str):
    timestamp = time.strftime("%H:%M:%S")
    activity_logs.append(f"[{timestamp}] {message}")
    if len(activity_logs) > 20: 
        activity_logs.pop(0)

def update_ui_state(obs, is_reset=False):
    data = obs.model_dump() if hasattr(obs, "model_dump") else (obs if isinstance(obs, dict) else vars(obs))
    metadata = data.get("metadata", {}) or {}

    task_text = metadata.get("task")
    extracted_code = metadata.get("code")

    if is_reset and not task_text:
        feedback_str = str(data.get("feedback", ""))
        if "TASK:" in feedback_str and "CODE:" in feedback_str:
            parts = feedback_str.split("CODE:")
            task_text = parts[0].replace("TASK:", "").strip()
            extracted_code = parts[1].strip()

    if task_text: current_ui_state["task"] = str(task_text)
    if extracted_code:
        if is_reset: current_ui_state["initial_code"] = str(extracted_code)
        current_ui_state["current_code"] = str(extracted_code)

def parse_env_step(raw_result):
    if isinstance(raw_result, tuple):
        obs, reward, done, info = raw_result[:4]
    else:
        obs = raw_result
        passed = getattr(obs, "test_passed", False)
        reward = getattr(obs, "reward", 1.0 if passed else 0.0)
        done = getattr(obs, "done", passed)
        info = {}
    return obs, float(reward), bool(done), info

# --- FASTAPI SETUP ---
app = FastAPI(title="LLM Debug Gym Server")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    add_log("🔌 Agent connected via WebSocket.")
    
    def find_task_id(d):
        if isinstance(d, dict):
            if "task_id" in d: return d["task_id"]
            for v in d.values():
                res = find_task_id(v)
                if res: return res
        return None

    try:
        while True:
            try:
                request = await websocket.receive_json()
                req_type = request.get("type", "unknown")
                
                if req_type == "handshake":
                    await websocket.send_json({"type": "handshake", "data": {"status": "connected"}})
                
                elif req_type == "reset":
                    req_task_id = find_task_id(request) or os.environ.get("TASK_ID")
                    
                    if not req_task_id:
                        raise ValueError("No TASK_ID found in client payload.")
                        
                    add_log(f"🔄 Resetting to: {req_task_id}")
                    obs = env.reset(options={"task_id": req_task_id})
                    update_ui_state(obs, is_reset=True)
                    await asyncio.sleep(2)
                    
                    await websocket.send_json({
                        "type": "reset",
                        "data": {
                            "observation": jsonable_encoder(obs),
                            "reward": 0.1,
                            "done": False,
                            "info": {"task_id": env.current_task_id}
                        }
                    })

                elif req_type == "step":
                    action_data = request.get("data", request)
                    action = DebugAction(**action_data)
                    add_log(f"🤖 AI Action: {action.command}")
                    
                    if action.command == "WRITE":
                        current_ui_state["current_code"] = action.content.strip()
                        await asyncio.sleep(1.5)
                    
                    raw_result = env.step(action)
                    obs, reward, done, info = parse_env_step(raw_result)
                    update_ui_state(obs, is_reset=False)
                    
                    if action.command == "TEST":
                        test_passed = getattr(obs, "test_passed", False)
                        if test_passed:
                            status = "✅ SUCCESS"
                        elif reward > 0.2:
                            status = "🔄 PARTIAL"
                        else:
                            status = "❌ FAILED"
                        add_log(f"📊 Result: {status} | Reward: {reward:.2f}")

                    if getattr(obs, "test_passed", False) and "✅ TASK IS SUCCESSFUL" not in current_ui_state["task"]:
                        current_ui_state["task"] = f"✅ TASK IS SUCCESSFUL!\n\n---\n\n{current_ui_state['task']}"

                    await websocket.send_json({
                        "type": "step",
                        "data": {"observation": jsonable_encoder(obs), "reward": reward, "done": done, "info": jsonable_encoder(info)}
                    })
                    
            except WebSocketDisconnect:
                raise
            except Exception as inner_e:
                add_log(f"⚠️ Action Error: {inner_e}")
                try:
                    await websocket.send_json({"type": "error", "error": str(inner_e)})
                except:
                    pass 
                    
    except WebSocketDisconnect:
        add_log("🔌 Agent disconnected (Moving to next task or finished).")
    except Exception as e:
        add_log(f"⚠️ Critical WS Error: {str(e)}")

@app.post("/reset")
async def reset(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        payload = {}
    
    def find_task_id(d):
        if isinstance(d, dict):
            if "task_id" in d: return d["task_id"]
            for v in d.values():
                res = find_task_id(v)
                if res: return res
        return None
        
    t_id = find_task_id(payload)
    
    # --- FALLBACK TASK ID LOGIC ---
    if not t_id:
        # IMPORTANT: Replace the string below with a valid task ID from your environment
        t_id = os.environ.get("TASK_ID", "task_easy")
        
    obs = env.reset(options={"task_id": t_id})
    update_ui_state(obs, is_reset=True)
    return {"observation": jsonable_encoder(obs), "reward": 0.1, "done": False, "info": {"task_id": env.current_task_id}}

@app.post("/step")
async def step(request: Request):
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        payload = {}
        
    action = DebugAction(**payload)
    if action.command == "WRITE":
        current_ui_state["current_code"] = action.content.strip()
    
    raw_result = env.step(action)
    obs, reward, done, info = parse_env_step(raw_result)
    update_ui_state(obs, is_reset=False)
    
    if getattr(obs, "test_passed", False) and "✅ TASK IS SUCCESSFUL" not in current_ui_state["task"]:
        current_ui_state["task"] = f"✅ TASK IS SUCCESSFUL!\n\n---\n\n{current_ui_state['task']}"
        
    return {"observation": jsonable_encoder(obs), "reward": reward, "done": done, "info": jsonable_encoder(info)}

# --- GRADIO UI ---
with gr.Blocks(title="LLM Debug Gym") as demo:
    gr.Markdown("# 🤖 LLM Debug Gym - Live Monitor")
    
    with gr.Row():
        with gr.Column(scale=2):
            task_display = gr.Textbox(label="Current Task Description", interactive=False)
            with gr.Row():
                initial_code_display = gr.Code(label="Original Buggy Code", language="python", interactive=False)
                live_code_display = gr.Code(label="AI's Live Code State", language="python", interactive=False)
        with gr.Column(scale=1):
            log_viewer = gr.Textbox(label="Real-time Logs", lines=20, interactive=False)

    demo.queue() 
    
    def refresh_ui():
        return current_ui_state["task"], current_ui_state["initial_code"], current_ui_state["current_code"], "\n".join(reversed(activity_logs))
    
    refresh_timer = gr.Timer(1.0)
    refresh_timer.tick(refresh_ui, outputs=[task_display, initial_code_display, live_code_display, log_viewer])
    demo.load(refresh_ui, outputs=[task_display, initial_code_display, live_code_display, log_viewer])

demo.theme = gr.themes.Soft()
app = gr.mount_gradio_app(app, demo, path="/")

def main():
    uvicorn.run("server.app:app", host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
