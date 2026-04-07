DEBUG_TASKS = {
    "task_easy": {
        "task": "Fix the syntax error: missing closing quote on the dictionary key.",
        "code": 'def parse_log(log_line):\n    parts = log_line.split(": ")\n    return {"level: parts[0], "msg": parts[1]}',
        "test_cases": [
            'assert parse_log("INFO: Start") == {"level": "INFO", "msg": "Start"}',
            'assert parse_log("ERROR: Crash") == {"level": "ERROR", "msg": "Crash"}'
        ],
        "max_steps": 10
    },

    "task_medium": {
        "task": "Fix pop() so it returns None if the buffer is empty instead of throwing an error.",
        "code": 'class Buf:\n    def __init__(self): self.b = []\n    def pop(self): return self.b.pop(0)',
        "test_cases": [
            'b = Buf()\nb.b = ["x"]\nassert b.pop() == "x"', 
            'b = Buf()\nassert b.pop() is None'
        ],
        "max_steps": 15
    },

    "task_hard": {
        "task": "Fix tax calc: 10% base, +5% luxury, +50 fee if amount > 1000. MAX TAX IS 200.",
        "code": 'def calc_tax(amt, lux):\n    t = amt * 0.10\n    if lux: t += amt * 0.05\n    return t',
        "test_cases": [
            "assert calc_tax(100, False) == 10.0",
            "assert calc_tax(2000, False) == 200.0",
            "assert calc_tax(1500, True) == 200.0",
            "assert calc_tax(1200, False) == 170.0"
        ],
        "max_steps": 20
    }
}
