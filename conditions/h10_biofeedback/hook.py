import json, sys
d = json.load(sys.stdin)
seen = {}
try:
    for line in open(d['transcript_path']):
        try:
            m = json.loads(line).get('message')
        except ValueError:
            continue
        if isinstance(m, dict) and m.get('role') == 'assistant' and m.get('id'):
            seen[m['id']] = max(seen.get(m['id'], 0), (m.get('usage') or {}).get('output_tokens', 0))
except OSError:
    sys.exit(0)
print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse',
      'additionalContext': f'[출력 토큰 누적: {sum(seen.values()):,} tok / 응답 {len(seen)}회]'}}, ensure_ascii=False))
