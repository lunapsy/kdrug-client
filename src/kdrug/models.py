"""파싱된 응답을 담는 프레임워크 비종속 dataclass.

공공API 원본 응답(JSON dict)을 사람이 읽기 쉬운 snake_case 필드로 정규화한다.
세 API의 공통 조인 키는 ``item_seq`` (품목기준코드).

- PillIdentity : 낱알식별 — 외형/치수/색상/식별표시
- DrugPermit   : 허가정보 — 성분/저장방법/허가일/효능·용법 문서
- DrugProduct  : 제품허가 상세 — 성분/원료/저장/허가일/ATC/효능·용법·주의 문서
- DrugCost     : 약가기준(심평원) — 상한가/급여구분/주성분코드
- DrugInfo     : 위 넷을 병합한 통합 뷰 (식약처 3종=item_seq, 약가=보험코드 조인)
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


__all__ = ["PillIdentity", "DrugPermit", "DrugProduct", "DrugCost", "DrugInfo"]
