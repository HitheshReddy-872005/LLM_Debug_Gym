from pydantic import BaseModel
from typing import Optional, Dict, Any

class DebugAction(BaseModel):
    command: str  # WRITE or TEST
    content: Optional[str] = ""

class DebugObservation(BaseModel):
    feedback: str
    test_passed: bool
    reward: float
    done: bool
    metadata: Optional[Dict[str, Any]] = None

#updated
