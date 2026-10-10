report.py에 같은 코드가 세 번씩 반복돼 있어. salesreport 패키지로 리팩터해줘.
- salesreport/ 안에 역할별 모듈 최소 3개 (예: 로드, 집계, 출력)
- 중복 제거
- report.py는 진입점만 남기기: 빈 줄과 주석을 빼고 15줄 이하 (`python report.py FILE.csv` 사용법 유지)
- 출력은 바이트 단위로 기존과 같아야 해. sample.csv로 비교해볼 수 있어.
