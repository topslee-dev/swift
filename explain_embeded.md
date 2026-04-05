# MT 전문 임베딩 과정 상세 설명

## 개요

이 문서는 SWIFT MT 전문 데이터를 임베딩(Embedding)하여 의미적 검색(Semantic Search)을 가능하게 만든 과정과 해당 파이프라인을 설명합니다.

## 1. 임베딩 파이프라인 개요

```
MT_DATA (Python Dict) 
    → mt_documents.json (문서 추출)
    → 임베딩 생성 (OpenAI text-embedding-3-small)
    → mt_documents_with_embeddings.json (임베딩 포함)
    → ChromaDB (벡터 데이터베이스 저장)
```

## 2. 데이터 소스: mt_required_data.py

### 2.1 데이터 구조

`mt_required_data.py`에는 35개 이상의 MT 타입이 정의되어 있습니다. 각 MT 타입은 다음과 같은 구조를 가집니다:

```python
MT_DATA = {
    "MT103": {
        "category": "1",                    # 카테고리 번호
        "name": "Single Customer Credit Transfer",  # 메시지 이름
        "description": "개별 고객의 국제 전신 송금용 표준 결제 메시지",  # 설명
        "required_fields": [":20", ":23B", ":32A", ":50", ":59", ":71A"],  # 필수 필드
        "fields": [                          # 필드 목록
            {
                "field": ":20",
                "name": "Transaction Reference Number",
                "length": "16x",
                "description": "각 은행에서 생성되는 고유 참조 번호",
                "required": True,
            },
            # ... more fields
        ]
    },
    # ... more MT types
}
```

### 2.2 지원 MT 타입 목록

| 카테고리 | MT 타입 | 설명 |
|---------|---------|------|
| Category 1 | MT101, MT102, MT102Plus, MT103, MT107 | 고객 신용 전송 |
| Category 2 | MT202, MT202COV, MT205, MT205COV | 금융기관 전송 |
| Category 3 | MT300, MT303, MT320, MT330, MT340 | 외환/대출/예금 |
| Category 4 | MT400, MT410 | 수표/압류 |
| Category 5 | MT506, MT509, MT515 | 증권 정산 |
| Category 6 | MT600 | 무역 서비스 |
| Category 7 | MT700, MT707, MT710, MT720, MT760 | 신용장/보증 |
| Category 9 | MT900, MT910, MT940 | 확인/명세서 |

## 3. 문서 추출 파이프라인

### 3.1 문서 변환 로직

Python에서 정의된 MT_DATA 딕셔너리를 JSON 형태의 문서로 변환합니다. 각 필드마다 하나의 문서로 생성됩니다.

**변환 로직 (의사코드)**:

```python
for each mt_type in MT_DATA:
    for each field in mt_type["fields"]:
        document = {
            "message_type": mt_type_name,      # 예: "MT103"
            "category": mt_type["category"],   # 예: "1"
            "name": mt_type["name"],           # 예: "Single Customer Credit Transfer"
            "field": field["field"],           # 예: ":20"
            "field_name": field["name"],        # 예: "Transaction Reference Number"
            "description": field["description"],  # 필드 설명
            "text": f"MT{mt_type_name} {mt_type['name']} Field {field['field']} {field['name']}: {field['description']}",
            "category_desc": get_category_description(mt_type["category"])
        }
```

### 3.2 생성된 문서 예시

`mt_documents.json`에 저장된 문서 예시:

```json
{
  "message_type": "MT103",
  "category": "1",
  "name": "Single Customer Credit Transfer",
  "field": ":20",
  "field_name": "Transaction Reference Number",
  "description": "각 은행에서 생성되는 고유 참조 번호",
  "text": "MTMT103 Single Customer Credit Transfer Field :20 Transaction Reference Number: 각 은행에서 생성되는 고유 참조 번호",
  "category_desc": "Customer Payments and Cheques - 고객 결제 및 수표"
}
```

### 3.3 텍스트 필드 구성

`text` 필드는 검색에 사용될 핵심 텍스트로, 다음 정보를 포함합니다:

- **MT 타입**: 예 "MT103"
- **메시지 이름**: 예 "Single Customer Credit Transfer"
- **필드 번호**: 예 ":20"
- **필드 이름**: 예 "Transaction Reference Number"
- **설명**: 예 "각 은행에서 생성되는 고유 참조 번호"

## 4. 임베딩 생성 과정

### 4.1 사용된 임베딩 모델

- **모델**: `text-embedding-3-small` (OpenAI)
- **임베딩 차원**: 1536차원
- **특징**: 비용 효율적이고 고품질의 임베딩 제공

### 4.2 임베딩 생성 Python 코드 (예시)

```python
from openai import OpenAI
import json

client = OpenAI()

def generate_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

# 문서 로드
with open('mt_documents.json', 'r', encoding='utf-8') as f:
    documents = json.load(f)

# 각 문서에 대해 임베딩 생성
for doc in documents:
    doc['embedding'] = generate_embedding(doc['text'])

# 결과 저장
with open('mt_documents_with_embeddings.json', 'w', encoding='utf-8') as f:
    json.dump(documents, f, ensure_ascii=False, indent=2)
```

### 4.3 임베딩 결과 예시

`mt_documents_with_embeddings.json`에서 확인 가능한 임베딩 배열 예시:

```json
{
  "message_type": "MT103",
  "field": ":20",
  "text": "MTMT103 Single Customer Credit Transfer...",
  "embedding": [
    -0.05855399742722511,
    -0.01034589670598507,
    0.015281813219189644,
    -0.02992827445268631,
    ... (1536차원)
  ]
}
```

## 5. ChromaDB 저장

### 5.1 ChromaDB란?

ChromaDB는 오픈소스 벡터 데이터베이스로, 의미적 검색에 최적화되어 있습니다.

### 5.2 저장 과정

```python
import chromadb
from chromadb.config import Settings

# 클라이언트 초기화
client = chromadb.PersistentClient(path="./data/chroma_db")

# 컬렉션 생성 (벡터 차원: 1536)
collection = client.get_or_create_collection(
    name="mt_fields",
    metadata={"hnsw:space": "cosine"}  # 코사인 유사도 사용
)

# 문서 추가
for doc in documents_with_embeddings:
    collection.add(
        ids=[f"{doc['message_type']}_{doc['field']}"],
        embeddings=[doc['embedding']],
        documents=[doc['text']],
        metadatas=[{
            "message_type": doc['message_type'],
            "field": doc['field'],
            "field_name": doc['field_name'],
            "description": doc['description']
        }]
    )
```

### 5.3 데이터베이스 구조

생성된 ChromaDB 파일:
- `chroma.sqlite3`: 메타데이터 저장
- `d71966bf-9c2c-4fca-bbfc-531a04e8c505/`: 벡터 데이터 저장
  - `header.bin`
  - `data_level0.bin`
  - `link_lists.bin`
  - `length.bin`

## 6. 검색 동작 원리

### 6.1 의미적 검색 프로세스

1. **사용자 쿼리 입력**: 예 "beneficiary bank details"
2. **쿼리 임베딩 생성**: same embedding model 사용
3. **유사도 계산**: ChromaDB에서 코사인 유사도 계산
4. **결과 반환**: 가장 유사한 문서들 반환

### 6.2 검색 Python 코드 예시

```python
def search_mt_fields(query, n_results=5):
    # 쿼리 임베딩 생성
    query_embedding = generate_embedding(query)
    
    # ChromaDB에서 검색
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    return results
```

### 6.3 검색 예시

| 검색 쿼리 | 검색 결과 |
|----------|----------|
| "beneficiary" | MT103 :59 Beneficiary, MT700 :59 Beneficiary 등 |
| "foreign exchange" | MT300 Foreign Exchange Deal, MT303 FX Option Confirmation |
| "cheque" | MT110 Cheque, MT400 Cheque/Payment Order |

## 7. 전체 파이프라인 요약

```
┌─────────────────────────────────────────────────────────────┐
│  1단계: 데이터 추출                                          │
│  ┌─────────────────┐    ┌────────────────────┐             │
│  │ mt_required_data │ → │ mt_documents.json  │             │
│  │ (Python Dict)   │    │ (2052개 문서)       │             │
│  └─────────────────┘    └────────────────────┘             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2단계: 임베딩 생성                                          │
│  ┌────────────────────┐    ┌────────────────────────────┐   │
│  │ mt_documents.json  │ → │ mt_documents_with_         │   │
│  │                    │    │ embeddings.json            │   │
│  └────────────────────┘    │ (1536차원 임베딩 포함)     │   │
│                             └────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3단계: ChromaDB 저장                                       │
│  ┌────────────────────────────┐    ┌──────────────────┐   │
│  │ mt_documents_with_         │ → │ ChromaDB         │   │
│  │ embeddings.json           │    │ (벡터 DB)        │   │
│  └────────────────────────────┘    └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  4단계: 의미적 검색                                          │
│  ┌──────────────┐    ┌─────────────────┐                   │
│  │ 사용자 쿼리   │ → │ 유사도 검색      │ → 검색 결과       │
│  └──────────────┘    └─────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

## 8. 관련 파일 목록

| 파일 | 설명 |
|------|------|
| `mt_required_data.py` | 35개 MT 타입의 필드 정의 (원본 데이터) |
| `mt_documents.json` | 추출된 문서 (2052개) |
| `mt_documents_with_embeddings.json` | 임베딩이 추가된 문서 |
| `data/chroma_db/` | ChromaDB 벡터 데이터베이스 |
| `streamlit_app.py` | 검색 기능이 포함된 웹 UI |

## 9. 의존성

임베딩 파이프라인에 필요한 Python 패키지:

```
openai          # OpenAI 임베딩 API
chromadb        # 벡터 데이터베이스
```

## 10. 참고 사항

- 임베딩 생성 시 OpenAI API 키 필요
- ChromaDB는 로컬에 저장되어 재사용 가능
- 코사인 유사도를 사용하여 의미적으로 유사한 필드 검색 가능
- 자연어 쿼리로 SWIFT 필드 정보 검색 가능
