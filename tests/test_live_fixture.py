"""실제 라이브 응답(저장된 픽스처)으로 파싱 파이프라인을 검증.

tests/fixtures/service07_dtl.json 은 실제 공공데이터포털
DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnDtlInq06 (item_seq=202106092, 타이레놀정500)
응답에서 인증키만 마스킹한 것. (네트워크 없이 실데이터 스키마 회귀 방지)
"""

import json
from decimal import Decimal
from pathlib import Path

from kdrug.client import _extract_items
from kdrug.parsers import parse_cost, parse_grn, parse_permit, parse_product

FIXTURE = Path(__file__).parent / "fixtures" / "service07_dtl.json"
EYAK_FIXTURE = Path(__file__).parent / "fixtures" / "e_yak_eun_yo_sample.json"
GRN_FIXTURE = Path(__file__).parent / "fixtures" / "grn03_sample.json"
COST_FIXTURE = Path(__file__).parent / "fixtures" / "dgamt_sample.json"


def test_parse_grn_on_live_grn03():
    """실제 낱알식별 grn03 응답으로 PillIdentity 매핑 검증."""
    payload = json.loads(GRN_FIXTURE.read_text(encoding="utf-8"))
    row = _extract_items(payload, "grn")[0]
    pill = parse_grn(row)
    assert pill.item_seq == "202106092"
    assert "타이레놀" in pill.item_name
    assert pill.drug_shape == "장방형"
    assert pill.is_capsule is False
    assert pill.length_long and pill.length_short  # 치수 채워짐
    assert pill.print_front                          # 식별표시
    assert pill.image_url.startswith("https://")


def test_dtl_envelope_without_response_wrapper():
    """Service07 은 {response:{...}} 없이 최상위 header/body 로 온다 — 처리되는지."""
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert set(payload.keys()) == {"header", "body"}
    assert payload["header"]["resultCode"] == "00"
    assert len(_extract_items(payload, "price")) == 1


def test_parse_product_on_live_detail():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    row = _extract_items(payload, "product")[0]
    dp = parse_product(row)
    # 라이브 실데이터: 타이레놀정500밀리그람(아세트아미노펜), item_seq=202106092
    assert dp.item_seq == "202106092"
    assert "타이레놀" in dp.item_name
    assert "아세트아미노펜" in dp.main_ingredient
    assert dp.atc_code == "N02BE01"
    assert dp.storage_method                      # 비어 있지 않음
    assert dp.item_permit_date == "20210823"
    assert dp.ee_doc_data.startswith("<DOC")      # 효능효과 HTML 문서
    assert dp.to_dict()["item_seq"] == "202106092"


def test_parse_cost_on_live_dgamt():
    """실제 심평원 약가(getDgamtList) 응답으로 DrugCost 매핑 검증 (리피토정20mg)."""
    payload = json.loads(COST_FIXTURE.read_text(encoding="utf-8"))
    row = _extract_items(payload, "cost")[0]
    c = parse_cost(row)
    assert c.mds_cd == "073400330"          # 보험코드 = 제품허가 EDI_CODE
    assert c.max_price == Decimal("688")    # 실제 상한가
    assert c.pay_type == "급여"
    assert "전문" in c.spc_gnl_type
    assert c.gnl_name_code                   # 주성분코드 채워짐


def test_parse_permit_on_e_yak_eun_yo():
    """e약은요(공식 명세 IROS_239) 필드 매핑 검증."""
    payload = json.loads(EYAK_FIXTURE.read_text(encoding="utf-8"))
    row = _extract_items(payload, "permit")[0]
    dp = parse_permit(row)
    assert dp.item_seq == "200003092"
    assert "아스피린" in dp.item_name
    assert dp.entp_name == "한미약품(주)"
    assert "혈전" in dp.efficacy           # efcyQesitm 효능
    assert "1일 1회" in dp.use_method      # useMethodQesitm 사용법
    assert "음주" in dp.warning            # atpnWarnQesitm 경고
    assert "병용" in dp.interaction        # intrcQesitm 상호작용
    assert "쇽" in dp.side_effect          # seQesitm 부작용
    assert "실온" in dp.storage            # depositMethodQesitm 보관법
    assert dp.image_url.startswith("https://nedrug.mfds.go.kr")
    assert dp.open_date == "20200901"
