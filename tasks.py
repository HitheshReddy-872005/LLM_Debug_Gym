# server/tasks.py

DEBUG_TASKS = [
    {
        # TASK 0: Basic Syntax Error
        "domain": "String Manipulation",
        "task": "Fix the syntax error in the log parsing function.",
        "code": '''def parse_log(log_line):
    parts = log_line.split(": ")
    # BUG: Missing closing quote on the dictionary key
    return {"level: parts[0], "msg": parts[1]}''',
        "test_cases": [
            'assert parse_log("INFO: Server started") == {"level": "INFO", "msg": "Server started"}',
            'assert parse_log("ERROR: Crash") == {"level": "ERROR", "msg": "Crash"}'
        ]
    },
    
    {
        # TASK 1: Logic / Routing Error
        "domain": "API Routing",
        "task": "Fix the router logic so it returns the correct HTTP status codes. GET should be 200, POST should be 201, and everything else should be 405.",
        "code": '''def handle_request(method):
    if method == "GET":
        return 200
    elif method == "POST":
        # BUG: Hardcoded wrong return type for POST
        return 200
    else:
        return 405''',
        "test_cases": [
            'assert handle_request("GET") == 200',
            'assert handle_request("POST") == 201',
            'assert handle_request("DELETE") == 405'
        ]
    },

    {
        # TASK 2: Data Structures & Edge Cases
        "domain": "Data Structures & Edge Cases",
        "task": "Fix the MessageBuffer so that calling pop() on an empty buffer returns None instead of throwing an IndexError.",
        "code": '''class MessageBuffer:
    def __init__(self):
        self.buffer = []
        
    def push(self, msg):
        self.buffer.append(msg)
        
    def pop(self):
        # BUG: Does not check if buffer is empty before popping
        return self.buffer.pop(0)''',
        "test_cases": [
            '''b = MessageBuffer()
b.push("msg1")
assert b.pop() == "msg1"''',
            '''b = MessageBuffer()
assert b.pop() is None  # This should not throw an error!'''
        ]
    },

    {
        # TASK 3: Algorithms
        "domain": "Sorting Algorithms",
        "task": "Fix the sorting function so it correctly sorts a list of priority scores in DESCENDING order (highest first).",
        "code": '''def sort_priorities(scores):
    # BUG: Currently sorts in ascending order
    n = len(scores)
    for i in range(n):
        for j in range(0, n-i-1):
            if scores[j] > scores[j+1]:
                scores[j], scores[j+1] = scores[j+1], scores[j]
    return scores''',
        "test_cases": [
            'assert sort_priorities([10, 50, 20]) == [50, 20, 10]',
            'assert sort_priorities([1, 2, 3, 4]) == [4, 3, 2, 1]'
        ]
    },

    {
        # TASK 4: Concurrency & State (Themed around Network Nodes)
        "domain": "Concurrency & State",
        "task": "Fix the NodeTracker so it correctly increments the heartbeat count for existing peers. Currently, it resets the count to 1 every time a heartbeat is received.",
        "code": '''class NodeTracker:
    def __init__(self):
        self.active_nodes = {}
        
    def receive_heartbeat(self, node_id):
        if node_id not in self.active_nodes:
            self.active_nodes[node_id] = 1
        else:
            # BUG: Overwrites instead of incrementing
            self.active_nodes[node_id] = 1
            
    def get_count(self, node_id):
        return self.active_nodes.get(node_id, 0)''',
        "test_cases": [
            '''tracker = NodeTracker()
tracker.receive_heartbeat("peer_A")
assert tracker.get_count("peer_A") == 1''',
            '''tracker = NodeTracker()
tracker.receive_heartbeat("peer_B")
tracker.receive_heartbeat("peer_B")
tracker.receive_heartbeat("peer_B")
assert tracker.get_count("peer_B") == 3  # Should have incremented to 3'''
        ]
    }
]
