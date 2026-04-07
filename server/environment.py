import traceback
from typing import Dict, Any, Tuple
from models import DebugObservation, DebugAction
from tasks import DEBUG_TASKS 

class LLMDebugEnv:
    def __init__(self):
        self.current_task_index = 0          
        self.current_task = None
        self.current_code = ""
        
        # OpenEnv requirements
        self.current_step = 0
        self.dynamic_max_steps = 10 
        self.history_log = []

    def reset(self, task_params: Dict[str, Any] = None) -> Tuple[DebugObservation, Dict[str, Any]]:
        # Initialize episode tracking
        self.current_step = 0
        self.history_log = []
        if task_params is None:
            task_params = {}
            
        # Get dynamic limit if provided in YAML, else default to 10
        self.dynamic_max_steps = task_params.get("dynamic_limit", 10)

        # Your task loading logic
        self.current_task = DEBUG_TASKS[self.current_task_index]
        self.current_code = self.current_task['code']
        self.current_task_index = (self.current_task_index + 1) % len(DEBUG_TASKS)
                
        # Build the initial feedback
        feedback = f"TASK: {self.current_task['task']}\n\nCODE:\n{self.current_code}"
        
        # Log for the LLM Grader trajectory
        self.history_log.append(f"--- STARTING DEBUG SESSION | Domain: {self.current_task['domain']} ---")
        self.history_log.append(f"Initial State:\n{feedback}")

        obs = DebugObservation(
            feedback=feedback,
            test_passed=False, 
            reward=0.01,  
            done=False,
            metadata={"domain": self.current_task['domain'], "code": self.current_code} 
        )
        
        # OpenEnv expects a tuple of (observation, info)
        info = {"trajectory": "\n".join(self.history_log)}
        return obs, info

    def step(self, action: DebugAction) -> Tuple[DebugObservation, float, bool, Dict[str, Any]]:
        self.current_step += 1
        self.history_log.append(f"[Step {self.current_step}] Action: {action.command}")
        
        # Default loop variables
        reward = 0.01
        is_done = False
        final_feedback = ""
        test_passed = False

        if action.command == "WRITE":
            self.current_code = action.content
            final_feedback = "Code updated. Ready for testing."
            
        elif action.command == "TEST":
            test_cases = self.current_task.get('test_cases', [])
            passed_count = 0
            total_tests = len(test_cases)
            error_feedback = ""
            
            for test in test_cases:
                try:
                    full_script = self.current_code + "\n\n" + test
                    exec_scope = {}
                    exec(full_script, {}, exec_scope)
                    passed_count += 1
                except Exception as e:
                    # Feed the exact error back to the AI so it can learn
                    error_feedback += f"\n- FAILED: {test} -> {type(e).__name__}: {str(e)}"
            
            # Calculate fractional reward and clamp it for the validator
            raw_reward = float(passed_count) / total_tests if total_tests > 0 else 0.0
            reward = max(0.01, min(0.99, raw_reward))
                        
            # Strict pass check
            test_passed = (passed_count == total_tests and total_tests > 0)
            is_done = test_passed 
            
            if test_passed:
                reward = 1.0 # Give full 1.0 reward on complete success
                final_feedback = f"SUCCESS! All {total_tests} tests passed."
            else:
                final_feedback = f"Partial Success. Passed {passed_count}/{total_tests} tests. Fix the following errors and try again:{error_feedback}"
                    
        else:
            final_feedback = f"Invalid action command. Must be 'WRITE' or 'TEST'."

        # Log the environment's response to the trajectory
        self.history_log.append(f"[Step {self.current_step}] Observation: {final_feedback}")

        # Check if we ran out of steps (OpenEnv fail-safe)
        if not is_done and self.current_step >= self.dynamic_max_steps:
            is_done = True
            self.history_log.append("STATUS: Maximum steps reached. Terminating early.")

        # Create the observation model
        obs = DebugObservation(
            feedback=final_feedback,
            test_passed=test_passed,
            reward=reward,
            done=is_done, 
            metadata={"domain": self.current_task['domain'], "code": self.current_code}
        )
        
        # OpenEnv expects a tuple of (observation, reward, done, info)
        info = {
            "trajectory": "\n".join(self.history_log),
            "steps_taken": self.current_step
        }
        
        return obs, reward, is_done, info
