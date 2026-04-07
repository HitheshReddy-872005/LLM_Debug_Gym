import traceback
from models import DebugObservation, DebugAction
from tasks import DEBUG_TASKS 

class LLMDebugEnv:
    def __init__(self):
        self.current_task_index = 0  
        self.current_task = None
        self.current_code = ""

    def reset(self):
        self.current_task = DEBUG_TASKS[self.current_task_index]
        self.current_code = self.current_task['code']
        self.current_task_index = (self.current_task_index + 1) % len(DEBUG_TASKS)
        
        return DebugObservation(
            feedback=f"TASK: {self.current_task['task']}\n\nCODE:\n{self.current_code}",
            test_passed=False, 
            reward=0.01,  
            done=False,
            metadata={"domain": self.current_task['domain'], "code": self.current_code} 
        )

    def step(self, action: DebugAction):
        if action.command == "WRITE":
            self.current_code = action.content
            return DebugObservation(
                feedback="Code updated. Ready for testing.",
                test_passed=False, 
                reward=0.01,  
                done=False,
                metadata={"domain": self.current_task['domain'], "code": self.current_code}
            )
            
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

            # THE GRADUAL LEARNING FIX: 
            # Only end the environment episode if the AI got a perfect score.
            is_done = test_passed 

            if test_passed:
                final_feedback = f"SUCCESS! All {total_tests} tests passed."
            else:
                final_feedback = f"Partial Success. Passed {passed_count}/{total_tests} tests. Fix the following errors and try again:{error_feedback}"

            return DebugObservation(
                feedback=final_feedback,
                test_passed=test_passed,
                reward=reward,
                done=is_done, 
                metadata={"domain": self.current_task['domain'], "code": self.current_code}
            )
            
        else:
            return DebugObservation(
                feedback=f"Invalid action command. Must be 'WRITE' or 'TEST'.",
                test_passed=False, 
                reward=0.01,  
                done=False,
                metadata={"domain": self.current_task['domain'], "code": self.current_code}
            )
