from openenv.core import Action, Observation
from pydantic import BaseModel
from typing import Optional

class DebugAction(Action):
    """
    The agent chooses: 
    - 'WRITE': to edit the code (requires 'content')
    - 'TEST': to run the hidden task validation
    """
    command: str
    content: Optional[str] = None

class DebugObservation(Observation):
    """
    The 'Sensory' data plus metadata for the autograder.
    """
    feedback: str      # Terminal output or task description
    test_passed: bool  # True if the 'TEST' command succeeded
    reward: float = 0.0  # Mandatory: 0.0 to 1.0 range
    done: bool = False   # Mandatory: Signal for episode end
