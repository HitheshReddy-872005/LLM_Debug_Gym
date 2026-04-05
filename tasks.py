
DEBUG_TASKS = [
    {
        "domain": "Algorithms",
        "task": "Fix the binary search. It loops infinitely if the target is not in the array.",
        "code": "def binary_search(arr, target):\n    low, high = 0, len(arr) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target: return mid\n        elif arr[mid] < target: low = mid\n        else: high = mid\n    return -1",
        # ⬅️ THE HIDDEN UNIT TESTS
        "test_code": """
assert binary_search([1, 2, 3, 4, 5], 3) == 2, "Failed to find middle element"
assert binary_search([1, 2, 3, 4, 5], 1) == 0, "Failed to find first element"
assert binary_search([1, 2, 3], 5) == -1, "Failed to return -1 for missing element (Infinite loop fix failed)"
"""
    },
    {
        "domain": "Algorithms",
        "task": "Fix the Bubble Sort. It throws an IndexError on the last iteration.",
        "code": "def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(0, n - i):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]\n    return arr",
        "test_code": """
assert bubble_sort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9], "Sorting failed for unsorted array"
assert bubble_sort([1, 2, 3]) == [1, 2, 3], "Sorting failed for already sorted array"
"""
    },
    {
        "domain": "Data Structures",
        "task": "Fix the Valid Parentheses checker. It crashes if there are more closing brackets than opening ones.",
        "code": "def is_valid(s):\n    stack = []\n    mapping = {')': '(', '}': '{', ']': '['}\n    for char in s:\n        if char in mapping:\n            top_element = stack.pop()\n            if mapping[char] != top_element: return False\n        else:\n            stack.append(char)\n    return not stack",
        "test_code": """
assert is_valid('()[]{}') == True, "Failed basic valid string"
assert is_valid('(]') == False, "Failed mismatched brackets"
assert is_valid(']') == False, "Failed on empty stack pop (The reported bug)"
"""
    },
    {
        "domain": "Algorithms",
        "task": "Fix Kadane's Algorithm for Maximum Subarray Sum. It returns 0 if all numbers are negative, but it should return the highest negative number.",
        "code": "def max_subarray(nums):\n    max_so_far = 0\n    current_max = 0\n    for i in range(len(nums)):\n        current_max = current_max + nums[i]\n        if current_max < 0:\n            current_max = 0\n        elif max_so_far < current_max:\n            max_so_far = current_max\n    return max_so_far",
        "test_code": """
assert max_subarray([-2,1,-3,4,-1,2,1,-5,4]) == 6, "Failed on standard array with positive and negative numbers"
assert max_subarray([-3, -5, -2]) == -2, "Failed on all-negative array (The reported bug)"
"""
    },
    {
        "domain": "Data Structures",
        "task": "Fix the BFS traversal. It acts like DFS because it uses the wrong pop method on the list.",
        "code": "def bfs(graph, start):\n    visited, queue = set(), [start]\n    visited.add(start)\n    while queue:\n        vertex = queue.pop()\n        for neighbor in graph[vertex]:\n            if neighbor not in visited:\n                visited.add(neighbor)\n                queue.append(neighbor)\n    return visited",
        "test_code": """
graph = {1: [2, 3], 2: [4], 3: [], 4: []}
# A proper BFS starting at 1 should visit 2 and 3 before visiting 4.
# If it uses pop() instead of pop(0), it will visit 3, then 2, then 4.
visited_order = []
def mocked_bfs(graph, start):
    visited, queue = set(), [start]
    visited.add(start)
    while queue:
        vertex = queue.pop(0) # The correct implementation
        visited_order.append(vertex)
        for neighbor in graph[vertex]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return visited
# This tests if the code crashes or returns totally wrong data types
assert type(bfs(graph, 1)) == set, "Did not return a set"
"""
    }
]