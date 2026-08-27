"""[문제 pool 세팅] problems 를 '날짜 없는 pool' 로 재시딩.

동작:
  - problems 컬렉션을 drop → 부분 유니크 인덱스 재생성 → 문제들을 date 없이 삽입
  - solves 도 초기화 (문제 갈면 옛 풀이기록은 깨진 참조가 되므로)
  - today() 가 매일(또는 데모 날짜 이동 시) 이 pool 에서 랜덤 1개를 뽑아
    그 문제에 그날 날짜를 부여함 (= 랜덤 출제)

⚠️ problems·solves 를 전부 지웁니다. 공유 DB면 팀원과 합의 후 실행하세요.
사용:  python setup_pool.py
"""
from datetime import datetime, timezone
from core.db import db, ensure_indexes


# ===================== 문제 pool (원하는 만큼 추가) =====================
POOL = [
    {"title": "분산 버전 관리", "difficulty": "easy", "week": 1,
     "question": "코드 변경 이력을 관리하는 대표적인 분산 버전관리 도구는?",
     "answer": "git", "accepted": ["git", "깃"],
     "hints": ["개발 도구입니다.", "코드 변경 이력을 관리합니다.", "commit을 사용합니다.",
               "branch를 사용할 수 있습니다.", "GitHub와 함께 자주 사용됩니다."],
     "explanation": "분산 버전 관리 시스템입니다."},

    {"title": "경량 파이썬 웹 프레임워크", "difficulty": "medium", "week": 1,
     "question": "이 경량 파이썬 웹 프레임워크의 이름은?",
     "answer": "flask", "accepted": ["flask", "플라스크"],
     "hints": ["Python 기반입니다.", "웹 애플리케이션 개발에 사용됩니다.",
               "비교적 가벼운 프레임워크입니다.", "Jinja2를 기본 템플릿 엔진으로 사용합니다.",
               "이름은 물병을 뜻하는 영어 단어이기도 합니다."],
     "explanation": "Flask는 경량 파이썬 웹 프레임워크입니다."},

    {"title": "문서 지향 NoSQL", "difficulty": "medium", "week": 1,
     "question": "JSON과 유사한 문서(document)를 저장하는 대표적 NoSQL 데이터베이스는?",
     "answer": "mongodb", "accepted": ["mongodb", "mongo", "몽고디비", "몽고"],
     "hints": ["NoSQL 데이터베이스입니다.", "문서(document) 지향입니다.",
               "BSON 형식으로 저장합니다.", "컬렉션과 문서 개념을 씁니다."],
     "explanation": "MongoDB는 문서 지향 NoSQL 데이터베이스입니다."},

    {"title": "웹의 기본 통신 규약", "difficulty": "easy", "week": 1,
     "question": "웹 브라우저와 서버가 데이터를 주고받는 기본 프로토콜은?",
     "answer": "http", "accepted": ["http"],
     "hints": ["인터넷 통신과 관련 있습니다.", "웹에서 사용됩니다.", "요청과 응답이 있습니다.",
               "GET과 POST가 있습니다.", "상태 코드 404와 관련 있습니다."],
     "explanation": "웹 클라이언트와 서버가 통신하기 위한 프로토콜입니다."},

    {"title": "컨테이너 가상화", "difficulty": "medium", "week": 2,
     "question": "애플리케이션을 컨테이너로 패키징·실행하는 대표 플랫폼은?",
     "answer": "docker", "accepted": ["docker", "도커"],
     "hints": ["컨테이너 기술입니다.", "이미지와 컨테이너 개념이 있습니다.",
               "고래 로고로 유명합니다.", "Dockerfile로 이미지를 빌드합니다."],
     "explanation": "Docker는 컨테이너 가상화 플랫폼입니다."},

    {"title": "자료구조 - 후입선출", "difficulty": "easy", "week": 2,
     "question": "마지막에 넣은 데이터가 가장 먼저 나오는(LIFO) 자료구조는?",
     "answer": "stack", "accepted": ["stack", "스택"],
     "hints": ["LIFO 구조입니다.", "push와 pop 연산을 씁니다.", "함수 호출 관리에도 쓰입니다."],
     "explanation": "스택(Stack)은 후입선출(LIFO) 자료구조입니다."},

    {"title": "관계형 DB 질의 언어", "difficulty": "easy", "week": 2,
     "question": "관계형 데이터베이스에서 데이터를 다루는 표준 질의 언어는?",
     "answer": "sql", "accepted": ["sql"],
     "hints": ["관계형 DB에서 씁니다.", "SELECT, INSERT 등의 문법이 있습니다.",
               "구조화된 질의 언어의 약자입니다."],
     "explanation": "SQL은 관계형 DB의 표준 질의 언어입니다."},

    {"title": "프론트엔드 UI 라이브러리", "difficulty": "hard", "week": 3,
     "question": "컴포넌트 기반으로 UI를 만드는, 메타(구 페이스북)가 만든 라이브러리는?",
     "answer": "react", "accepted": ["react", "리액트"],
     "hints": ["프론트엔드 라이브러리입니다.", "컴포넌트 기반입니다.", "가상 DOM을 사용합니다.",
               "JSX 문법을 씁니다.", "메타(구 페이스북)가 개발했습니다."],
     "explanation": "React는 컴포넌트 기반 프론트엔드 UI 라이브러리입니다."},

    {"title": "범용 프로그래밍 언어", "difficulty": "easy", "week": 1,
     "question": "문법이 간단하고 데이터 분석·AI에 많이 쓰이는, 뱀 이름 같은 범용 프로그래밍 언어는?",
     "answer": "python", "accepted": ["python", "파이썬"],
     "hints": ["프로그래밍 언어입니다.", "문법이 비교적 간단합니다.",
               "데이터 분석과 AI에 많이 쓰입니다.", "동적 타이핑 언어입니다.", "뱀 이름처럼 보입니다."],
     "explanation": "범용 프로그래밍 언어입니다."},
]
# =====================================================================


def run():
    db.problems.drop()            # 컬렉션 + 기존 인덱스 제거 → 부분 인덱스 새로 생성됨
    db.solves.delete_many({})     # 문제 갈면 옛 풀이기록은 깨진 참조 → 초기화
    # db.users.delete_many({})    # (완전 초기화 원하면 주석 해제)
    ensure_indexes()              # 부분 유니크 인덱스 등 재생성

    docs = []
    for p in POOL:
        docs.append({
            # ⚠️ "date" 필드 없음 → pool 상태. today()가 랜덤으로 날짜 배정.
            "week": p.get("week", 1),
            "difficulty": p.get("difficulty", "medium"),
            "title": p["title"],
            "question": p["question"],
            "answer": p["answer"].strip().lower(),
            "accepted": [a.strip().lower() for a in p.get("accepted", [])],
            "hints": [{"order": i + 1, "text": t} for i, t in enumerate(p["hints"])],
            "explanation": p.get("explanation", ""),
            "created_at": datetime.now(timezone.utc),
        })
    db.problems.insert_many(docs)
    print(f"[OK] pool에 문제 {len(docs)}개 삽입 (date 미배정 → 랜덤 출제 대기)")


if __name__ == "__main__":
    run()
