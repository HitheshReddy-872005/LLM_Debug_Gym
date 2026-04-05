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
        
        bundled_feedback = f"TASK: {self.current_task['task']}\n\nCODE:\n{self.current_code}"
        
        return DebugObservation(
            feedback=bundled_feedback,
            test_passed=False,
            reward=0.0,
            done=False,
            metadata={
                "domain": self.current_task['domain'], 
                "code": self.current_code
            } 
        )

    def step(self, action: DebugAction):
        if action.command == "WRITE":
            self.current_code = action.content
            
            return DebugObservation(
                feedback="Code updated. Ready for testing.",
                test_passed=False,
                reward=0.0,
                done=False,
                metadata={"domain": self.current_task['domain'], "code": self.current_code}
            )
            
        elif action.command == "TEST":
            try:
                # ⬅️ THE NEW TEST LOGIC
                # Grab the hidden tests for this specific task
                hidden_tests = self.current_task.get('test_code', '')
                
                # Glue the AI's code and the hidden tests together!
                full_execution_script = self.current_code + "\n\n" + hidden_tests
                
                compiled_code = compile(full_execution_script, '<string>', 'exec')
                local_scope = {}
                exec(compiled_code, {}, local_scope)
                
                return DebugObservation(
                    feedback="Test Passed! The code executed and passed all hidden unit tests.",
                    test_passed=True,
                    reward=1.0,
                    done=True,
                    metadata={"domain": self.current_task['domain'], "code": self.current_code}
                )
                
            except AssertionError as e:
                # ⬅️ Catch logic failures specifically!
                return DebugObservation(
                    feedback=f"Test Failed! The code ran, but gave the wrong logical answer.\nAssertion Error: {str(e)}",
                    test_passed=False,
                    reward=0.0,
                    done=False,
                    metadata={"domain": self.current_task['domain'], "code": self.current_code}
                )
                
            except Exception as e:
                # Catch syntax errors or complete crashes
                error_msg = traceback.format_exc(limit=0).strip()
                return DebugObservation(
                    feedback=f"Test Failed. The code crashed:\n{error_msg}",
                    test_passed=False,
                    reward=0.0,
                    done=False, 
                    metadata={"domain": self.current_task['domain'], "code": self.current_code}
                )
        
        else:
            return DebugObservation(
                feedback=f"Unknown command: {action.command}. Use WRITE or TEST.",
                test_passed=False,
                reward=0.0,
                done=False,
                metadata={"domain": self.current_task['domain'], "code": self.current_code}
            )