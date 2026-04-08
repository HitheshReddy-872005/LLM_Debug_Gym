DEBUG_TASKS = {
    "task_easy": {
        "task": "Fix 'clean_input(s)'. It must return a trimmed string. If input is None, False, or not a string, return an empty string.",
        # BUG: str() casts None to 'None' and False to 'False', failing the edge cases.
        "code": "def clean_input(s):\n    return str(s).strip()", 
        "test_cases": [
            "assert clean_input('  hello  ') == 'hello'",
            "assert clean_input('word ') == 'word'",
            "assert clean_input(None) == ''",
            "assert clean_input(False) == ''",
            "assert clean_input(123) == ''",
            "assert clean_input('') == ''",
            "assert clean_input('   ') == ''",
            "assert clean_input('\\n\\t') == ''",
            "assert clean_input(' 0 ') == '0'",
            "assert clean_input([]) == ''"
        ],
        "max_steps": 10
    },
    "task_medium": {
        "task": "Fix 'get_unique_ordered(items)'. Return unique items in order of first appearance. Handle unhashable types (like lists/dicts) safely.",
        # BUG: dict.fromkeys preserves order perfectly, but CRASHES on unhashable lists/dicts.
        "code": "def get_unique_ordered(items):\n    return list(dict.fromkeys(items))", 
        "test_cases": [
            "assert get_unique_ordered([3, 1, 2, 1]) == [3, 1, 2]",
            "assert get_unique_ordered(['a', 'b', 'a']) == ['a', 'b']",
            "assert get_unique_ordered([None, None]) == [None]",
            "assert get_unique_ordered([True, 1, 0, False]) == [True, 0]",
            "assert get_unique_ordered([]) == []",
            "assert get_unique_ordered([[1], [1], [2]]) == [[1], [2]]", # Will crash here
            "assert get_unique_ordered([(1,), (1,)]) == [(1,)]",
            "assert get_unique_ordered([{}, {}]) == [{}]", # Will crash here
            "assert get_unique_ordered([1, '1']) == [1, '1']",
            "assert get_unique_ordered([1.0, 1]) == [1.0]"
        ],
        "max_steps": 15
    },
    "task_hard": {
        "task": "Fix 'deep_merge(d1, d2)'. Merge dictionaries recursively. Colliding keys: merge if both are dicts, else d2 wins.",
        # BUG: It correctly recurses, but forgets to assign the result back to res[k]
        "code": "def deep_merge(d1, d2):\n    res = d1.copy()\n    for k, v in d2.items():\n        if k in res and isinstance(v, dict):\n            deep_merge(res[k], v)\n        else:\n            res[k] = v\n    return res",
        "test_cases": [
            "assert deep_merge({'a': 1}, {'b': 2}) == {'a': 1, 'b': 2}",
            "assert deep_merge({'a': 1}, {'a': 5}) == {'a': 5}",
            "assert deep_merge({}, {'a': 1}) == {'a': 1}",
            "assert deep_merge({'a': 1}, {}) == {'a': 1}",
            "assert deep_merge({'a': 0}, {'a': False}) == {'a': False}",
            "assert deep_merge({'a': [1]}, {'a': [2]}) == {'a': [2]}",
            "assert deep_merge({'a': {'x': 1}}, {'a': {'y': 2}}) == {'a': {'x': 1, 'y': 2}}", # Fails
            "assert deep_merge({'a': 1}, {'a': {'x': 1}}) == {'a': {'x': 1}}",
            "assert deep_merge({'a': {'b': {'c': 1}}}, {'a': {'b': {'d': 2}}}) == {'a': {'b': {'c': 1, 'd': 2}}}", # Fails
            "assert deep_merge({'a': None}, {'a': {'x': 1}}) == {'a': {'x': 1}}"
        ],
        "max_steps": 20
    }
}

#updated
