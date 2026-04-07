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
            test_passed=False, reward=0.0, done=False,
            metadata={"domain": self.current_task['domain'], "code": self.current_code} 
        )

    def step(self, action: DebugAction):
        if action.command == "WRITE":
            self.current_code = action.content
            return DebugObservation(
                feedback="Code updated. Ready for testing.",
                test_passed=False, reward=0.0, done=False,
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
                    error_feedback += f"\n- Test Failed: {test} ({type(e).__name__})"

            # Calculate fractional reward (Shaped Reward)
            reward = float(passed_count) / total_tests if total_tests > 0 else 0.0
            test_passed = (reward == 1.0)

            return DebugObservation(
                feedback=f"Tests complete. Passed {passed_count}/{total_tests}.{error_feedback}",
                test_passed=test_passed,
                reward=reward,
                done=True, # Episode ends after a TEST action
                metadata={"domain": self.current_task['domain'], "code": self.current_code}
            )
