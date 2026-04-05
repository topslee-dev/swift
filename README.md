# SWIFT MT Validator

SWIFT MT 메시지 검증기 - 5개 블록 구조 검증, 필수 필드 체크, 의미적 검색

## 주요 기능

- 35개 MT 타입 지원 (MT103, MT202, MT700 등)
- 5개 블록 전체 검증 (Block 1~5)
- 필수 필드 자동 검증
- 의미적 검색 (Vector DB)

## 프로젝트 구조

```
swift/
├── streamlit_app.py           # Streamlit 메인 앱 (4개 탭)
├── swift_parser.py            # 5개 블록 파서 및 검증
├── mt_required_data.py        # 35개 MT 타입 필드 정보
├── requirements.txt            # Python 의존성
├── README.html                # 상세 HTML 문서
├── README.md                  # 이 파일
├── .gitignore                 # Git 무시 파일
├── images/                    # 스크린샷
│   ├── tab1-description.png   # 전문별 설명 조회
│   ├── tab2-validation.png     # INPUT 전문 검증
│   ├── tab3-search.png        # 의미적 검색
│   └── tab4-full-validation.png # 전체 전문 검증
└── data/
    ├── chroma_db/             # Vector DB (Chroma)
    ├── mt_documents.json      # MT 필드 데이터
    └── mt_documents_with_embeddings.json # 임베딩 데이터
```

## 사용 방법

### 1. 클론
```bash
git clone <repository-url>
cd swift
```

### 2. 가상환경 생성
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 실행
```bash
.venv\Scripts\streamlit.exe run streamlit_app.py
```

브라우저에서 `http://localhost:8501`로 접속

## 아키텍처

### 1. Streamlit UI (streamlit_app.py)
- 4개 탭 구성:
  - 전문별 설명 조회
  - INPUT 전문 검증
  - 의미적 검색
  - 전체 전문 검증

### 2. SWIFT 파서 (swift_parser.py)
- 5개 블록 파싱
- 각 블록 검증:
  - Block 1: Basic Header (F01 + BIC)
  - Block 2: Application Header (메시지 타입)
  - Block 3: User Header (UETR)
  - Block 4: Text (필드 검증)
  - Block 5: Trailer (체크섬)

### 3. 데이터 (mt_required_data.py)
- 35개 MT 타입 정의
- 각 필드: 번호, 이름, 길이, 설명, 필수여부

### 4. Vector DB (Chroma)
- 의미적 검색 기능
- 205개 임베딩 (384차원)
- sentence-transformers/all-MiniLM-L6-v2

## 기술 스택

| 기술 | 용도 |
|------|------|
| Python | 프로그래밍 언어 |
| Streamlit | 웹 프레임워크 |
| Chroma DB | Vector Database |
| Sentence Transformers | 텍스트 임베딩 |
| Pandas | 데이터 처리 |
