import json, sys
json.load(sys.stdin)
rules = open(__file__.replace('hook.py', 'rules.md')).read()
print(json.dumps({'hookSpecificOutput': {'hookEventName': 'UserPromptSubmit', 'additionalContext': rules}}, ensure_ascii=False))
