import asyncio
import os
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
ENV_URL = os.getenv("ENV_URL", "https://hitheshreddy-llm-debug-gym.hf.space") 

# 2. Concrete Client Implementation
class LLMDebugClient(EnvClient[DebugAction, DebugObservation, State]):
    def _step_payload(self, action: DebugAction) -> dict:
        return action.model_dump()

    def _parse_result(self, payload: dict):
        # Maps the server response to a namespace for dot-notation access
        return SimpleNamespace(
            observation=DebugObservation(**payload["observation"]),
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False)
        )

    def _parse_state(self, payload: dict) -> State:
        return State(**payload)

# 3. Logging Functions (Strictly formatted for Validator Round 1)
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    # score is now formatted as a float (e.g., 0.75) to pass shaped reward checks
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)

def parse_llm_response(text: str):
    text = text.strip()
    if "ACTION: TEST" in text.upper():
        return "TEST", ""
    if "ACTION: WRITE" in text.upper():
        parts = text.split("CODE:")
        code = parts[-1].strip() if len(parts) > 1 else ""
        return "WRITE", code
    return "TEST", "" 

async def main() -> None:
    if not HF_TOKEN:
        print("Error: HF_TOKEN not found. Check your secrets or .env file.")
        return

    ai_client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    
    print(f"DEBUG: Attempting to connect to -> {ENV_URL}")
    
    # Initialize the client with the provided environment URL
    with LLMDebugClient(base_url=ENV_URL).sync() as env:
        
        rewards: List[float] = []
        steps_taken = 0
        success = False

        log_start(task="debug-challenge", env="llm-debug-gym", model=MODEL_NAME)

        try:
            # Start the episode
            res = env.reset()
            current_feedback = res.observation.feedback

            for step in range(1, 11):
                # Prompt the LLM for a fix based on current environment feedback
                completion = ai_client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "You are an expert Python debugger. Fix the code. Format: ACTION: <WRITE/TEST> CODE: <Full code if WRITE>"},
                        {"role": "user", "content": f"Feedback: {current_feedback}"},
                    ]
                )
                
                cmd, code = parse_llm_response(completion.choices[0].message.content or "")

                # Execute the step in the environment
                res = env.step(DebugAction(command=cmd, content=code))
                
                rewards.append(res.reward)
                steps_taken = step
                current_feedback = res.observation.feedback
                
                # Log progress for the validator
                log_step(step=step, action=cmd, reward=res.reward, done=res.done, error=None)

                if res.done:
                    success = res.observation.test_passed
                    break

        except Exception as e:
            print(f"Error during execution: {e}")
        finally:
            # Capture the final reward as the score (e.g., 0.66 for partial credit)
            final_score = rewards[-1] if rewards else 0.0
            log_end(success=success, steps=steps_taken, score=final_score, rewards=rewards)

if __name__ == "__main__":
    asyncio.run(main())
