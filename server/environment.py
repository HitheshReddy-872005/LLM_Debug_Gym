import os
import sys
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tasks import DEBUG_TASKS
from models import DebugObservation, DebugAction

class LLMDebugEnv:
    def __init__(self):
        self.current_task_id = None
        self.current_task = {}
        self.current_code = ""
        self.current_step = 0
        self.history_log = []

    def reset(self, options=None, **kwargs) -> DebugObservation:
        self.current_step = 0
        self.history_log = []
        options = options or {}
        
        req_id = options.get("task_id") or os.environ.get("TASK_ID")
        if not req_id: raise ValueError("FATAL: No TASK_ID provided.")

        self.current_task_id = req_id
        self.current_task = DEBUG_TASKS[self.current_task_id]
        self.current_code = self.current_task.get('code', '')
        
        feedback = f"TASK: {self.current_task.get('task')}\nCODE: {self.current_code}"
        self.history_log.append(f"--- SESSION STARTED: {self.current_task_id} ---")
        
        return DebugObservation(feedback=feedback, test_passed=False, reward=0.1, done=False, metadata={"code": self.current_code, "task": self.current_task.get('task')})

    def step(self, action: DebugAction) -> DebugObservation:
        self.current_step += 1
        self.history_log.append(f"Step {self.current_step}: {action.command}")
        
        reward, is_done, test_passed = 0.1, False, False
        final_feedback = ""

        if action.command == "WRITE":
            self.current_code = action.content
            final_feedback = "Code updated. Now reply with TEST to check it."
            
        elif action.command == "TEST":
            exec_scope = {}
            # 1. PRE-CHECK SYNTAX AND EXECUTE BASE FUNCTION
            try:
                compile(self.current_code, '<string>', 'exec')
                exec(self.current_code, exec_scope)
            except Exception as e:
                final_feedback = f"CRITICAL ERROR: Code failed to compile or run.\n{type(e).__name__}: {str(e)}\n\nCURRENT CODE:\n{self.current_code}"
                return DebugObservation(feedback=final_feedback, test_passed=False, reward=0.1, done=False, metadata={"code": self.current_code})
            
            # 2. RUN TEST CASES
            test_cases = self.current_task.get('test_cases', [])
            passed_count = 0
            failed_logs = []
            
            for t in test_cases:
                try:
                    # Execute test against the already-compiled scope
                    exec(t, exec_scope)
                    passed_count += 1
                except AssertionError:
                    failed_logs.append(f"Failed assertion: {t}")
                except Exception as e:
                    failed_logs.append(f"Crashed on {t}: {type(e).__name__} - {str(e)}")
            
            total = len(test_cases)
            reward = max(0.1, min(0.9, float(passed_count)/total if total > 0 else 0))
            test_passed = (passed_count == total and total > 0)
            is_done = test_passed
            
            final_feedback = f"Result: {passed_count}/{total} tests passed."
            if failed_logs:
                final_feedback += "\nIssues to fix:\n- " + "\n- ".join(failed_logs[:3])
            
            # 3. MEMORY RETENTION
            if not is_done:
                final_feedback += f"\n\nCURRENT CODE TO FIX:\n{self.current_code}"

        if not is_done and self.current_step >= self.current_task.get("max_steps", 10):
            is_done = True
            
        return DebugObservation(feedback=final_feedback, test_passed=test_passed, reward=reward, done=is_done, metadata={"code": self.current_code})

    def state(self) -> Dict[str, Any]:
        return {"task_id": self.current_task_id, "current_code": self.current_code, "step": self.current_step}
