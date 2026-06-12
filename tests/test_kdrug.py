"""네트워크 없이 동작하는 단위 테스트 — KdrugClient._http_get 을 mock 한다."""

import json
from decimal import Decimal

import pytest

from kdrug import (
    KdrugAuthError,
    KdrugClient,
    KdrugResponseError,
    parse_cost,
    parse_grn,
    parse_permit,
    parse_product,
)
from kdrug.client import _extract_items


# ── 가짜 응답 빌더 ────────────────────────────────────────────────────


def _envelope(items, result_code="00"):
    return {
        "response": {
            "header": {"resultCode": result_code, "resultMsg": "OK"},
            "body": {"items": items},
        }
    }


GRN_ROW = {
    "ITEM_SEQ": "199104100",
    "ITEM_NAME": "타이레놀정500밀리그람",
    "ENTP_NAME": "한국얀센",
    "LENG_LONG": "17.1",
    "LENG_SHORT": "7.0",
    "THICK": "5.8",
    "FORM_CODE_NAME": "정제",
    "DRUG_SHAPE": "장방형",
    "COLOR_CLASS1": "하양",
    "PRINT_FRONT": "TYLENOL",
    "ITEM_IMAGE": "https://example.com/x.jpg",
}
PERMIT_ROW = {  # e약은요 (getDrbEasyDrugList)
    "itemSeq": "199104100",
    "itemName": "타이레놀정500밀리그람",
    "entpName": "한국얀센",
    "efcyQesitm": "이 약은 해열 및 통증 완화에 사용합니다.",
    "useMethodQesitm": "성인은 1회 1~2정씩 복용합니다.",
    "depositMethodQesitm": "실온에서 보관하십시오.",
    "itemImage": "https://example.com/p.jpg",
}
PRODUCT_ROW = {  # 제품허가 상세 (getDrugPrdtPrmsnDtlInq06)
    "ITEM_SEQ": "199104100",
    "ITEM_NAME": "타이레놀정500밀리그람",
    "MAIN_ITEM_INGR": "아세트아미노펜",
    "STORAGE_METHOD": "기밀용기, 실온보관",
    "ATC_CODE": "N02BE01",
    "ITEM_PERMIT_DATE": "19910410",
    "EDI_CODE": "643503520",
}
COST_ROW = {  # 약가 (getDgamtList)
    "mdsCd": "643503520",
    "itmNm": "타이레놀정500밀리그람",
    "mxCprc": "88",
    "payTpNm": "급여",
    "spcGnlTpNm": "전문",
    "gnlNmCd": "243901ATB",
}


def _make_client(monkeypatch, mapping):
    """endpoint substring → items 매핑으로 _http_get 을 가로챈다."""
    client = KdrugClient(api_key="dummy-key")

    def fake_http_get(url):
        for needle, payload in mapping.items():
            if needle in url:
                return json.dumps(payload).encode("utf-8")
        return json.dumps(_envelope([])).encode("utf-8")

    monkeypatch.setattr(client, "_http_get", fake_http_get)
    return client


# ── 인증 ──────────────────────────────────────────────────────────────


def test_empty_api_key_raises():
    with pytest.raises(KdrugAuthError):
        KdrugClient(api_key="")


def test_from_env(monkeypatch):
    monkeypatch.setenv("KDRUG_API_KEY", "env-key")
    client = KdrugClient.from_env()
    assert client.api_key == "env-key"


def test_from_env_missing(monkeypatch):
    monkeypatch.delenv("KDRUG_API_KEY", raising=False)
    with pytest.raises(KdrugAuthError):
        KdrugClient.from_env()


# ── 파서 ──────────────────────────────────────────────────────────────


def test_parse_grn_basic():
    pill = parse_grn(GRN_ROW)
    assert pill.item_seq == "199104100"
    assert pill.length_long == 17.1
    assert pill.is_capsule is False  # '정제' 라 캡슐 아님


def test_parse_grn_capsule_detection():
    pill = parse_grn({"FORM_CODE_NAME": "경질캡슐제"})
    assert pill.is_capsule is True


def test_parse_permit_e_yak_eun_yo():
    permit = parse_permit(PERMIT_ROW)
    assert permit.item_seq == "199104100"
    assert "해열" in permit.efficacy
    assert permit.storage == "실온에서 보관하십시오."
    assert permit.image_url.endswith("p.jpg")


def test_parse_product_permit():
    product = parse_product(PRODUCT_ROW)
    assert product.main_ingredient == "아세트아미노펜"
    assert product.atc_code == "N02BE01"
    assert product.item_permit_date == "19910410"
    assert product.edi_code == "643503520"   # 보험코드 = 약가 mds_cd


def test_parse_cost_dgamt():
    cost = parse_cost(COST_ROW)
    assert cost.mds_cd == "643503520"
    assert cost.max_price == Decimal("88")
    assert cost.pay_type == "급여"
    assert cost.gnl_name_code == "243901ATB"


# ── _extract_items ────────────────────────────────────────────────────


def test_extract_items_list():
    assert _extract_items(_envelope([GRN_ROW]), "grn") == [GRN_ROW]


def test_extract_items_single_dict():
    payload = {"response": {"header": {"resultCode": "00"},
                            "body": {"items": {"item": GRN_ROW}}}}
    assert _extract_items(payload, "grn") == [GRN_ROW]


def test_extract_items_nodata_code_is_empty():
    assert _extract_items(_envelope([], result_code="03"), "grn") == []


def test_extract_items_error_code_raises():
    with pytest.raises(KdrugResponseError):
        _extract_items(_envelope([], result_code="22"), "grn")


# ── get_drug_info 통합 ────────────────────────────────────────────────


def test_get_drug_info_merges_four(monkeypatch):
    client = _make_client(monkeypatch, {
        "MdcinGrnIdntfcInfoService03": _envelope([GRN_ROW]),
        "DrbEasyDrugInfoService": _envelope([PERMIT_ROW]),
        "DrugPrdtPrmsnInfoService07": _envelope([PRODUCT_ROW]),
        "dgamtCrtrInfoService": _envelope([COST_ROW]),
    })
    result = client.get_drug_info(item_seq="199104100")
    assert result.ok
    assert set(result.info.sources) == {"grn", "permit", "product", "cost"}
    merged = result.info.to_dict()
    assert merged["item_name"] == "타이레놀정500밀리그람"
    assert merged["main_ingredient"] == "아세트아미노펜"   # 제품허가(product)
    assert merged["efficacy"].startswith("이 약은")          # e약은요(permit)
    assert merged["max_price"] == "88"                        # 약가(cost)


def test_get_drug_info_cost_joins_by_edi(monkeypatch):
    """약가는 제품허가 보험코드(EDI=mds_cd)로 조인된다 — URL 에 mdsCd 가 실려야 함."""
    seen = {}

    client = KdrugClient(api_key="dummy")

    def fake_http_get(url):
        if "dgamtCrtrInfoService" in url:
            seen["cost_url"] = url
            return json.dumps(_envelope([COST_ROW])).encode("utf-8")
        if "DrugPrdtPrmsnInfoService07" in url:
            return json.dumps(_envelope([PRODUCT_ROW])).encode("utf-8")
        return json.dumps(_envelope([])).encode("utf-8")

    monkeypatch.setattr(client, "_http_get", fake_http_get)
    result = client.get_drug_info(item_seq="199104100")
    assert result.info.cost is not None
    assert "mdsCd=643503520" in seen["cost_url"]   # 보험코드로 정확 조인
    assert "ServiceKey=" in seen["cost_url"]         # 심평원은 대문자 ServiceKey


def test_get_drug_info_partial_failure(monkeypatch):
    # product 만 오류 코드 → errors 에 기록, 나머지는 병합
    client = _make_client(monkeypatch, {
        "MdcinGrnIdntfcInfoService03": _envelope([GRN_ROW]),
        "DrbEasyDrugInfoService": _envelope([PERMIT_ROW]),
        "DrugPrdtPrmsnInfoService07": _envelope([], result_code="500"),
        "dgamtCrtrInfoService": _envelope([COST_ROW]),
    })
    result = client.get_drug_info(item_seq="199104100")
    assert result.ok
    assert "product" in result.errors
    assert result.info.product is None
    # grn, permit, 그리고 약가(cost, 품목명 폴백으로 조회됨)
    assert "grn" in result.info.sources and "permit" in result.info.sources
    assert "product" not in result.info.sources


def test_get_drug_info_all_empty(monkeypatch):
    client = _make_client(monkeypatch, {})  # 전부 빈 응답
    result = client.get_drug_info(item_seq="000000000")
    assert not result.ok
    assert result.info.is_empty


def test_get_drug_info_requires_arg(monkeypatch):
    client = _make_client(monkeypatch, {})
    with pytest.raises(ValueError):
        client.get_drug_info()


# ── 인증키 인코딩/디코딩 처리 ─────────────────────────────────────────


def _capture_url(monkeypatch, client):
    captured = {}

    def fake_http_get(url):
        captured["url"] = url
        return json.dumps(_envelope([])).encode("utf-8")

    monkeypatch.setattr(client, "_http_get", fake_http_get)
    return captured


def test_decoding_key_is_url_encoded(monkeypatch):
    # 원문(Decoding) 키의 +,/,= 는 URL 인코딩되어 들어가야 한다.
    client = KdrugClient(api_key="ab+cd/ef==")
    assert client.key_is_encoded is False  # '%' 없으니 자동으로 디코딩 키
    cap = _capture_url(monkeypatch, client)
    client.fetch_grn_raw(item_seq="1")
    assert "serviceKey=ab%2Bcd%2Fef%3D%3D" in cap["url"]


def test_encoding_key_inserted_verbatim(monkeypatch):
    # 이미 인코딩된(Encoding) 키는 그대로 — 이중 인코딩 금지.
    enc = "ab%2Bcd%2Fef%3D%3D"
    client = KdrugClient(api_key=enc)
    assert client.key_is_encoded is True  # '%' 있으니 자동으로 인코딩 키
    cap = _capture_url(monkeypatch, client)
    client.fetch_grn_raw(item_seq="1")
    assert f"serviceKey={enc}" in cap["url"]
    assert "%252B" not in cap["url"]  # 이중 인코딩 흔적 없음


def test_from_env_encoding_decoding_names(monkeypatch):
    monkeypatch.delenv("KDRUG_API_KEY", raising=False)
    monkeypatch.delenv("DRUG_API_KEY_DECODING", raising=False)
    monkeypatch.setenv("DRUG_API_KEY_ENCODING", "ab%2Bcd")
    client = KdrugClient.from_env(use_dotenv=False)
    assert client.api_key == "ab%2Bcd"
    assert client.key_is_encoded is True


# ── 서비스별 요청 파라미터 표기 (공식 스펙 준수) ──────────────────────


def test_request_param_casing_per_service(monkeypatch):
    """grn=소문자, e약은요=camelCase, 제품허가=소문자 (대문자로 보내면 필터 무시됨)."""
    client = KdrugClient(api_key="dummy")
    cap = _capture_url(monkeypatch, client)

    client.fetch_grn_raw(item_seq="123")
    assert "item_seq=123" in cap["url"] and "ITEM_SEQ=" not in cap["url"]

    client.fetch_permit_raw(item_seq="123")
    assert "itemSeq=123" in cap["url"]

    client.fetch_product_raw(item_seq="123")
    assert "item_seq=123" in cap["url"]

    client.fetch_cost_raw(mds_cd="643503520")
    assert "mdsCd=643503520" in cap["url"] and "_type=json" in cap["url"]
