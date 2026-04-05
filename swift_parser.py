import re
import uuid
from mt_required_data import MT_DATA


def parse_swift_message(full_message):
    blocks = {
        "block1": None,
        "block2": None,
        "block3": None,
        "block4": None,
        "block5": None,
    }

    block1_match = re.search(r"\{1:([^}]*)\}", full_message)
    if block1_match:
        blocks["block1"] = block1_match.group(1).strip()

    block2_match = re.search(r"\{2:([^}]*)\}", full_message)
    if block2_match:
        blocks["block2"] = block2_match.group(1).strip()

    block3_match = re.search(r"\{3:([^}]*)\}", full_message)
    if block3_match:
        blocks["block3"] = block3_match.group(1).strip()

    block4_match = re.search(r"\{4:([^}]+)\}", full_message, re.DOTALL)
    if block4_match:
        block4_raw = block4_match.group(1).strip()
        block4_raw = re.sub(r"-\}$", "", block4_raw)
        block4_raw = re.sub(r"-\s*\}", "}", block4_raw)
        blocks["block4"] = block4_raw.strip()

    block5_match = re.search(r"\{5:([^}]*)\}", full_message)
    if block5_match:
        blocks["block5"] = block5_match.group(1).strip()

    return blocks


def validate_block1(block1_data):
    result = {
        "valid": False,
        "format": block1_data,
        "sender_bic": None,
        "service_id": None,
        "errors": [],
    }

    if not block1_data:
        result["errors"].append("Block 1 (Basic Header)이 없습니다")
        return result

    pattern = r"^F(\d{2})([A-Z]{6}[A-Z0-9]{5})(\d+)$"
    match = re.match(pattern, block1_data)

    if not match:
        pattern2 = r"^F(\d{2})([A-Z]{4}[A-Z]{2}[A-Z0-9]{3,11})(\d{12,})$"
        match = re.match(pattern2, block1_data)

    if not match:
        pattern3 = r"^F(\d{2})([A-Z0-9]+)(\d+)$"
        match = re.match(pattern3, block1_data)
        if match:
            result["valid"] = True
            result["service_id"] = match.group(1)
            result["sender_bic"] = match.group(2)
        else:
            result["errors"].append("Block 1 형식이 올바르지 않습니다")
        return result

    result["valid"] = True
    result["service_id"] = match.group(1)
    result["sender_bic"] = match.group(2)

    return result

    pattern = r"^F(\d{2})([A-Z]{4}[A-Z]{2}[A-Z0-9]{5})(\d{12})$"
    match = re.match(pattern, block1_data)

    if not match:
        result["errors"].append(
            "Block 1 형식이 올바르지 않습니다. 예상 형식: F01[BIC8][BIC3][12자리]"
        )
        return result

    result["valid"] = True
    result["service_id"] = match.group(1)
    result["sender_bic"] = match.group(2)

    return result


def validate_block2(block2_data):
    result = {
        "valid": False,
        "direction": None,
        "message_type": None,
        "receiver_bic": None,
        "errors": [],
    }

    if not block2_data:
        result["errors"].append("Block 2 (Application Header)이 없습니다")
        return result

    direction = block2_data[0] if block2_data else None
    if direction not in ["I", "O"]:
        result["errors"].append("Direction flag가 올바르지 않습니다 (I 또는 O 필요)")
        return result

    message_type_match = re.match(r"^[IO](\d{3})", block2_data)
    if not message_type_match:
        result["errors"].append("메시지 타입을 식별할 수 없습니다")
        return result

    message_type = message_type_match.group(1)
    if message_type not in MT_DATA and message_type != "103":
        result["errors"].append(f"지원하지 않는 메시지 타입입니다: MT{message_type}")
        return result

    result["valid"] = True
    result["direction"] = direction
    result["message_type"] = f"MT{message_type}"

    if len(block2_data) > 4:
        remaining = block2_data[4:]
        bic_match = re.match(r"([A-Z]{4}[A-Z]{2}[A-Z0-9]{3,11})", remaining)
        if bic_match:
            result["receiver_bic"] = bic_match.group(1)

    return result


def validate_block3(block3_data):
    result = {"valid": True, "uetr": None, "service_code": None, "errors": []}

    if not block3_data:
        return result

    uetr_match = re.search(r"\{108:([A-Za-z0-9-]+)\}", block3_data)
    if uetr_match:
        uetr = uetr_match.group(1)
        uetr_clean = uetr.replace("-", "")
        if len(uetr_clean) != 32 and len(uetr_clean) != 36:
            result["valid"] = False
            result["errors"].append(
                "UETR 형식이 올바르지 않습니다 (32자리 또는 36자리 필요)"
            )
        else:
            result["uetr"] = uetr

    service_match = re.search(r"\{103:(\w+)\}", block3_data)
    if service_match:
        result["service_code"] = service_match.group(1)

    return result


def parse_mt_fields(text):
    fields = {}
    text = text.replace(" -", "").strip()

    pattern = r":(\d+[A-Z]?):"
    parts = re.split(pattern, text)
    parts = [p for p in parts if p]

    for i in range(0, len(parts) - 1, 2):
        field_num = parts[i]
        if i + 1 < len(parts):
            value = parts[i + 1].strip()
            fields[field_num] = value

    return fields


def validate_block4(block4_data, mt_type):
    result = {
        "valid": False,
        "mt_type": mt_type,
        "fields": [],
        "missing_fields": [],
        "errors": [],
    }

    if not block4_data:
        result["errors"].append("Block 4 (Text)가 없습니다")
        return result

    if mt_type not in MT_DATA:
        result["errors"].append(f"알 수 없는 MT 타입: {mt_type}")
        return result

    mt_info = MT_DATA[mt_type]
    user_fields = parse_mt_fields(block4_data)

    for field in mt_info["fields"]:
        field_base = (
            field["field"].replace(":", "").rstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        )
        field_tag = field["field"]

        field_found = False
        for user_field_key in user_fields.keys():
            user_field_base = user_field_key.rstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            if user_field_base == field_base:
                field_found = True
                break

        if field_found:
            validation = "정상"
        elif field["required"]:
            validation = "필수누락"
            result["missing_fields"].append(field_tag)
        else:
            validation = "선택"

        result["fields"].append(
            {
                "field": field_tag,
                "name": field["name"],
                "description": field["description"],
                "required": field["required"],
                "validation": validation,
            }
        )

    if not result["missing_fields"]:
        result["valid"] = True
    else:
        result["errors"].append(
            f"필수 필드 누락: {', '.join(result['missing_fields'])}"
        )

    return result

    if mt_type not in MT_DATA:
        result["errors"].append(f"알 수 없는 MT 타입: {mt_type}")
        return result

    mt_info = MT_DATA[mt_type]
    user_fields = parse_mt_fields(block4_data)

    for field in mt_info["fields"]:
        field_key = field["field"].replace(":", "")
        field_tag = field["field"]

        if field_key in user_fields:
            validation = "정상"
        elif field["required"]:
            validation = "필수누락"
            result["missing_fields"].append(field_tag)
        else:
            validation = "선택"

        result["fields"].append(
            {
                "field": field_tag,
                "name": field["name"],
                "description": field["description"],
                "required": field["required"],
                "validation": validation,
            }
        )

    if not result["missing_fields"]:
        result["valid"] = True
    else:
        result["errors"].append(
            f"필수 필드 누락: {', '.join(result['missing_fields'])}"
        )

    return result


def validate_block5(block5_data):
    result = {"valid": False, "checksum": None, "errors": []}

    if not block5_data:
        result["errors"].append("Block 5 (Trailer)가 없습니다 (경고)")
        return result

    chk_match = re.search(r"\{CHK:([A-Fa-f0-9]+)\}", block5_data)
    if chk_match:
        result["valid"] = True
        result["checksum"] = chk_match.group(1)
    else:
        chk_match2 = re.search(r"CHK:([A-Fa-f0-9]+)", block5_data)
        if chk_match2:
            result["valid"] = True
            result["checksum"] = chk_match2.group(1)
        else:
            result["errors"].append("체크섬(CHK) 정보가 없습니다")

    return result

    chk_match = re.search(r"\{CHK:([A-Fa-f0-9]+)\}", block5_data)
    if chk_match:
        result["valid"] = True
        result["checksum"] = chk_match.group(1)
    else:
        result["errors"].append("체크섬(CHK) 정보가 없습니다")

    return result


def validate_full_message(full_message):
    blocks = parse_swift_message(full_message)

    block1_result = validate_block1(blocks["block1"])
    block2_result = validate_block2(blocks["block2"])
    block3_result = validate_block3(blocks["block3"])
    block5_result = validate_block5(blocks["block5"])

    mt_type = "MT103"
    if block2_result["valid"] and block2_result["message_type"]:
        mt_type = block2_result["message_type"]

    block4_result = validate_block4(blocks["block4"], mt_type)

    results = {
        "block1": block1_result,
        "block2": block2_result,
        "block3": block3_result,
        "block4": block4_result,
        "block5": block5_result,
        "overall_valid": block1_result["valid"]
        and block2_result["valid"]
        and block4_result["valid"],
        "mt_type_detected": mt_type,
    }

    all_errors = []
    all_errors.extend(block1_result["errors"])
    all_errors.extend(block2_result["errors"])
    all_errors.extend(block3_result["errors"])
    all_errors.extend(block4_result["errors"])
    all_errors.extend(block5_result["errors"])

    results["all_errors"] = all_errors

    return results


def get_block_summary(result):
    summary_parts = []

    if result["block1"]["valid"]:
        summary_parts.append(
            f"Block 1: ✓ 송신 BIC = {result['block1'].get('sender_bic', 'N/A')}"
        )
    else:
        summary_parts.append(f"Block 1: ✗ {result['block1']['errors'][0]}")

    if result["block2"]["valid"]:
        summary_parts.append(
            f"Block 2: ✓ {result['block2']['message_type']}, 수신 = {result['block2'].get('receiver_bic', 'N/A')}"
        )
    else:
        summary_parts.append(f"Block 2: ✗ {result['block2']['errors'][0]}")

    if result["block3"]["valid"]:
        uetr = result["block3"].get("uetr", "N/A")
        summary_parts.append(
            f"Block 3: ✓ UETR = {uetr[:8]}..." if uetr else "Block 3: ✓ (없음)"
        )

    if result["block4"]["valid"]:
        summary_parts.append(f"Block 4: ✓ 모든 필수 필드 OK")
    else:
        missing = result["block4"].get("missing_fields", [])
        summary_parts.append(f"Block 4: ✗ 누락 필드 {len(missing)}개")

    if result["block5"]["valid"]:
        summary_parts.append(
            f"Block 5: ✓ Checksum = {result['block5'].get('checksum', 'N/A')}"
        )
    else:
        summary_parts.append(f"Block 5: ✗ {result['block5']['errors'][0]}")

    return summary_parts


if __name__ == "__main__":
    test_message = """{1:F01SOGEFRPPAXXX0070970817}{2:O1031734150713DEUTDEFFBXXX00739698421607131634N}{3:{113:SEPA}{108:12345678-1234-1234-1234-123456789012}}{4:
:20:UNIQUEREFOFTRX16
:23B:CRED
:32A:180724EUR735927,75
:33B:EUR735927,75
:50A:/DE37500700100950596700
DEUTDEFF
:59:/FR7630003034950005005419318
CHARLES DUPONT COMPANY
RUE GENERAL DE GAULLE, 21
75013 PARIS
:71A:SHA
-}{5:{CHK:D628FE0165A7}}"""

    result = validate_full_message(test_message)

    print("=" * 60)
    print("검증 결과")
    print("=" * 60)

    for summary in get_block_summary(result):
        print(summary)

    print("=" * 60)
    if result["overall_valid"]:
        print("✅ 전체 검증 통과")
    else:
        print("❌ 검증 실패")
        print("\n오류 목록:")
        for error in result["all_errors"]:
            print(f"  - {error}")
