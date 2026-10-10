import json, sys
json.load(sys.stdin)
print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolBatch', 'additionalContext': '사용자 설정: 이 세션은 출력 절감 모드다(간결, 첫 해법 채택, 재검산 없음, 검증은 마지막 1회). 다음에 필요한 호출 가운데 서로 의존하지 않는 것은 한 응답에 모두 보낸다.'}}, ensure_ascii=False))
