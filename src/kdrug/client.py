"""KdrugClient — 공공데이터포털 의약품 6종 OpenAPI 통합 클라이언트.

엔드포인트 (data.go.kr, 2026-07 현행):
  - 낱알식별     MdcinGrnIdntfcInfoService03/getMdcinGrnIdntfcInfoList03
  - 허가정보     DrbEasyDrugInfoService/getDrbEasyDrugList (e약은요)
  - 제품허가     DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnDtlInq06
  - 약가기준     dgamtCrtrInfoService1.2/getDgamtList (심평원 B551182)
  - 공급중단     MdcinPrdctnIncmeSuplyService2/getMdcinPrdctnIncmeSuplyList
  - 생산·수입실적 MdcinPrdctnImportAcmsltService02/getMdcinPrdctnImportrstList02

식약처 API 의 공통 조인 키는 ``ITEM_SEQ`` (품목기준코드).
표준 라이브러리(urllib)만 사용 — 외부 의존성 없음.

기본 사용::

    from kdrug import KdrugClient

    client = KdrugClient(api_key="...")          # 또는 KdrugClient.from_env()
    info = client.get_drug_info(item_seq="202106092")
    print(info.item_name, info.price.max_price)

저수준(원본 dict)도 가능::

    rows = client.fetch_grn_raw(item_seq="202106092")
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Optional

from .exceptions import KdrugAuthError, KdrugHTTPError, KdrugResponseError
from .models import (
    DrugCost, DrugInfo, DrugPermit, DrugProduct, MarketStatus,
    PillIdentity, ProductionRecord, SupplyReport,
)
from .parsers import (
    parse_cost, parse_grn, parse_permit, parse_product,
    parse_production, parse_supply,
)

logger = logging.getLogger("kdrug")

# ── 기본 엔드포인트 (2026-06 기준 현행 버전) ─────────────────────────
# 주의: 공공데이터포털은 서비스 버전을 올리며 구버전 경로를 폐기(404)한다.
#   - 낱알식별: Service02 → Service03 (구버전은 "API not found" 404)
#   - 제품허가: Service06/getDrugPrdtPrmsnDtlInq05 → Service07/getDrugPrdtPrmsnInq07
# 버전이 또 바뀌면 생성자 인자나 KDRUG_*_ENDPOINT 환경변수로 덮어쓸 수 있다.
DEFAULT_GRN_ENDPOINT = (
    "https://apis.data.go.kr/1471000/"
    "MdcinGrnIdntfcInfoService03/getMdcinGrnIdntfcInfoList03"
)
DEFAULT_PERMIT_ENDPOINT = (
    "https://apis.data.go.kr/1471000/"
    "DrbEasyDrugInfoService/getDrbEasyDrugList"
)
# 제품허가 상세(getDrugPrdtPrmsnDtlInq06) — 성분·저장·유효기간·효능/용법/주의·ATC 등.
# Dtl(상세) 오퍼레이션은 item_seq 로 정확히 필터된다(ITEM_SEQ 조인에 필수).
#   ⚠️ 같은 서비스의 getDrugPrdtPrmsnInq07(목록)은 item_seq 필터가 안 되므로 쓰지 말 것.
DEFAULT_PRODUCT_ENDPOINT = (
    "https://apis.data.go.kr/1471000/"
    "DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnDtlInq06"
)
# 약가기준(심평원 getDgamtList) — 상한가·급여구분·주성분코드 등.
#   ⚠️ 식약처(1471000)가 아닌 심평원(B551182) 서비스. ITEM_SEQ 없음 → 제품코드
#   (mdsCd = 제품허가 EDI_CODE 보험코드) 또는 품목명으로 조회. 인증 파라미터는
#   'ServiceKey'(대문자), 포맷 파라미터는 '_type=json'.
DEFAULT_COST_ENDPOINT = (
    "https://apis.data.go.kr/B551182/"
    "dgamtCrtrInfoService1.2/getDgamtList"
)
# 생산수입공급중단(getMdcinPrdctnIncmeSuplyList) — 중단 보고: 최종공급일·중단사유·재고.
#   ⚠️ item_seq 요청 파라미터가 없다. itemName/entpName 검색 후 ITEM_SEQ 매칭.
DEFAULT_SUPPLY_ENDPOINT = (
    "https://apis.data.go.kr/1471000/"
    "MdcinPrdctnIncmeSuplyService2/getMdcinPrdctnIncmeSuplyList"
)
# 생산·수입실적(getMdcinPrdctnImportrstList02) — 연도별 생산/수입 금액.
#   ⚠️ item_seq 파라미터가 무시된다(라이브 확인). item_name 검색 후 ITEM_SEQ 매칭.
#   ⚠️ 응답 items 가 [{"item": {...}}] 로 한 겹 중첩 — _extract_items 가 흡수.
#   금액 단위: 생산=백만원, 수입=달러(USD).
DEFAULT_PRODUCTION_ENDPOINT = (
    "https://apis.data.go.kr/1471000/"
    "MdcinPrdctnImportAcmsltService02/getMdcinPrdctnImportrstList02"
)

ENV_API_KEY = "KDRUG_API_KEY"
# rxstock/Edge Function 호환 — 인코딩/디코딩 키를 구분해 받는 환경변수도 인식.
ENV_API_KEY_ENCODING = "DRUG_API_KEY_ENCODING"
ENV_API_KEY_DECODING = "DRUG_API_KEY_DECODING"
DEFAULT_TIMEOUT = 8.0
DEFAULT_RETRIES = 2

# 공공데이터포털 "데이터 없음" 계열 코드 — 오류가 아니라 빈 결과로 처리.
NODATA_CODES = {"03", "300"}
SUCCESS_CODES = {"00", "0"}


@dataclass
class KdrugClient:
    """의약품 6종 API 래퍼 (낱알식별·e약은요·제품허가·약가·공급중단·생산수입실적).

    Args:
        api_key: 공공데이터포털 인증키 (Decoding 또는 Encoding).
        key_is_encoded: 키가 이미 URL 인코딩된 Encoding 키인지 여부.
            None(기본)이면 키에 '%' 가 있으면 Encoding 으로 자동 판별.
            Encoding 키는 그대로 삽입(이중 인코딩 방지), Decoding 키는 인코딩해 삽입.
        grn_endpoint / permit_endpoint / product_endpoint / cost_endpoint /
        supply_endpoint / production_endpoint:
            주소 오버라이드(선택).
        timeout: 요청 타임아웃(초).
        retries: 네트워크 오류 시 추가 재시도 횟수.
        user_agent: 요청 User-Agent.
    """

    api_key: str
    key_is_encoded: Optional[bool] = None
    grn_endpoint: str = DEFAULT_GRN_ENDPOINT
    permit_endpoint: str = DEFAULT_PERMIT_ENDPOINT
    product_endpoint: str = DEFAULT_PRODUCT_ENDPOINT
    cost_endpoint: str = DEFAULT_COST_ENDPOINT
    supply_endpoint: str = DEFAULT_SUPPLY_ENDPOINT
    production_endpoint: str = DEFAULT_PRODUCTION_ENDPOINT
    timeout: float = DEFAULT_TIMEOUT
    retries: int = DEFAULT_RETRIES
    user_agent: str = "kdrug-client/0.2 (+https://github.com/lunapsy/kdrug-client)"

    def __post_init__(self) -> None:
        if not (self.api_key or "").strip():
            raise KdrugAuthError(
                "API key is empty. Pass api_key=... or set the "
                f"{ENV_API_KEY} environment variable."
            )
        self.api_key = self.api_key.strip()
        # 자동 판별: 인코딩 키는 %2B/%2F/%3D 처럼 '%' 를 포함한다.
        if self.key_is_encoded is None:
            self.key_is_encoded = "%" in self.api_key

    # ── 구성 ──────────────────────────────────────────────────────────

    @classmethod
    def from_env(cls, *, use_dotenv: bool = True, **overrides: Any) -> "KdrugClient":
        """환경변수 ``KDRUG_API_KEY`` 로 클라이언트 생성.

        ``use_dotenv`` 가 True(기본)면 현재 디렉터리부터 상위로 ``.env`` 파일을
        찾아 자동으로 읽는다(이미 설정된 실제 환경변수가 항상 우선).

        엔드포인트 등은 ``KDRUG_GRN_ENDPOINT`` / ``KDRUG_PERMIT_ENDPOINT`` /
        ``KDRUG_PRICE_ENDPOINT`` 환경변수로도 덮어쓸 수 있고, kwargs 가 최우선.
        """
        if use_dotenv:
            from ._env import load_dotenv
            load_dotenv()  # best-effort — .env 없으면 조용히 통과

        # 우선순위: KDRUG_API_KEY → DRUG_API_KEY_ENCODING → DRUG_API_KEY_DECODING
        # (뒤 두 개는 rxstock/Edge Function 시크릿과 동일한 이름 — 그대로 재사용 가능)
        key = (os.environ.get(ENV_API_KEY) or "").strip()
        key_is_encoded: Optional[bool] = None
        if not key:
            enc = (os.environ.get(ENV_API_KEY_ENCODING) or "").strip()
            dec = (os.environ.get(ENV_API_KEY_DECODING) or "").strip()
            if enc:
                key, key_is_encoded = enc, True
            elif dec:
                key, key_is_encoded = dec, False
        if not key:
            raise KdrugAuthError(
                f"인증키 환경변수가 없습니다. {ENV_API_KEY} (또는 "
                f"{ENV_API_KEY_ENCODING}/{ENV_API_KEY_DECODING}) 를 설정하세요. "
                f"`kdrug --init` 로 .env 템플릿을 만들 수 있습니다."
            )
        params: dict[str, Any] = {"api_key": key}
        if key_is_encoded is not None:
            params["key_is_encoded"] = key_is_encoded
        for env_name, field_name in (
            ("KDRUG_GRN_ENDPOINT", "grn_endpoint"),
            ("KDRUG_PERMIT_ENDPOINT", "permit_endpoint"),
            ("KDRUG_PRODUCT_ENDPOINT", "product_endpoint"),
            ("KDRUG_COST_ENDPOINT", "cost_endpoint"),
            ("KDRUG_SUPPLY_ENDPOINT", "supply_endpoint"),
            ("KDRUG_PRODUCTION_ENDPOINT", "production_endpoint"),
        ):
            val = (os.environ.get(env_name) or "").strip()
            if val:
                params[field_name] = val
        params.update(overrides)
        return cls(**params)

    # ── 저수준: 원본 dict 리스트 ──────────────────────────────────────

    def fetch_grn_raw(self, *, item_seq: Optional[str] = None,
                      item_name: Optional[str] = None, rows: int = 10,
                      page: int = 1) -> list[dict[str, Any]]:
        """낱알식별 — 원본 row dict 리스트.

        getMdcinGrnIdntfcInfoList03 공식 스펙상 요청 파라미터는 소문자
        item_seq / item_name 이다(대문자로 보내면 필터가 무시됨). 응답 키는 대문자.
        """
        params = self._id_params("item_seq", "item_name", item_seq, item_name, rows, page)
        return self._fetch(self.grn_endpoint, params, "grn")

    def fetch_permit_raw(self, *, item_seq: Optional[str] = None,
                         item_name: Optional[str] = None, rows: int = 10,
                         page: int = 1) -> list[dict[str, Any]]:
        """e약은요(환자용 복약정보) — 원본 row dict 리스트.

        getDrbEasyDrugList 공식 스펙상 요청 파라미터는 camelCase itemSeq / itemName.
        """
        params = self._id_params("itemSeq", "itemName", item_seq, item_name, rows, page)
        return self._fetch(self.permit_endpoint, params, "permit")

    def fetch_product_raw(self, *, item_seq: Optional[str] = None,
                          item_name: Optional[str] = None, rows: int = 10,
                          page: int = 1) -> list[dict[str, Any]]:
        """제품허가 상세 — 원본 row dict 리스트.

        getDrugPrdtPrmsnDtlInq06 공식 스펙상 요청 파라미터는 소문자 item_seq / item_name.
        """
        params = self._id_params("item_seq", "item_name", item_seq, item_name, rows, page)
        return self._fetch(self.product_endpoint, params, "product")

    def fetch_cost_raw(self, *, mds_cd: Optional[str] = None,
                       item_name: Optional[str] = None,
                       manufacturer: Optional[str] = None,
                       rows: int = 10, page: int = 1) -> list[dict[str, Any]]:
        """약가기준(심평원 getDgamtList) — 원본 row dict 리스트.

        ITEM_SEQ 가 없는 서비스. mds_cd(제품코드=보험코드) 로 정확 조회하거나
        item_name(품목명)/manufacturer(제조업체명)로 검색. 인증 파라미터는
        'ServiceKey'(대문자), 포맷은 '_type=json'.
        """
        params: dict[str, Any] = {"numOfRows": rows, "pageNo": page, "_type": "json"}
        if mds_cd:
            params["mdsCd"] = mds_cd
        if item_name:
            params["itmNm"] = item_name
        if manufacturer:
            params["mnfEntpNm"] = manufacturer
        if not (mds_cd or item_name or manufacturer):
            raise ValueError("fetch_cost requires mds_cd, item_name, or manufacturer.")
        return self._fetch(self.cost_endpoint, params, "cost", service_key_param="ServiceKey")

    def fetch_supply_raw(self, *, item_name: Optional[str] = None,
                         entp_name: Optional[str] = None, rows: int = 10,
                         page: int = 1) -> list[dict[str, Any]]:
        """생산수입공급중단 — 원본 row dict 리스트.

        getMdcinPrdctnIncmeSuplyList 공식 스펙상 요청 파라미터는 camelCase
        itemName / entpName. **item_seq 파라미터가 없다** — 특정 품목은 품목명으로
        검색한 뒤 응답의 ITEM_SEQ 로 매칭할 것. 조건 없이 호출하면 전체 목록.
        """
        params: dict[str, Any] = {"numOfRows": rows, "pageNo": page, "type": "json"}
        if item_name:
            params["itemName"] = item_name
        if entp_name:
            params["entpName"] = entp_name
        return self._fetch(self.supply_endpoint, params, "supply")

    def fetch_production_raw(self, *, item_name: Optional[str] = None,
                             entp_name: Optional[str] = None,
                             year: Optional[str] = None,
                             part: Optional[str] = None, rows: int = 10,
                             page: int = 1) -> list[dict[str, Any]]:
        """생산·수입실적 — 원본 row dict 리스트.

        getMdcinPrdctnImportrstList02 공식 스펙상 요청 파라미터는 소문자
        item_name / entp_name / date_year / result_part. **item_seq 는 보내도
        무시된다**(라이브 확인) — 품목명 검색 후 ITEM_SEQ 매칭할 것.
        응답 items 의 [{"item": {...}}] 중첩은 _extract_items 가 풀어준다.
        """
        params: dict[str, Any] = {"numOfRows": rows, "pageNo": page, "type": "json"}
        if item_name:
            params["item_name"] = item_name
        if entp_name:
            params["entp_name"] = entp_name
        if year:
            params["date_year"] = str(year)
        if part:
            params["result_part"] = part
        return self._fetch(self.production_endpoint, params, "production")

    # ── 고수준: 정규화된 dataclass ────────────────────────────────────

    def fetch_grn(self, **kwargs: Any) -> list[PillIdentity]:
        """낱알식별 → PillIdentity 리스트."""
        return [parse_grn(r) for r in self.fetch_grn_raw(**kwargs)]

    def fetch_permit(self, **kwargs: Any) -> list[DrugPermit]:
        """e약은요(환자용 복약정보) → DrugPermit 리스트."""
        return [parse_permit(r) for r in self.fetch_permit_raw(**kwargs)]

    def fetch_product(self, **kwargs: Any) -> list[DrugProduct]:
        """제품허가 상세 → DrugProduct 리스트."""
        return [parse_product(r) for r in self.fetch_product_raw(**kwargs)]

    def fetch_cost(self, **kwargs: Any) -> list[DrugCost]:
        """약가기준(심평원) → DrugCost 리스트."""
        return [parse_cost(r) for r in self.fetch_cost_raw(**kwargs)]

    def fetch_supply(self, **kwargs: Any) -> list[SupplyReport]:
        """생산수입공급중단 → SupplyReport 리스트."""
        return [parse_supply(r) for r in self.fetch_supply_raw(**kwargs)]

    def fetch_production(self, **kwargs: Any) -> list[ProductionRecord]:
        """생산·수입실적 → ProductionRecord 리스트."""
        return [parse_production(r) for r in self.fetch_production_raw(**kwargs)]

    # ── 최상위: 4종 통합 ──────────────────────────────────────────────

    def get_drug_info(self, *, item_seq: Optional[str] = None,
                      item_name: Optional[str] = None,
                      with_cost: bool = True,
                      with_market: bool = False,
                      strict: bool = False) -> "DrugInfoResult":
        """여러 API를 한 번에 호출해 ``DrugInfo`` 로 병합.

        낱알식별·e약은요·제품허가는 item_seq 로, 약가(cost)는 제품허가의 보험코드
        (EDI_CODE = mds_cd)로 정확 조인하고, 보험코드가 없으면 품목명으로 조회한다.

        ``with_market=True`` 면 유통 상태(생산·수입실적 + 공급중단)까지 붙여서
        ``info.market`` 과 ``info.to_dict()`` 평탄화에 포함한다. 유통 상태만
        나중에 따로 갱신하려면 ``get_market_status()`` 를 쓰면 된다 (같은 결과).

        Args:
            item_seq: 품목기준코드 (권장 — 식약처 공통 조인 키).
            item_name: 제품명 (item_seq 없을 때 사용).
            with_cost: 약가(심평원) 조회 포함 여부 (기본 True).
            with_market: 유통 상태(실적+공급중단) 조회 포함 여부 (기본 False —
                API 2회가 추가되므로 옵트인).
            strict: True 면 일부 API 실패 시 예외. False(기본) 면 실패를
                ``result.errors`` 에 모아두고 받은 데이터만 병합.

        Returns:
            DrugInfoResult — ``.info`` (DrugInfo) 와 ``.errors`` (dict).
        """
        if not item_seq and not item_name:
            raise ValueError("get_drug_info requires item_seq or item_name.")

        errors: dict[str, str] = {}
        identity = self._safe_one(
            self.fetch_grn, "grn", errors, strict, item_seq=item_seq, item_name=item_name)
        permit = self._safe_one(
            self.fetch_permit, "permit", errors, strict, item_seq=item_seq, item_name=item_name)
        product = self._safe_one(
            self.fetch_product, "product", errors, strict, item_seq=item_seq, item_name=item_name)

        # 대표 식별값: 받은 것 중 먼저 채워진 값
        resolved_seq = item_seq or ""
        resolved_name = item_name or ""
        resolved_entp = ""
        for part in (identity, permit, product):
            if part is None:
                continue
            resolved_seq = resolved_seq or getattr(part, "item_seq", "")
            resolved_name = resolved_name or getattr(part, "item_name", "")
            resolved_entp = resolved_entp or getattr(part, "entp_name", "")

        # 약가(cost): 보험코드(EDI=mds_cd) 정확 조인 → 없으면 품목명 검색.
        cost = None
        if with_cost:
            edi = getattr(product, "edi_code", "") if product else ""
            if edi:
                cost = self._safe_one(self.fetch_cost, "cost", errors, strict, mds_cd=edi)
            elif resolved_name:
                cost = self._safe_one(
                    self.fetch_cost, "cost", errors, strict, item_name=resolved_name)

        # 유통 상태 (선택): 실적+공급중단 — 실패는 errors 로 흡수 (strict 존중)
        market = None
        if with_market and (resolved_seq or resolved_name):
            market_result = self.get_market_status(
                item_seq=resolved_seq or None,
                item_name=resolved_name or None,
                strict=strict)
            errors.update(market_result.errors)
            market = market_result.status

        sources = [name for name, part in
                   (("grn", identity), ("permit", permit),
                    ("product", product), ("cost", cost),
                    ("market", market if (market and (market.has_record
                     or market.suspend_reports)) else None)) if part]

        info = DrugInfo(
            item_seq=resolved_seq,
            item_name=resolved_name,
            entp_name=resolved_entp,
            sources=sources,
            identity=identity,
            permit=permit,
            product=product,
            cost=cost,
            market=market,
        )
        return DrugInfoResult(info=info, errors=errors)

    # ── 최상위: 유통 상태 (공급중단 + 생산·수입실적 결합) ─────────────

    def get_market_status(self, *, item_seq: Optional[str] = None,
                          item_name: Optional[str] = None,
                          rows: int = 50,
                          strict: bool = False) -> "MarketStatusResult":
        """공급중단·생산수입실적 2종을 결합해 유통 상태(``MarketStatus``)로 병합.

        "허가는 있는데 실제로 시장에 공급되고 있는가?"에 답한다.
        **허가만 받고 생산·수입하지 않는 품목**을 걸러낼 때 쓴다.
        ``get_drug_info(with_market=True)`` 에 포함시킬 수도 있고, 이 메서드로
        유통 상태만 따로 (재)조회할 수도 있다.

        두 API 모두 item_seq 검색이 안 되므로 품목명으로 검색한 뒤 응답의
        ITEM_SEQ 로 매칭한다. item_seq 만 주어지면 제품허가 상세에서 품목명을
        먼저 해석한다(API 1회 추가).

        ⚠️ 허가가 취하된 품목은 제품허가 API에서 조회되지 않는다. 이런 품목은
        item_name 을 함께 넘겨야 조회된다(공급중단 품목일수록 흔한 케이스).

        Args:
            item_seq: 품목기준코드. 응답 매칭 기준.
            item_name: 품목명. 검색 키 (없으면 제품허가에서 해석).
            rows: 이름 검색 범위 (동명 품목 대비, 기본 50).
            strict: True 면 일부 API 실패 시 예외. False(기본)면 errors 에 수집.

        Returns:
            MarketStatusResult — ``.status`` (MarketStatus) 와 ``.errors`` (dict).
        """
        if not item_seq and not item_name:
            raise ValueError("get_market_status requires item_seq or item_name.")

        errors: dict[str, str] = {}

        # 품목명 해석 (item_seq 만 있을 때 — 제품허가 상세는 item_seq 정확 조회 가능)
        if not item_name:
            product = self._safe_one(
                self.fetch_product, "product", errors, strict, item_seq=item_seq)
            item_name = getattr(product, "item_name", "") if product else ""
            if not item_name:
                errors.setdefault(
                    "resolve",
                    "품목명 해석 실패 — 허가취하 품목일 수 있음. item_name 을 직접 전달하세요.")
                return MarketStatusResult(
                    status=MarketStatus(item_seq=item_seq or ""), errors=errors)

        def _match(rows_: list[Any]) -> list[Any]:
            """item_seq 가 주어졌으면 정확 매칭, 아니면 품목명 그대로."""
            if not item_seq:
                return rows_
            return [r for r in rows_ if r.item_seq == item_seq]

        records: list[ProductionRecord] = []
        try:
            records = _match(self.fetch_production(item_name=item_name, rows=rows))
        except (KdrugHTTPError, KdrugResponseError) as e:
            if strict:
                raise
            errors["production"] = f"{type(e).__name__}: {e}"
            logger.warning("kdrug production failed: %s", e)

        reports: list[SupplyReport] = []
        try:
            reports = _match(self.fetch_supply(item_name=item_name, rows=rows))
        except (KdrugHTTPError, KdrugResponseError) as e:
            if strict:
                raise
            errors["supply"] = f"{type(e).__name__}: {e}"
            logger.warning("kdrug supply failed: %s", e)

        # 최근 연도 실적 집계 (같은 연도 복수 레코드는 합산)
        latest_year = ""
        latest_amount = None
        part = ""
        if records:
            latest_year = max(r.year for r in records)
            latest = [r for r in records if r.year == latest_year]
            amounts = [r.amount for r in latest if r.amount is not None]
            latest_amount = sum(amounts) if amounts else None
            part = latest[0].part

        status = MarketStatus(
            item_seq=item_seq or (records[0].item_seq if records else ""),
            item_name=item_name,
            has_record=bool(records),
            latest_year=latest_year,
            latest_amount=latest_amount,
            part=part,
            records=records,
            is_suspended=any(r.is_suspended for r in reports),
            suspend_reports=reports,
        )
        return MarketStatusResult(status=status, errors=errors)

    # ── 내부 helper ───────────────────────────────────────────────────

    @staticmethod
    def _id_params(seq_key: str, name_key: str, item_seq: Optional[str],
                   item_name: Optional[str], rows: int, page: int) -> dict[str, Any]:
        params: dict[str, Any] = {"numOfRows": rows, "pageNo": page, "type": "json"}
        if item_seq:
            params[seq_key] = item_seq
        elif item_name:
            params[name_key] = item_name
        else:
            raise ValueError("item_seq or item_name is required.")
        return params

    def _safe_one(self, fetch_fn: Any, name: str, errors: dict[str, str],
                  strict: bool, **kwargs: Any) -> Any:
        """단일 API 호출 → 첫 row dataclass. strict=False 면 예외를 errors 에 흡수."""
        try:
            results = fetch_fn(**kwargs)
        except (KdrugHTTPError, KdrugResponseError) as e:
            if strict:
                raise
            errors[name] = f"{type(e).__name__}: {e}"
            logger.warning("kdrug %s failed: %s", name, e)
            return None
        return results[0] if results else None

    def _fetch(self, endpoint: str, params: dict[str, Any], label: str,
               *, service_key_param: str = "serviceKey") -> list[dict[str, Any]]:
        # serviceKey 는 별도로 조립한다:
        #  - Encoding 키: 이미 인코딩됨 → 그대로 삽입 (이중 인코딩 방지)
        #  - Decoding 키: 원문 → 직접 인코딩해 삽입
        # 인증 파라미터명은 서비스별로 다를 수 있다(식약처 serviceKey / 심평원 ServiceKey).
        if self.key_is_encoded:
            key_param = self.api_key
        else:
            key_param = urllib.parse.quote(self.api_key, safe="")
        query = urllib.parse.urlencode(params, doseq=True, safe="")
        url = f"{endpoint}?{service_key_param}={key_param}&{query}"

        if logger.isEnabledFor(logging.INFO):
            logger.info("kdrug GET [%s] %s", label, url.replace(key_param, "***"))

        raw = self._http_get(url)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            snippet = raw[:200].decode("utf-8", "replace")
            raise KdrugResponseError(
                f"[{label}] JSON parse failed: {e}. body starts: {snippet!r}"
            ) from e

        items = _extract_items(payload, label)
        logger.info("kdrug [%s] returned %d items", label, len(items))
        return items

    def _http_get(self, url: str) -> bytes:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": self.user_agent, "Accept": "application/json"},
        )
        last_exc: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return resp.read()
            except urllib.error.HTTPError as e:
                # 4xx/5xx — 5xx 는 재시도, 4xx 는 즉시 실패
                if e.code and 400 <= e.code < 500:
                    raise KdrugHTTPError(
                        f"HTTP {e.code} {e.reason}", status_code=e.code) from e
                last_exc = e
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last_exc = e
            if attempt < self.retries:
                time.sleep(0.5 * (attempt + 1))
        raise KdrugHTTPError(
            f"HTTP request failed after {self.retries + 1} attempts: "
            f"{type(last_exc).__name__}: {last_exc}"
        )


@dataclass
class DrugInfoResult:
    """get_drug_info 반환 — 병합된 정보 + API별 오류."""

    info: DrugInfo
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        """하나 이상의 API에서 데이터를 받았으면 True."""
        return not self.info.is_empty

    def __bool__(self) -> bool:
        return self.ok


@dataclass
class MarketStatusResult:
    """get_market_status 반환 — 유통 상태 + API별 오류."""

    status: MarketStatus
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        """실적 또는 공급중단 보고 중 하나라도 확인됐으면 True."""
        return self.status.has_record or bool(self.status.suspend_reports)

    def __bool__(self) -> bool:
        return self.ok


def _extract_items(payload: dict[str, Any], label: str) -> list[dict[str, Any]]:
    """공공데이터포털 공통 응답에서 items 리스트만 추출.

    정상: {"response": {"header": {...}, "body": {"items": [...] | {"item": [...]}}}}
    resultCode 가 성공/데이터없음 외 값이면 KdrugResponseError.
    """
    header = payload.get("response", {}).get("header", {}) or payload.get("header", {})
    result_code = header.get("resultCode")
    if result_code is not None:
        code = str(result_code)
        if code in NODATA_CODES:
            return []
        if code not in SUCCESS_CODES:
            msg = header.get("resultMsg", "unknown")
            raise KdrugResponseError(
                f"[{label}] API error code={code} msg={msg}", result_code=code)

    body = payload.get("response", {}).get("body", {}) or payload.get("body", {})
    items = body.get("items")
    if items is None:
        return []
    if isinstance(items, list):
        # 생산·수입실적처럼 [{"item": {...}}, ...] 로 한 겹 싸여 오는 경우 흡수
        return [
            r["item"] if isinstance(r, dict) and set(r.keys()) == {"item"} else r
            for r in items
        ]
    if isinstance(items, dict):
        inner = items.get("item")
        if inner is None:
            return []
        return inner if isinstance(inner, list) else [inner]
    return []


__all__ = ["KdrugClient", "DrugInfoResult", "MarketStatusResult"]
