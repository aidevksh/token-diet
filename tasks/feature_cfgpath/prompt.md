cfgpath.py에 기능을 추가해줘.

1. get 경로 문법 확장
   - 리스트 인덱스: `servers[1].host`, 연속 인덱스 `matrix[0][2]`, 음수 인덱스 `items[-1]`
   - 이스케이프된 점: `a\.b.c`는 키 "a.b" 아래의 "c"
   - 키가 없거나, 인덱스가 범위를 벗어나거나, 타입이 안 맞으면 예외 없이 default 반환
2. `set(cfg, path, value)` 추가
   - 중간 경로가 없으면 만든다. 다음 세그먼트가 인덱스면 빈 리스트, 아니면 빈 dict
   - 리스트 인덱스가 길이와 같으면 append, 길이보다 크면 IndexError
   - cfg를 반환
3. `delete(cfg, path)` 추가: 지웠으면 True, 경로가 없으면 False

기존 테스트는 계속 통과해야 해.
