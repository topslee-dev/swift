# SWIFT MT 전문 검증기 (SWIFT MT Message Validator)

## 프로그램 개요

SWIFT MT 전문 검증기는国际金融通信 Society for Worldwide Interbank Financial Telecommunication SWIFT 메시지를 검증하는 웹 기반 도구입니다. Python으로 개발되었으며, Streamlit을 사용하여 웹 UI를 제공합니다.

## 주요 기능

### 1. 전문별 설명 조회 (Tab 1)
- 35개 이상의 MT 타입 지원
- 각 MT 타입의 필드 정보 (필드 번호, 이름, 길이, 설명, 필수 여부) 조회
- 필수 필드 하이라이트

### 2. INPUT 전문 검증 (Tab 2)
- 선택한 MT 타입에 대한 Block 4 (Text) 검증
- 사용자 입력 메시지에서 필드 파싱
- 필수 필드 누락 여부 검사

### 3. 의미적 검색 (Tab 3)
- ChromaDB 기반 임베딩 검색
- 자연어로 필드 설명 검색 가능
- 예: "beneficiary", "foreign exchange" 등

### 4. 전체 전문 검증 (Tab 4)
- 5개 블록 전체 검증
  - **Block 1 (Basic Header)**: 송신 BIC, 서비스 ID 검증
  - **Block 2 (Application Header)**: 메시지 타입, 방향, 수신 BIC 검증
  - **Block 3 (User Header)**: UETR, 서비스 코드 검증
  - **Block 4 (Text)**: 필수 필드 검증
  - **Block 5 (Trailer)**: 체크섬(CHK) 검증

## 지원 MT 타입

| 카테고리 | MT 타입 | 설명 |
|---------|---------|------|
| Category 1 | MT101, MT102, MT102Plus, MT103, MT107 | 고객 신용 전송 |
| Category 2 | MT202, MT202COV, MT205, MT205COV | 금융기관 전송 |
| Category 3 | MT300, MT303, MT320, MT330, MT340 | 외환/대출/예금 |
| Category 4 | MT400, MT410 | 수표/압류 |
| Category 5 | MT506, MT509, MT515 |증권 정산 |
| Category 6 | MT600 | 무역 서비스 |
| Category 7 | MT700, MT707, MT710, MT720, MT760 | 신용장/보증 |
| Category 9 | MT900, MT910, MT940 | 확인/명세서 |

## 기술 스택

- **Backend**: Python 3.x
- **Web Framework**: Streamlit
- **Vector Database**: ChromaDB (의미적 검색용)
- **Data Processing**: Pandas, Regex

## 프로젝트 구조

```
swift/
├── swift_parser.py      # SWIFT 메시지 파싱 및 검증 로직
├── mt_required_data.py # MT 타입별 필드 정의 데이터
├── streamlit_app.py     # Streamlit 웹 UI
├── requirements.txt    # Python 의존성
├── data/
│   ├── chroma_db/      # ChromaDB 임베딩 데이터베이스
│   ├── mt_documents.json
│   └── mt_documents_with_embeddings.json
└── images/             # UI 스크린샷
```

## 실행 방법

```bash
# Python 가상환경 생성 (선택)
python -m venv .venv

# 의존성 설치
pip install -r requirements.txt

# Streamlit 앱 실행
streamlit run streamlit_app.py
```

## SWIFT 메시지 구조

SWIFT 메시지는 5개의 블록으로 구성됩니다:

1. **{1: Block 1 - Basic Header}**
   - 형식: `F{서비스코드}{송신BIC}{ Sequence Number}`
   - 예: `{1:F01SOGEFRPPAXXX0070970817}`

2. **{2: Block 2 - Application Header}**
   - 형식: `{.direction}{MT타입}{날짜시간}{수신BIC}{ederence}`
   - 예: `{2:O1031734150713DEUTDEFFBXXX00739698421607131634N}`

3. **{3: Block 3 - User Header}**
   - 선택적 블록 (UETR, 서비스 코드 등)
   - 예: `{3:{108:12345678-1234-1234-1234-123456789012}}`

4. **{4: Block 4 - Text}**
   - 실제 메시지 내용 (필드:값 형식)
   - 예: `:20:REF123456`

5. **{5: Block 5 - Trailer}**
   - 체크섬 정보
   - 예: `{5:{CHK:D628FE0165A7}}`

## 필드 길이 형식 Legend

| 기호 | 의미 |
|------|------|
| n | 숫자 |
| a | 영문자 |
| c | 문자 |
| x | 영문/숫자 |
| !n | n자리 필수 (예: 6!n = 6자리 필수) |
| n*m | n~m회 반복 |
| A/D | A 또는 D 옵션 |

## 개발 상태

- [x] 기본 파싱 로직 구현
- [x] 35개 MT 타입 지원
- [x] Block 1-5 검증
- [x] Streamlit UI
- [x] 의미적 검색

## 참고 사항

이 프로그램은 교육 및 검증 목적으로 만들어졌습니다. 실제 금융 거래에는 공식 SWIFT 검증 도구를 사용하세요.
