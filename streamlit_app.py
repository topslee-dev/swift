import streamlit as st
import pandas as pd
import re
import chromadb
from mt_required_data import MT_DATA
from swift_parser import validate_full_message, get_block_summary, parse_swift_message

st.set_page_config(page_title="SWIFT MT 전문 검증기", page_icon="🏦", layout="wide")


def parse_mt_message(message_text):
    fields = {}
    pattern = r":(\d+[A-Z]?):(.+)"
    matches = re.findall(pattern, message_text)
    for match in matches:
        field_num = match[0]
        value = match[1].strip()
        fields[field_num] = value
    return fields


def validate_mt_message(mt_type, message_text):
    if mt_type not in MT_DATA:
        return {"error": f"알 수 없는 MT 타입: {mt_type}"}

    mt_info = MT_DATA[mt_type]
    user_fields = parse_mt_message(message_text)

    results = []
    for field in mt_info["fields"]:
        field_key = field["field"].replace(":", "")
        field_tag = field["field"]

        if field_key in user_fields:
            validation = "✓ 정상"
        elif field["required"]:
            validation = "✗ 필수누락"
        else:
            validation = "- 선택"

        results.append(
            {
                "필드": field_tag,
                "필드명": field["name"],
                "설명": field["description"],
                "필수": "필수" if field["required"] else "선택",
                "검증": validation,
            }
        )

    return {
        "mt_type": mt_type,
        "name": mt_info["name"],
        "results": results,
        "user_fields": user_fields,
    }


def get_mt_field_info(mt_type):
    if mt_type not in MT_DATA:
        return None

    mt_info = MT_DATA[mt_type]
    fields = []
    for field in mt_info["fields"]:
        fields.append(
            {
                "필드": field["field"],
                "필드명": field["name"],
                "길이": field.get("length", ""),
                "설명": field["description"],
                "필수": "필수" if field["required"] else "선택",
            }
        )
    return {
        "mt_type": mt_type,
        "name": mt_info["name"],
        "description": mt_info["description"],
        "fields": fields,
    }


def search_mt_fields(query, n_results=10):
    try:
        client = chromadb.PersistentClient(path="data/chroma_db")
        collection = client.get_collection("swift_mt_messages")

        results = collection.query(query_texts=[query], n_results=n_results)

        search_results = []
        if results["documents"] and results["documents"][0]:
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                search_results.append(
                    {
                        "메시지타입": meta["message_type"],
                        "필드": meta["field"],
                        "필드명": meta["field_name"],
                        "설명": doc.split(": ")[-1] if ": " in doc else doc,
                    }
                )

        return search_results
    except Exception as e:
        st.error(f"검색 오류: {str(e)}")
        return []


st.title("🏦 SWIFT MT 전문 검증기")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📋 전문별 설명 조회", "✅ INPUT 전문 검증", "🔍 의미적 검색", "📨 전체 전문 검증"]
)

with tab1:
    st.header("전문별 설명 조회")

    mt_types = sorted(MT_DATA.keys())
    selected_mt = st.selectbox(
        "MT 타입 선택",
        mt_types,
        index=mt_types.index("MT103") if "MT103" in mt_types else 0,
        key="select_mt_type",
    )

    if selected_mt:
        info = get_mt_field_info(selected_mt)

        st.subheader(f"{info['mt_type']} - {info['name']}")
        st.caption(info["description"])

        df = pd.DataFrame(info["fields"])
        st.dataframe(df, width="stretch", hide_index=True)

        required_fields = [f["필드"] for f in info["fields"] if f["필수"] == "필수"]
        st.info(f"📌 필수 필드: {', '.join(required_fields)}")

with tab2:
    st.header("INPUT 전문 검증")

    col1, col2 = st.columns([1, 2])

    with col1:
        mt_type_input = st.selectbox(
            "MT 타입 선택",
            mt_types,
            index=mt_types.index("MT103") if "MT103" in mt_types else 0,
            key="select_mt_validate",
        )

    with col2:
        st.caption(
            "예시:\n:20: REF123456\n:32A: 230726EUR1000\n:50K: /1234567890\nJohn Doe\n:59: Jane Smith\n:71A: OUR"
        )

    message_input = st.text_area(
        "전문 입력",
        height=200,
        placeholder=":20: REF123456\n:32A: 230726EUR1000\n:50K: /1234567890\nJohn Doe\n:59: Jane Smith\n:71A: OUR",
    )

    if st.button("검증하기", key="btn_validate_block4"):
        if message_input:
            result = validate_mt_message(mt_type_input, message_input)

            if "error" in result:
                st.error(result["error"])
            else:
                st.subheader(f"검증 결과: {result['mt_type']} - {result['name']}")

                df = pd.DataFrame(result["results"])
                st.dataframe(df, width="stretch", hide_index=True)

                missing = [r for r in result["results"] if r["검증"] == "✗ 필수누락"]
                if missing:
                    st.error(
                        f"⚠️ 누락된 필수 필드: {', '.join([r['필드'] for r in missing])}"
                    )
                else:
                    st.success("✅ 모든 필수 필드가 입력되었습니다!")
        else:
            st.warning("전문을 입력해주세요.")

with tab3:
    st.header("의미적 검색")

    col1, col2 = st.columns([5, 1])
    with col1:
        search_query = st.text_input(
            "검색어 입력",
            placeholder="예: beneficiary, foreign exchange, securities...",
            key="search_input",
            label_visibility="collapsed",
        )
    with col2:
        search_button = st.button(
            "🔍 검색", key="search_button", use_container_width=True
        )

    if search_button and search_query:
        results = search_mt_fields(search_query)

        if results:
            st.subheader(f"검색 결과 ({len(results)}개)")

            df = pd.DataFrame(results)
            st.dataframe(df, width="stretch", hide_index=True)
        else:
            st.warning("검색 결과가 없습니다.")
    elif search_button and not search_query:
        st.warning("검색어를 입력해주세요.")

    if search_query and not search_button:
        results = search_mt_fields(search_query)

        if results:
            st.subheader(f"검색 결과 ({len(results)}개)")

            df = pd.DataFrame(results)
            st.dataframe(df, width="stretch", hide_index=True)
        else:
            st.warning("검색 결과가 없습니다.")

    st.caption(
        "💡 팁: 'beneficiary', 'foreign exchange', 'documentary credit', 'securities', 'cheque' 등으로 검색해보세요."
    )

with tab4:
    st.header("전체 전문 검증 (5개 블록)")

    st.caption("""
    예시 전문 형식:
    {1:F01SOGEFRPPAXXX0070970817}
    {2:O1031734150713DEUTDEFFBXXX00739698421607131634N}
    {3:{108:12345678-1234-1234-1234-123456789012}}
    {4:
    :20:UNIQUEREF
    :23B:CRED
    :32A:180724EUR1000,00
    :50K:/1234567890
    :59:/9876543210
    :71A:SHA
    -}
    {5:{CHK:D628FE0165A7}}
    """)

    full_message_input = st.text_area(
        "5개 블록 전체 전문 입력",
        height=300,
        placeholder="""{1:F01SOGEFRPPAXXX0070970817}{2:O1031734150713DEUTDEFFBXXX00739698421607131634N}{3:{108:12345678-1234-1234-1234-123456789012}}{4:
:20:UNIQUEREF
:23B:CRED
:32A:180724EUR1000,00
:50K:/1234567890
:59:/9876543210
:71A:SHA
-}{5:{CHK:D628FE0165A7}}""",
    )

    if st.button("전체 전문 검증하기", key="btn_validate_full"):
        if full_message_input:
            result = validate_full_message(full_message_input)

            st.subheader("📊 검증 결과 요약")

            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                if result["block1"]["valid"]:
                    st.success("✅ Block 1")
                else:
                    st.error("❌ Block 1")

            with col2:
                if result["block2"]["valid"]:
                    st.success("✅ Block 2")
                else:
                    st.error("❌ Block 2")

            with col3:
                if result["block3"]["valid"]:
                    st.success("✅ Block 3")
                else:
                    st.warning("⚠️ Block 3")

            with col4:
                if result["block4"]["valid"]:
                    st.success("✅ Block 4")
                else:
                    st.error("❌ Block 4")

            with col5:
                if result["block5"]["valid"]:
                    st.success("✅ Block 5")
                else:
                    st.warning("⚠️ Block 5")

            st.divider()

            for summary in get_block_summary(result):
                if "✓" in summary:
                    st.write(f"✅ {summary}")
                elif "✗" in summary:
                    st.write(f"❌ {summary}")

            st.divider()

            if result["overall_valid"]:
                st.success("🎉 전체 검증 통과!")
            else:
                st.error("❌ 검증 실패")

                if result["all_errors"]:
                    st.subheader("오류 목록:")
                    for i, error in enumerate(result["all_errors"], 1):
                        st.write(f"{i}. {error}")

            if result["block4"]["fields"]:
                st.subheader("Block 4 (Text) 상세 검증 결과")
                block4_df = pd.DataFrame(result["block4"]["fields"])
                st.dataframe(block4_df, width="stretch", hide_index=True)

                missing = result["block4"].get("missing_fields", [])
                if missing:
                    st.error(f"⚠️ 누락된 필수 필드: {', '.join(missing)}")
        else:
            st.warning("전문을 입력해주세요.")

st.sidebar.header("ℹ️ 정보")
st.sidebar.write("""
**SWIFT MT 전문 검증기**
- 35개 MT 타입 지원
- 5개 블록 전체 검증
- 필수 필드 검증
- 의미적 검색 기능
""")

st.sidebar.header("📐 길이 형식 Legend")
st.sidebar.write("""
| 기호 | 의미 |
|------|------|
| **n** | 숫자 |
| **a** | 영문자 |
| **c** | 문자 |
| **x** | 영문/숫자 |
| **!n** | n자리 필수 (예: 6!n = 6자리) |
| **n*m** | n~m회 반복 |
| **A/D** | A 또는 D 옵션 |
| **ISIN** | 국제증권식별번호 |
""")
