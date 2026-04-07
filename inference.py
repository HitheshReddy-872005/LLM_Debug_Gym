import asyncio
import os
import re
import textwrap
from typing import List, Optional
from types import SimpleNamespace 
from dotenv import load_dotenv
from openai import OpenAI
from openenv.core.env_client import EnvClient
from openenv.core import State
from models import DebugAction, DebugObservation

# 1. Load configuration
load_dotenv() 

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")
# Default to localhost to prevent proxy timeouts during LLM generations
ENV_URL = os.getenv("ENV_URL", "http://localhost:8000") 

# 2. Concrete Client Implementation
class LLMDebugClient(EnvClient[DebugAction, DebugObservation, State]):
    def _step_payload(self, action: DebugAction) -> dict:
        return action.model_dump()

    def _parse_result(self, payload: dict):
        return SimpleNamespace(
            observation=DebugObservation(**payload["observation"]),
            reward=payload.get("reward", 0.01),
            done=payload.get("done", False)
        )

    def _parse_state(self, payload: dict) -> State:
        return State(**payload)

# 3. Logging Functions (Strictly formatted for Validator)
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    
    # Final layer of safety for the log output to keep it strictly (0, 1)
    clamped_score = max(0.01, min(0.99, score))
        
    print(f"[END] success={str(success).lower()} steps={steps} score={clamped_score:.3f} rewards={rewards_str}", flush=True)

def parse_llm_response(text: str):
    text_upper = text.upper()
    
    # 1. Prioritize WRITE. If the LLM wrote code, we must capture it!
    if "ACTION: WRITE" in text_upper:
        # Split using the original text to preserve case sensitivity in the code
        parts = re.split(r"CODE:\s*", text, flags=re.IGNORECASE)
        code = parts[-1].strip() if len(parts) > 1 else text
        
        # UI-Safe markdown backtick stripping
        ticks = "`" * 3
        if ticks in code:
            pattern = ticks + r"(?:python)?\n?(.*?)\n?" + ticks
            match = re.search(pattern, code, re.DOTALL)
            if match:
                code = match.group(1).strip()
            else:
                code = code.replace(ticks + "python", "").replace(ticks, "").strip()
                
        return "WRITE", code

    # 2. If it didn't write code, check if it wants to test
    elif "ACTION: TEST" in text_upper:
        return "TEST", ""
        
    # 3. Smart Fallback: If the LLM forgot the "ACTION:" keyword but still wrote a Python block
    if "```python" in text.lower():
        match = re.search(r"```python\n?(.*?)\n?```", text, flags=re.DOTALL | re.IGNORECASE)
        if match:
            return "WRITE", match.group(1).strip()

    # 4. Ultimate fallback
    return "TEST", ""

async def main() -> None:
    if not HF_TOKEN:
        print("Error: HF_TOKEN not found. Check your secrets or .env file.")
        return

    ai_client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    
    print(f"DEBUG: Attempting to connect to -> {ENV_URL}")
    with LLMDebugClient(base_url=ENV_URL).sync() as env:
        
        rewards: List[float] = []
        steps_taken = 0
        success = False

        log_start(task="debug-challenge", env="llm-debug-gym", model=MODEL_NAME)

        try:
            res = env.reset()
            current_feedback = res.observation.feedback

            for step in range(1, 11):
                completion = ai_client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "You are an expert Python debugger. Fix the code. Format: ACTION: WRITE CODE: <Full code if WRITE> or ACTION: TEST"},
                        {"role": "user", "content": f"Feedback: {current_feedback}"},
                    ]
                )
                
                cmd, code = parse_llm_response(completion.choices[0].message.content or "")

                res = env.step(DebugAction(command=cmd, content=code))
                
                rewards.append(res.reward)
                steps_taken = step
                current_feedback = res.observation.feedback
                
                log_step(step=step, action=cmd, reward=res.reward, done=res.done, error=None)

                if res.done:
                    success = res.observation.test_passed
                    break

        except Exception as e:
            print(f"Error during execution: {e}")
        finally:
            final_score = rewards[-1] if rewards else 0.01
            log_end(success=success, steps=steps_taken, score=final_score, rewards=rewards)

if __name__ == "__main__":
    asyncio.run(main())
