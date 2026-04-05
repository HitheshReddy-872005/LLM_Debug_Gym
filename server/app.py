import time
import asyncio
import uvicorn
import gradio as gr
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder

# Internal imports based on your project structure
from server.environment import LLMDebugEnv
from models import DebugAction

# --- GLOBAL STATE ---
env = LLMDebugEnv()
activity_logs = []

# Global state for the Gradio UI polling
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

# --- THE DEEP EXTRACTION & STRING SPLITTER LOGIC ---
def update_ui_state(obs, is_reset=False):
    """Unpacks models and extracts bundled task/code strings."""
    
    # 1. Convert to dictionary
    if hasattr(obs, "model_dump"):
        data = obs.model_dump()
    elif hasattr(obs, "dict"):
        data = obs.dict()
    elif isinstance(obs, dict):
        data = obs
    else:
        try:
            data = vars(obs)
        except:
            data = {}

    metadata = data.get("metadata", {}) or {}

    task_text = None
    extracted_code = data.get("code") or metadata.get("code")

    # 2. Check standard keys first
    for key in ["task", "instruction", "description", "prompt", "challenge"]:
        if data.get(key): task_text = data.get(key)
        elif metadata.get(key): task_text = metadata.get(key)

    # 3. Handle bundled "TASK:" and "CODE:" strings on reset
    if is_reset:
        feedback_str = str(data.get("feedback", ""))
        
        # If the environment combines them into one string:
        if "TASK:" in feedback_str and "CODE:" in feedback_str:
            parts = feedback_str.split("CODE:")
            task_text = parts[0].replace("TASK:", "").strip()
            extracted_code = parts[1].strip()
            
        elif not task_text and feedback_str:
            task_text = feedback_str

    # 4. Only overwrite task if new one found, or if reset failed to find one
    if task_text:
        current_ui_state["task"] = str(task_text)
    elif is_reset:
        current_ui_state["task"] = f"⚠️ Task hidden. Data keys: {list(data.keys())}"

    # 5. Only update initial code on reset
    if extracted_code:
        if is_reset:
            current_ui_state["initial_code"] = str(extracted_code)
        current_ui_state["current_code"] = str(extracted_code)


# --- UNIVERSAL STEP PARSER ---
def parse_env_step(step_result):
    if isinstance(step_result, tuple):
        if len(step_result) >= 5:
            obs, reward, term, trunc, info = step_result[:5]
            return obs, float(reward), bool(term or trunc), info
        elif len(step_result) == 4:
            obs, reward, done, info = step_result
            return obs, float(reward), bool(done), info
            
    elif isinstance(step_result, dict):
        obs = step_result.get("observation", step_result)
        passed = step_result.get("test_passed", False)
        reward = step_result.get("reward", 1.0 if passed else 0.0)
        done = step_result.get("done", passed)
        return obs, float(reward), bool(done), step_result.get("info", {})
    
    obs = step_result
    passed = getattr(obs, "test_passed", False)
    reward = getattr(obs, "reward", 1.0 if passed else 0.0)
    done = getattr(obs, "done", passed)
    return obs, float(reward), bool(done), {}

# --- FASTAPI SETUP ---
app = FastAPI(title="LLM Debug Gym Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- OPENENV PROTOCOL WEBSOCKET HANDLER ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    add_log("🔌 Agent connected via WebSocket.")
    try:
        while True:
            request = await websocket.receive_json()
            req_type = request.get("type", "unknown")
            add_log(f"📥 Protocol Action: {req_type}")
            
            if req_type == "handshake":
                await websocket.send_json({
                    "type": "handshake", 
                    "data": {"status": "connected"}
                })
            
            elif req_type == "reset":
                add_log("🔄 Environment Reset initiated by Agent.")
                obs = env.reset()
                update_ui_state(obs, is_reset=True)
                
                # ⏳ PAUSE 1: Give user time to read the new task
                await asyncio.sleep(2)
                
                await websocket.send_json({
                    "type": "reset",
                    "data": {
                        "observation": jsonable_encoder(obs),
                        "reward": 0.0,
                        "done": False,
                        "info": {}
                    }
                })
            
            elif req_type == "step":
                action_data = request.get("data", {})
                action = DebugAction(**action_data)
                add_log(f"🤖 AI Action: {action.command}")
                
                if action.command == "WRITE":
                    snippet = action.content.strip()[:50].replace("\n", " ")
                    add_log(f"📝 Writing Code: {snippet}...")
                    current_ui_state["current_code"] = action.content.strip()
                    
                    # ⏳ PAUSE 2: Give user time to read the AI's code edits
                    await asyncio.sleep(3)
                    
                raw_result = env.step(action)
                obs, reward, done, info = parse_env_step(raw_result)
                update_ui_state(obs, is_reset=False)

                status = "✅ SUCCESS" if reward > 0 else "❌ FAILED"
                add_log(f"📊 Result: {status} | Reward: {reward}")
                
                # The Victory Banner
                if reward > 0:
                    current_ui_state["task"] = f"✅ TASK IS SUCCESSFUL! The AI solved the challenge.\n\n---\n\n{current_ui_state['task']}"
                
                await websocket.send_json({
                    "type": "step",
                    "data": {
                        "observation": jsonable_encoder(obs),
                        "reward": reward,
                        "done": done,
                        "info": jsonable_encoder(info)
                    }
                })
                
            else:
                await websocket.send_json({
                    "type": req_type,
                    "data": {"status": "ok"}
                })
                
    except WebSocketDisconnect:
        add_log("🔌 Agent disconnected.")
    except Exception as e:
        add_log(f"⚠️ WS Error: {str(e)}")


# --- REST API ENDPOINTS ---
@app.post("/reset")
async def reset():
    add_log("🔄 REST Environment Reset.")
    obs = env.reset()
    update_ui_state(obs, is_reset=True)
    return {"observation": jsonable_encoder(obs), "reward": 0.0, "done": False}

@app.post("/step")
async def step(request: Request):
    payload = await request.json()
    action = DebugAction(**payload)
    if action.command == "WRITE":
        current_ui_state["current_code"] = action.content.strip()
        
    raw_result = env.step(action)
    obs, reward, done, info = parse_env_step(raw_result)
    update_ui_state(obs, is_reset=False)
    
    if reward > 0:
        current_ui_state["task"] = f"✅ TASK IS SUCCESSFUL! The AI solved the challenge.\n\n---\n\n{current_ui_state['task']}"
        
    return {"observation": jsonable_encoder(obs), "reward": reward, "done": done, "info": jsonable_encoder(info)}


# --- GRADIO FRONTEND ---
def get_live_logs():
    if not activity_logs:
        return "Waiting for Agent activity..."
    return "\n".join(reversed(activity_logs))

def get_current_task():
    return current_ui_state["task"]

def get_initial_code():
    return current_ui_state["initial_code"]

def get_current_code():
    return current_ui_state["current_code"]

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🤖 LLM Debug Gym - Live Monitor")
    
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### 🖥️ Task Environment")
            task_display = gr.Textbox(
                label="Current Task Description", 
                value=get_current_task, 
                every=1, 
                interactive=False
            )
            
            with gr.Row():
                initial_code_display = gr.Code(
                    label="Original Buggy Code", 
                    language="python", 
                    value=get_initial_code, 
                    every=1, 
                    interactive=False
                )
                live_code_display = gr.Code(
                    label="AI's Live Code State", 
                    language="python", 
                    value=get_current_code, 
                    every=1, 
                    interactive=False
                )
            
            with gr.Row():
                reset_btn = gr.Button("Manual Reset", variant="secondary")

        with gr.Column(scale=1):
            gr.Markdown("### 📡 Live Agent Activity")
            log_viewer = gr.Textbox(
                label="Real-time Logs",
                value=get_live_logs,
                every=1,
                lines=20,
                interactive=False
            )
            
    def ui_reset():
        obs = env.reset()
        activity_logs.clear()
        add_log("🔄 Manual Reset from Web UI.")
        update_ui_state(obs, is_reset=True)

    reset_btn.click(ui_reset)

app = gr.mount_gradio_app(app, demo, path="/")

def main():
    uvicorn.run("server.app:app", host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()