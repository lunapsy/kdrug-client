"""파싱된 응답을 담는 프레임워크 비종속 dataclass.

공공API 원본 응답(JSON dict)을 사람이 읽기 쉬운 snake_case 필드로 정규화한다.
세 API의 공통 조인 키는 ``item_seq`` (품목기준코드).

- PillIdentity     : 낱알식별 — 외형/치수/색상/식별표시
- DrugPermit       : 허가정보 — 성분/저장방법/허가일/효능·용법 문서
- DrugProduct      : 제품허가 상세 — 성분/원료/저장/허가일/ATC/효능·용법·주의 문서
- DrugCost         : 약가기준(심평원) — 상한가/급여구분/주성분코드
- SupplyReport     : 생산수입공급중단 보고 — 최종공급일/중단사유/자사재고량
- ProductionRecord : 생산·수입실적 — 연도별 생산/수입 금액
- DrugInfo         : 위 4종(식별·e약은요·허가·약가)을 병합한 통합 뷰
- MarketStatus     : 실적+공급중단을 결합한 유통 상태 요약 (is_marketed)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from decimal import Decimal
from typing import Any, Optional


def _clean(d: dict[str, Any]) -> dict[str, Any]:
    """None / 빈 문자열 값을 제거한 dict 반환 (병합·출력용)."""
    out: dict[str, Any] = {}
    for k, v in d.items():
        if v is None or v == "":
            continue
        out[k] = v
    return out


@dataclass
class PillIdentity:
    """낱알식별 정보 (MdcinGrnIdntfcInfoService03).

    알약 자체의 물리적 외형 — 자동 분류·이미지 매칭에 쓰는 핵심 데이터.
    """

    item_seq: str = ""
    item_name: str = ""
    entp_name: str = ""              # 제조/수입사
    bizrno: str = ""                 # 사업자등록번호
    # 치수 (mm)
    length_long: Optional[float] = None   # 장축
    length_short: Optional[float] = None  # 단축
    thickness: Optional[float] = None     # 두께
    # 제형/외형
    drug_shape: str = ""             # 모양 (원형/타원형 등)
    form_code_name: str = ""         # 제형 (정제/경질캡슐 등)
    is_capsule: Optional[bool] = None
    # 색상·식별표시
    color_class1: str = ""
    color_class2: str = ""
    print_front: str = ""
    print_back: str = ""
    mark_front: str = ""
    mark_back: str = ""
    line_front: str = ""
    line_back: str = ""
    # 분류
    class_no: str = ""
    class_name: str = ""
    etc_otc: str = ""                # 전문/일반 구분
    chart: str = ""                  # 성상
    image_url: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))


@dataclass
class DrugPermit:
    """의약품개요정보 — e약은요 (DrbEasyDrugInfoService / getDrbEasyDrugList).

    환자용 '알기 쉬운 의약품 정보' — 효능/사용법/주의/상호작용/부작용/보관법을
    평이한 문장으로 제공한다. (공식 명세 IROS_239 기준)

    참고: 성분·ATC·허가일 같은 임상/행정 상세는 이 서비스가 아니라 제품허가
    상세(DrugProduct / DrugPrdtPrmsnInfoService)에서 제공된다.
    """

    item_seq: str = ""               # itemSeq 품목기준코드
    item_name: str = ""              # itemName 제품명
    entp_name: str = ""              # entpName 업체명
    efficacy: str = ""               # efcyQesitm 문항1(효능)
    use_method: str = ""             # useMethodQesitm 문항2(사용법)
    warning: str = ""                # atpnWarnQesitm 문항3(주의사항 경고)
    caution: str = ""                # atpnQesitm 문항4(주의사항)
    interaction: str = ""            # intrcQesitm 문항5(상호작용)
    side_effect: str = ""            # seQesitm 문항6(부작용)
    storage: str = ""                # depositMethodQesitm 문항7(보관법)
    open_date: str = ""              # openDe 공개일자
    update_date: str = ""            # updateDe 수정일자
    image_url: str = ""              # itemImage 낱알이미지 URL

    def to_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))


@dataclass
class DrugProduct:
    """제품허가 상세정보 (DrugPrdtPrmsnInfoService07 / getDrugPrdtPrmsnDtlInq06).

    의약품 제품의 허가 상세 — 주성분, 원료, 저장방법, 유효기간, 허가일, ATC,
    전문/일반, 효능효과·용법용량·주의사항 문서(HTML), 보험코드(EDI) 등.
    item_seq 로 정확히 조회된다.

    참고: 약가(상한금액)는 이 서비스가 아니라 심평원 약가 서비스(DrugCost)에서 온다.
    ``edi_code``(보험코드)는 약가의 ``mds_cd``(제품코드)와 동일해 정확 조인 키로 쓰인다.
    """

    item_seq: str = ""
    item_name: str = ""
    item_eng_name: str = ""
    entp_name: str = ""
    entp_eng_name: str = ""
    bizrno: str = ""                       # 사업자등록번호
    main_ingredient: str = ""              # 주성분 (MAIN_ITEM_INGR)
    main_ingredient_eng: str = ""          # 주성분 영문 (MAIN_INGR_ENG)
    material_name: str = ""                # 원료/총량·분량·규격 (MATERIAL_NAME)
    storage_method: str = ""               # 저장방법
    valid_term: str = ""                   # 유효기간
    pack_unit: str = ""                    # 포장단위
    total_content: str = ""                # 총량
    atc_code: str = ""
    etc_otc_code: str = ""                 # 전문/일반 구분
    permit_kind_name: str = ""             # 허가/신고 구분
    newdrug_class_name: str = ""
    narcotic_kind_code: str = ""
    rare_drug_yn: str = ""
    chart: str = ""                        # 성상
    item_permit_date: str = ""             # 허가일자
    cancel_date: str = ""
    cancel_name: str = ""                  # 정상/취소/취하
    edi_code: str = ""                     # 보험코드(EDI) = 약가 mds_cd
    bar_code: str = ""
    # 첨부문서 (긴 HTML)
    ee_doc_data: str = ""                  # 효능효과
    ud_doc_data: str = ""                  # 용법용량
    nb_doc_data: str = ""                  # 사용상의 주의사항

    def to_dict(self) -> dict[str, Any]:
        return _clean(asdict(self))


@dataclass
class DrugCost:
    """약가기준정보 — 심평원 (dgamtCrtrInfoService / getDgamtList).

    건강보험 상한금액·급여구분·주성분코드 등. **품목기준코드(item_seq)가 없고**
    제품코드(``mds_cd``)·품목명(``item_name``) 기준이다. ``mds_cd`` 는 제품허가의
    보험코드(EDI_CODE)와 같아 정확 조인 키가 된다. 비급여/삭제 품목은 상한가가 없다.
    """

    mds_cd: str = ""                       # 제품코드 (= 보험코드 EDI_CODE)
    item_name: str = ""                    # itmNm 품목명
    manufacturer: str = ""                 # mnfEntpNm 제조업체명
    max_price: Optional[Decimal] = None    # mxCprc 상한가(원)
    pay_type: str = ""                     # payTpNm 급여구분
    spc_gnl_type: str = ""                 # spcGnlTpNm 전문/일반
    injection_path: str = ""               # injcPthNm 투여경로
    gnl_name_code: str = ""                # gnlNmCd 주성분코드
    unit: str = ""                         # unit 규격단위
    spec_name: str = ""                    # nomNm 규격명
    meft_div_no: str = ""                  # meftDivNo 효능군분류번호
    substitutable: str = ""                # sbstPsblTpNm 대체가능여부
    apply_start_date: str = ""             # adtStaDd 적용시작일자

    def to_dict(self) -> dict[str, Any]:
        out = _clean(asdict(self))
        if isinstance(out.get("max_price"), Decimal):
            out["max_price"] = str(out["max_price"])
        return out



@dataclass
class SupplyReport:
    """생산수입공급중단 보고 (MdcinPrdctnIncmeSuplyService2).

    업체가 식약처에 제출한 생산/수입/공급 중단 보고 1건. 최종공급일자·중단사유·
    자사재고량·공급부족가능성 등 수급 리스크 판단 정보를 담는다. 일 1회 갱신.

    ⚠️ 이 API는 item_seq 요청 파라미터가 없다 — 업체명(entpName)/품목명(itemName)
    으로만 검색되며, 특정 품목 매칭은 응답의 ITEM_SEQ 로 클라이언트에서 한다.
    """

    item_seq: str = ""                   # ITEM_SEQ 품목기준코드 (조인키)
    item_name: str = ""                  # ITEM_NAME 품목명
    edi_code: str = ""                   # EDI_CODE 표준코드
    entp_name: str = ""                  # ENTP_NAME 업체명
    entp_seq: str = ""                   # ENTP_SEQ 업 일련번호
    bizrno: str = ""                     # BIZRNO 사업자등록번호
    report_flag: str = ""                # SUSPEND_REPORT_FLAG 보고구분 (생산/수입/공급)
    report_seq: str = ""                 # SUSPEND_REPORT_SEQ 보고번호
    report_progress: str = ""            # REPORT_PGS_CODE 진행단계 (신청중/처리완료/취하 등)
    supply_yn: str = ""                  # SUPPLY_YN 보고구분_공급 (Y/N)
    last_supply_date: str = ""           # LAST_SUPPLY_DATE 최종공급일자 (YYYYMMDD)
    suspend_date: str = ""               # SUSPEND_DATE 공급중단일자 (YYYYMMDD)
    suspend_flag: str = ""               # SUSPEND_FLAG 중단구분 (1:공급 / 2:공급중단)
    inventory_date: str = ""             # INV_DATE 재고기준일자
    inventory_qty: str = ""              # INV_QTY 자사재고량
    suspend_reason: str = ""             # SUSPEND_REASON 중단사유
    shortage_risk: str = ""              # SUPPLY_LACK_PACI 공급부족가능성
    supply_plan: str = ""                # SUPPLY_PLAN 공급원활 추진계획
    report_date: str = ""                # REPORT_DATE 보고일자
    processed_date: str = ""             # EXAM_RESULT_TIME 처리일자
    address: str = ""                    # REPORT_ADDR 업체소재지

    @property
    def is_suspended(self) -> bool:
        """공급중단 보고 여부 (SUSPEND_FLAG == "2")."""
        return self.suspend_flag.strip() == "2"

    def to_dict(self) -> dict[str, Any]:
        out = _clean(asdict(self))
        out["is_suspended"] = self.is_suspended
        return out


@dataclass
class ProductionRecord:
    """생산·수입실적 (MdcinPrdctnImportAcmsltService02).

    품목별 연간 생산 또는 수입 실적 1건. **허가만 받아놓고 실제로 생산/수입하지
    않는 품목**을 걸러낼 때 쓴다 — 실적 레코드가 없으면 그 해 시장 공급이 없었다는
    신호다. 연 1회 갱신.

    ⚠️ 금액 단위가 구분별로 다르다: 생산 = 백만원, 수입 = 달러(USD).
    ⚠️ 같은 품목이 한 연도에 복수 레코드(포장단위별 등)로 나올 수 있다.
    ⚠️ 이 API도 item_seq 요청 파라미터가 무시된다(라이브 확인) — 품목명으로 검색
    후 응답의 ITEM_SEQ 로 매칭해야 한다.
    """

    item_seq: str = ""                   # ITEM_SEQ 품목기준코드 (조인키)
    item_name: str = ""                  # ITEM_NAME 품목명
    entp_name: str = ""                  # ENTP_NAME 업체명
    entp_seq: str = ""                   # ENTP_SEQ 업 일련번호
    bizrno: str = ""                     # BIZRNO 사업자등록번호
    year: str = ""                       # DATE_YEAR 집계년도
    part: str = ""                       # RESULT_PART 생산·수입 구분 ("생산"/"수입")
    amount: Optional[Decimal] = None     # AMT 실적금액 (생산:백만원 / 수입:달러)

    @property
    def is_production(self) -> bool:
        """국내 생산 실적 여부 (금액 단위: 백만원)."""
        return self.part.strip() == "생산"

    @property
    def is_import(self) -> bool:
        """수입 실적 여부 (금액 단위: 달러)."""
        return self.part.strip() == "수입"

    @property
    def amount_krw(self) -> Optional[Decimal]:
        """생산 실적 금액의 원 단위 환산. 수입 실적(달러)은 환율이 필요하므로 None."""
        if self.amount is None or not self.is_production:
            return None
        return self.amount * 1_000_000

    def to_dict(self) -> dict[str, Any]:
        out = _clean(asdict(self))
        if isinstance(out.get("amount"), Decimal):
            out["amount"] = str(out["amount"])
        return out


@dataclass
class MarketStatus:
    """유통 상태 요약 — 생산·수입실적 + 공급중단 보고 결합.

    "허가는 살아있는데 실제로 시장에 공급되고 있는가?"에 답한다.
    주문/발주 시스템 연동 시 죽은 품목(허가만 있고 미생산/미수입)을 걸러내는
    용도로 설계됐다. ``KdrugClient.get_market_status()`` 가 만든다.
    """

    item_seq: str = ""
    item_name: str = ""
    # 실적 (생산·수입실적 API)
    has_record: bool = False             # 생산/수입 실적 존재 여부
    latest_year: str = ""                # 가장 최근 실적 연도
    latest_amount: Optional[Decimal] = None  # 최근 연도 실적 합계 (단위는 part 참조)
    part: str = ""                       # 최근 실적 구분 ("생산"/"수입")
    records: list = field(default_factory=list)          # ProductionRecord 리스트
    # 공급중단 (공급중단 API)
    is_suspended: bool = False           # 공급중단 보고 존재 여부
    suspend_reports: list = field(default_factory=list)  # SupplyReport 리스트

    @property
    def is_marketed(self) -> bool:
        """실제 유통 중으로 추정 (실적 있음 + 공급중단 보고 없음)."""
        return self.has_record and not self.is_suspended

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "item_seq": self.item_seq,
            "item_name": self.item_name,
            "has_record": self.has_record,
            "latest_year": self.latest_year,
            "latest_amount": str(self.latest_amount) if self.latest_amount is not None else None,
            "part": self.part,
            "is_suspended": self.is_suspended,
            "is_marketed": self.is_marketed,
            "records": [r.to_dict() for r in self.records],
            "suspend_reports": [r.to_dict() for r in self.suspend_reports],
        }
        return out


@dataclass
class DrugInfo:
    """4종 API 결과를 병합한 통합 의약품 정보.

    ``sources`` 에는 실제로 데이터가 들어온 API 이름이 담긴다
    (예: ["grn", "permit", "product", "cost"]). 각 원본 dataclass 는
    ``identity / permit / product / cost`` 로 그대로 접근 가능.

    조인: grn/permit/product 는 item_seq 기준, cost(약가)는 제품허가 보험코드
    (EDI_CODE = mds_cd) 또는 품목명 기준으로 붙는다.
    """

    item_seq: str = ""
    item_name: str = ""
    entp_name: str = ""
    sources: list[str] = field(default_factory=list)

    identity: Optional[PillIdentity] = None
    permit: Optional[DrugPermit] = None
    product: Optional[DrugProduct] = None
    cost: Optional[DrugCost] = None

    def to_dict(self) -> dict[str, Any]:
        """평탄화된 단일 dict — 식별→복약→허가→약가 순으로 채우되 빈 값은 덮지 않는다."""
        merged: dict[str, Any] = {}
        for part in (self.identity, self.permit, self.product, self.cost):
            if part is None:
                continue
            for k, v in part.to_dict().items():
                if k not in merged or merged[k] in (None, ""):
                    merged[k] = v
        merged["item_seq"] = self.item_seq or merged.get("item_seq", "")
        merged["item_name"] = self.item_name or merged.get("item_name", "")
        merged["entp_name"] = self.entp_name or merged.get("entp_name", "")
        merged["sources"] = list(self.sources)
        return merged

    @property
    def is_empty(self) -> bool:
        return not self.sources


__all__ = [
    "PillIdentity", "DrugPermit", "DrugProduct", "DrugCost",
    "SupplyReport", "ProductionRecord", "MarketStatus", "DrugInfo",
]
