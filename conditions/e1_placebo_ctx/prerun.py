"""E1 맥락 위약: u01n이 같은 작업 폴더에 넣을 사전 맥락과 바이트 길이가 같은, 작업과 무관한 문서를 .claude/ctx.md로 만든다.

- 길이: 작업 폴더 사본에 u01n의 prerun(_ref_prerun.py)을 돌려 잰다.
- 내용: 가상의 사내 도서관 소장 목록. 태스크 이름을 seed로 써서 같은 문제에는 항상 같은 문서가 들어간다.
"""
import os, random, shutil, subprocess, sys, tempfile

work, task = sys.argv[1], sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))

tmp = tempfile.mkdtemp()
ref = os.path.join(tmp, 'w')
shutil.copytree(work, ref, ignore=shutil.ignore_patterns('.claude'))
subprocess.run([sys.executable, os.path.join(here, '_ref_prerun.py'), ref, task], check=True)
target = len(open(os.path.join(ref, '.claude', 'ctx.md'), 'rb').read())
shutil.rmtree(tmp, ignore_errors=True)

rnd = random.Random(task)
first = ['여름의', '조용한', '먼', '오래된', '푸른', '작은', '낯선', '따뜻한', '긴', '마지막']
second = ['정원', '항구', '골목', '편지', '기차', '도서관', '언덕', '부엌', '바다', '계절']
family = ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임']
given = ['하늘', '서연', '민준', '지우', '도윤', '예린', '태오', '수아', '현우', '다인']
lines = ['# 사내 도서관 소장 목록', '', '2층 열람실 서가 기준. 대출 기간은 2주이며 한 번 연장할 수 있다.', '']
i = 0
while len('\n'.join(lines).encode()) < target:
    i += 1
    lines.append(f'- {i:04d}. 『{rnd.choice(first)} {rnd.choice(second)}』 {rnd.choice(family)}{rnd.choice(given)} 지음, '
                 f'{rnd.randint(1985, 2025)}년, 서가 {rnd.choice("ABCDEFG")}-{rnd.randint(1, 40):02d}, 대출 {rnd.randint(0, 60)}회')
text = '\n'.join(lines).encode()[:target].decode('utf-8', errors='ignore')
os.makedirs(os.path.join(work, '.claude'), exist_ok=True)
open(os.path.join(work, '.claude', 'ctx.md'), 'w').write(text)
