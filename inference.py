import asyncio
import os
import re
import sys
import time
from dotenv import load_dotenv
from openai import OpenAI
from openenv.core.env_client import EnvClient
from openenv.core import State
from models import DebugAction, DebugObservation
from types import SimpleNamespace

load_dotenv()

# --- HUGGING FACE URL FIX ---
def fix_hf_url(url: str) -> str:
    """Converts standard Hugging Face Space URLs to Direct URLs for WebSockets."""
    if url and "huggingface.co/spaces/" in url:
        parts = url.split("huggingface.co/spaces/")[-1].strip("/").split("/")
        if len(parts) >= 2:
            username = parts[0]
            space_name = parts[1]
            return f"https://{username}-{space_name}.hf.space"
    return url

# --- 1. LLM CONFIGURATION (Strictly matching the Hackathon Checklist) ---
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")

# --- 2. ENVIRONMENT URL CONFIGURATION ---
# Check local ENV_URL first. If not found (like in Phase 2), default to your Space URL!
RAW_ENV_URL = os.getenv("ENV_URL", "https://huggingface.co/spaces/HitheshReddy/llm-debug-gym")
ENV_URL = fix_hf_url(RAW_ENV_URL)

STAGES = ["task_easy", "task_medium", "task_hard"]

class LLMDebugClient(EnvClient[DebugAction, DebugObservation, State]):
    def _step_payload(self, action: DebugAction) -> dict: 
        return action.model_dump()
        
    def _parse_result(self, payload: dict):
        if "error" in payload:
            print(f"SERVER ERROR: {payload['error']}")
            sys.exit(1)
        return SimpleNamespace(
            observation=DebugObservation(**payload["observation"]),
            reward=payload.get("reward", 0.1),
            done=payload.get("done", False)
        )
        
    def _parse_state(self, payload: dict) -> State: 
        return State(**payload)

async def run_stage(env, client, task_id):
    print(f"[START] task={task_id} env=llm-debug-gym model={MODEL_NAME}")
    
    res = env.reset(options={"task_id": task_id})
    current_feedback = res.observation.feedback
    steps_taken = 0
    
    md_ticks = "`" * 3
    
    for step in range(1, 21): 
        if res.done: break
        
        prompt = f"""You are an automated code-fixing API. Do not converse.

ENVIRONMENT FEEDBACK:
{current_feedback}

INSTRUCTIONS:
1. Do NOT write your own test cases. Do not write `assert` statements.
2. Do NOT explain your logic.

If you want to UPDATE the code, output ONLY a markdown block:
{md_ticks}python
# your fixed function here
{md_ticks}

If you have updated the code and want to TEST it, output EXACTLY this word and nothing else:
TEST
"""
        
        chat = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}]
        )
        
        llm_text = chat.choices[0].message.content.strip()
        
        if llm_text == "TEST" or "ACTION: TEST" in llm_text.upper():
            cmd = "TEST"
            code = ""
        else:
            cmd = "WRITE"
            match = re.search(r"`{3}(?:python)?\n?(.*?)\n?`{3}", llm_text, re.DOTALL | re.IGNORECASE)
            if match:
                code = match.group(1).strip()
            else:
                code = llm_text.strip() 
                
        res = env.step(DebugAction(command=cmd, content=code))
        current_feedback = res.observation.feedback
        steps_taken = step
        
        print(f"[STEP] step={step} action={cmd} reward={res.reward:.2f} done={str(res.done).lower()}")

    print(f"[END] task={task_id} score={res.reward:.2f} steps={steps_taken}\n")
    
    return {"id": task_id, "score": res.reward, "steps": steps_taken}

async def main() -> None:
    # Notice: We are checking HF_TOKEN here, which they specifically said will NOT have a default in their checklist.
    # If this trips locally, make sure you have it in your .env!
    if not HF_TOKEN:
        print("HF_TOKEN missing. Ensure it is set in your .env file or environment.")
        sys.exit(1)

    # Updated to use API_BASE_URL from their checklist
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    
    print(f"🚀 Initializing EnvClient with URL: {ENV_URL}")
    agent_client = LLMDebugClient(base_url=ENV_URL)
    agent_client.message_timeout = 60.0

    with agent_client.sync() as env:
        for task_id in STAGES:
            time.sleep(2) 
            await run_stage(env, client, task_id)

if __name__ == "__main__":
    asyncio.run(main())
