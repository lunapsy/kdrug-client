"""공급중단·생산수입실적·유통상태(get_market_status) 단위 테스트 — 네트워크 없이 동작."""

import json
from decimal import Decimal

import pytest

from kdrug import (
    KdrugClient,
    MarketStatus,
    parse_production,
    parse_supply,
)
from kdrug.client import _extract_items


# ── 실제 라이브 응답 기반 픽스처 (2026-07 실측) ───────────────────────


SUPPLY_ROW = {  # 공급중단 (getMdcinPrdctnIncmeSuplyList) — items 는 평평한 리스트
    "REPORT_PGS_CODE": "처리완료",
    "SUSPEND_REPORT_SEQ": "2015000038",
    "SUSPEND_REPORT_FLAG": "수입",
    "SUPPLY_YN": "Y",
    "ENTP_SEQ": "19920105",
    "ENTP_NAME": "한국쿄와하코기린(주)",
    "ITEM_SEQ": "200209631",
    "ITEM_NAME": "레나젤정800(세벨라머염산염)",
    "EDI_CODE": "8806663000324",
    "LAST_SUPPLY_DATE": "20150713",
    "SUSPEND_DATE": "20150930",
    "SUSPEND_FLAG": "2",
    "INV_DATE": "20150728",
    "INV_QTY": "3137",
    "SUSPEND_REASON": "판매 공급계약 종료에 따라 수입 종료",
    "SUPPLY_LACK_PACI": "대체 약제가 국내 타 제약사에서 공급 중",
    "SUPPLY_PLAN": "해당사항 없음",
    "REPORT_DATE": "20150729",
    "BIZRNO": "1148142327",
}
PRODUCTION_ROW = {  # 생산·수입실적 (getMdcinPrdctnImportrstList02)
    "ITEM_SEQ": "195500005",
    "DATE_YEAR": "2024",
    "ITEM_NAME": "중외5%포도당생리식염액",
    "ENTP_NAME": "제이더블유중외제약(주)",
    "ENTP_SEQ": "19550004",
    "RESULT_PART": "생산",
    "AMT": "4000.39",
    "BIZRNO": "1188102477",
}


def _flat_envelope(items, result_code="00"):
    """공급중단·실적 API 는 response 래퍼 없이 header/body 가 최상위."""
    return {
        "header": {"resultCode": result_code, "resultMsg": "NORMAL SERVICE."},
        "body": {"numOfRows": 10, "pageNo": 1, "totalCount": len(items),
                 "items": items},
    }


def _make_client(monkeypatch, mapping):
    """endpoint substring → payload 매핑으로 _http_get 을 가로챈다."""
    client = KdrugClient(api_key="dummy-key")

    def fake_http_get(url):
        for needle, payload in mapping.items():
            if needle in url:
                return json.dumps(payload).encode("utf-8")
        return json.dumps(_flat_envelope([])).encode("utf-8")

    monkeypatch.setattr(client, "_http_get", fake_http_get)
    return client


# ── 파서 ──────────────────────────────────────────────────────────────


def test_parse_supply_basic():
    r = parse_supply(SUPPLY_ROW)
    assert r.item_seq == "200209631"
    assert r.edi_code == "8806663000324"
    assert r.suspend_date == "20150930"
    assert r.inventory_qty == "3137"
    assert r.is_suspended is True          # SUSPEND_FLAG == "2"


def test_parse_supply_not_suspended():
    r = parse_supply({**SUPPLY_ROW, "SUSPEND_FLAG": "1"})
    assert r.is_suspended is False


def test_parse_production_basic():
    r = parse_production(PRODUCTION_ROW)
    assert r.item_seq == "195500005"
    assert r.year == "2024"
    assert r.is_production is True
    assert r.is_import is False
    assert r.amount == Decimal("4000.39")


def test_parse_production_amount_krw():
    r = parse_production(PRODUCTION_ROW)
    assert r.amount_krw == Decimal("4000.39") * 1_000_000  # 백만원 → 원


def test_parse_production_import_amount_krw_is_none():
    r = parse_production({**PRODUCTION_ROW, "RESULT_PART": "수입"})
    assert r.is_import is True
    assert r.amount_krw is None            # 달러는 환율 없이 환산 불가


# ── items 중첩 구조 ([{"item": {...}}]) 흡수 ─────────────────────────


def test_extract_items_unwraps_nested_item_list():
    payload = _flat_envelope([{"item": PRODUCTION_ROW}, {"item": PRODUCTION_ROW}])
    items = _extract_items(payload, "production")
    assert len(items) == 2
    assert items[0]["ITEM_SEQ"] == "195500005"   # 껍질이 벗겨져 있어야 함


def test_extract_items_flat_list_unchanged():
    payload = _flat_envelope([SUPPLY_ROW])
    items = _extract_items(payload, "supply")
    assert items == [SUPPLY_ROW]


# ── fetch_supply / fetch_production ──────────────────────────────────


def test_fetch_supply(monkeypatch):
    client = _make_client(monkeypatch, {
        "MdcinPrdctnIncmeSuplyService2": _flat_envelope([SUPPLY_ROW]),
    })
    reports = client.fetch_supply(item_name="레나젤")
    assert len(reports) == 1
    assert reports[0].is_suspended is True


def test_fetch_production_nested(monkeypatch):
    client = _make_client(monkeypatch, {
        "MdcinPrdctnImportAcmsltService02": _flat_envelope([{"item": PRODUCTION_ROW}]),
    })
    records = client.fetch_production(item_name="중외")
    assert len(records) == 1
    assert records[0].amount == Decimal("4000.39")


# ── get_market_status ────────────────────────────────────────────────


def test_market_status_marketed(monkeypatch):
    """실적 있음 + 중단 없음 = 유통 중."""
    client = _make_client(monkeypatch, {
        "MdcinPrdctnImportAcmsltService02": _flat_envelope([{"item": PRODUCTION_ROW}]),
    })
    result = client.get_market_status(
        item_seq="195500005", item_name="중외5%포도당생리식염액")
    assert result.ok
    assert result.status.has_record is True
    assert result.status.is_suspended is False
    assert result.status.is_marketed is True
    assert result.status.latest_year == "2024"
    assert result.status.latest_amount == Decimal("4000.39")


def test_market_status_suspended(monkeypatch):
    """실적 있어도 공급중단 보고 있으면 유통 아님."""
    prod = {**PRODUCTION_ROW, "ITEM_SEQ": "200209631"}
    client = _make_client(monkeypatch, {
        "MdcinPrdctnImportAcmsltService02": _flat_envelope([{"item": prod}]),
        "MdcinPrdctnIncmeSuplyService2": _flat_envelope([SUPPLY_ROW]),
    })
    result = client.get_market_status(
        item_seq="200209631", item_name="레나젤정800(세벨라머염산염)")
    assert result.status.has_record is True
    assert result.status.is_suspended is True
    assert result.status.is_marketed is False


def test_market_status_permit_only(monkeypatch):
    """허가만 있고 실적·중단 모두 없음 = 주문 연동 시 걸러낼 품목."""
    client = _make_client(monkeypatch, {})
    result = client.get_market_status(item_seq="999999999", item_name="유령약품정")
    assert result.status.is_marketed is False
    assert result.status.has_record is False
    assert not result.ok                    # 아무 데이터도 확인 못 함


def test_market_status_filters_by_item_seq(monkeypatch):
    """동명 다른 품목(ITEM_SEQ 불일치) 레코드는 제외해야 한다."""
    other = {**PRODUCTION_ROW, "ITEM_SEQ": "888888888"}
    client = _make_client(monkeypatch, {
        "MdcinPrdctnImportAcmsltService02": _flat_envelope(
            [{"item": PRODUCTION_ROW}, {"item": other}]),
    })
    result = client.get_market_status(
        item_seq="195500005", item_name="중외5%포도당생리식염액")
    assert len(result.status.records) == 1
    assert result.status.records[0].item_seq == "195500005"


def test_market_status_yearly_sum(monkeypatch):
    """같은 연도 복수 레코드(포장단위별)는 합산된다."""
    r1 = {**PRODUCTION_ROW, "AMT": "100.5"}
    r2 = {**PRODUCTION_ROW, "AMT": "200.5"}
    old = {**PRODUCTION_ROW, "DATE_YEAR": "2023", "AMT": "999"}
    client = _make_client(monkeypatch, {
        "MdcinPrdctnImportAcmsltService02": _flat_envelope(
            [{"item": r1}, {"item": r2}, {"item": old}]),
    })
    result = client.get_market_status(
        item_seq="195500005", item_name="중외5%포도당생리식염액")
    assert result.status.latest_year == "2024"
    assert result.status.latest_amount == Decimal("301.0")
    assert len(result.status.records) == 3   # 원본은 전부 보존


def test_market_status_resolve_failure(monkeypatch):
    """item_seq 만 주고 제품허가에서 품목명 해석 실패(허가취하) → errors 에 안내."""
    client = _make_client(monkeypatch, {})
    result = client.get_market_status(item_seq="200209631")
    assert not result.ok
    assert "resolve" in result.errors


def test_market_status_requires_key():
    client = KdrugClient(api_key="dummy-key")
    with pytest.raises(ValueError):
        client.get_market_status()


# ── to_dict ───────────────────────────────────────────────────────────


def test_market_status_to_dict():
    s = MarketStatus(item_seq="1", item_name="테스트", has_record=True,
                     latest_year="2024", latest_amount=Decimal("10.5"), part="생산")
    d = s.to_dict()
    assert d["is_marketed"] is True
    assert d["latest_amount"] == "10.5"     # Decimal 은 문자열로 직렬화


# ── get_drug_info(with_market=True) — 통합 평탄화 ─────────────────────


PRODUCT_ROW_JW = {  # 제품허가 상세 (품목명 해석용)
    "ITEM_SEQ": "195500005",
    "ITEM_NAME": "중외5%포도당생리식염액",
    "ENTP_NAME": "제이더블유중외제약(주)",
    "MAIN_ITEM_INGR": "포도당",
}


def _envelope(items, result_code="00"):
    return {
        "response": {
            "header": {"resultCode": result_code, "resultMsg": "OK"},
            "body": {"items": items},
        }
    }


def test_get_drug_info_with_market_flattens(monkeypatch):
    """with_market=True 면 유통 상태 스칼라가 to_dict() 평탄화에 포함된다."""
    client = _make_client(monkeypatch, {
        "DrugPrdtPrmsnInfoService07": _envelope([PRODUCT_ROW_JW]),
        "MdcinPrdctnImportAcmsltService02": _flat_envelope([{"item": PRODUCTION_ROW}]),
    })
    result = client.get_drug_info(item_seq="195500005", with_market=True,
                                  with_cost=False)
    info = result.info
    assert info.market is not None
    assert info.market.is_marketed is True
    assert "market" in info.sources

    d = info.to_dict()
    assert d["is_marketed"] is True
    assert d["has_record"] is True
    assert d["latest_year"] == "2024"
    assert d["latest_amount"] == "4000.39"
    assert d["market_part"] == "생산"
    assert d["is_suspended"] is False


def test_get_drug_info_without_market_default(monkeypatch):
    """기본값(with_market=False)은 기존과 동일 — market 없음, 평탄화에도 없음."""
    client = _make_client(monkeypatch, {
        "DrugPrdtPrmsnInfoService07": _envelope([PRODUCT_ROW_JW]),
    })
    result = client.get_drug_info(item_seq="195500005", with_cost=False)
    assert result.info.market is None
    assert "market" not in result.info.sources
    assert "is_marketed" not in result.info.to_dict()


def test_market_status_standalone_refresh(monkeypatch):
    """통합 조회와 별개로 get_market_status 만 다시 호출해 상태를 갱신할 수 있다."""
    client = _make_client(monkeypatch, {
        "DrugPrdtPrmsnInfoService07": _envelope([PRODUCT_ROW_JW]),
        "MdcinPrdctnImportAcmsltService02": _flat_envelope([{"item": PRODUCTION_ROW}]),
    })
    # 1) 통합 조회로 한 번
    info = client.get_drug_info(item_seq="195500005", with_market=True,
                                with_cost=False).info
    assert info.market.is_marketed is True

    # 2) 이후 공급중단 보고가 새로 올라온 상황 시뮬레이션
    suspended = {**SUPPLY_ROW, "ITEM_SEQ": "195500005",
                 "ITEM_NAME": "중외5%포도당생리식염액"}
    client2 = _make_client(monkeypatch, {
        "MdcinPrdctnImportAcmsltService02": _flat_envelope([{"item": PRODUCTION_ROW}]),
        "MdcinPrdctnIncmeSuplyService2": _flat_envelope([suspended]),
    })
    refreshed = client2.get_market_status(
        item_seq="195500005", item_name="중외5%포도당생리식염액")
    assert refreshed.status.is_suspended is True
    assert refreshed.status.is_marketed is False   # 상태만 따로 갱신됨
