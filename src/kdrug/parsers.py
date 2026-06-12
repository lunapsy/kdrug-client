"""공공API 원본 JSON row(dict) → 정규화된 dataclass 변환기.

공공데이터포털 의약품 API는 같은 의미의 필드를 API마다 다른 표기
(UPPER_SNAKE vs camelCase)로 내보낸다. 여기서 한 번에 흡수한다.

각 함수는 원본 row 1건을 받아 dataclass 1개를 돌려준다.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from .models import DrugCost, DrugPermit, DrugProduct, PillIdentity


# ── 값 추출 유틸 ──────────────────────────────────────────────────────


def _first(row: dict[str, Any], *keys: str) -> Any:
    """주어진 키들을 순서대로 보고 처음으로 값이 있는 것을 반환 (대소문자 표기 흡수)."""
    for k in keys:
        if k in row and row[k] not in (None, ""):
            return row[k]
    return None


def _text(row: dict[str, Any], *keys: str) -> str:
    v = _first(row, *keys)
    return str(v).strip() if v is not None else ""


def _float(row: dict[str, Any], *keys: str) -> Optional[float]:
    v = _first(row, *keys)
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _decimal(row: dict[str, Any], *keys: str) -> Optional[Decimal]:
    v = _first(row, *keys)
    if v is None:
        return None
    try:
        return Decimal(str(v).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None


# ── 파서 ─────────────────────────────────────────────────────────────


def parse_grn(row: dict[str, Any]) -> PillIdentity:
    """낱알식별 응답 1건 → PillIdentity."""
    form_code_name = _text(row, "FORM_CODE_NAME", "formCodeName")
    is_capsule: Optional[bool] = None
    if form_code_name:
        is_capsule = "캡슐" in form_code_name

    return PillIdentity(
        item_seq=_text(row, "ITEM_SEQ", "itemSeq"),
        item_name=_text(row, "ITEM_NAME", "itemName"),
        entp_name=_text(row, "ENTP_NAME", "entpName"),
        bizrno=_text(row, "BIZRNO", "bizrno"),
        length_long=_float(row, "LENG_LONG", "lengLong"),
        length_short=_float(row, "LENG_SHORT", "lengShort"),
        thickness=_float(row, "THICK", "thick"),
        drug_shape=_text(row, "DRUG_SHAPE", "drugShape"),
        form_code_name=form_code_name,
        is_capsule=is_capsule,
        color_class1=_text(row, "COLOR_CLASS1", "colorClass1"),
        color_class2=_text(row, "COLOR_CLASS2", "colorClass2"),
        print_front=_text(row, "PRINT_FRONT", "printFront"),
        print_back=_text(row, "PRINT_BACK", "printBack"),
        mark_front=_text(row, "MARK_CODE_FRONT_ANAL", "markCodeFrontAnal"),
        mark_back=_text(row, "MARK_CODE_BACK_ANAL", "markCodeBackAnal"),
        line_front=_text(row, "LINE_FRONT", "lineFront"),
        line_back=_text(row, "LINE_BACK", "lineBack"),
        class_no=_text(row, "CLASS_NO", "classNo"),
        class_name=_text(row, "CLASS_NAME", "className"),
        etc_otc=_text(row, "ETC_OTC_NAME", "ETC_OTC_CODE", "etcOtcName"),
        chart=_text(row, "CHART", "chart"),
        image_url=_text(row, "ITEM_IMAGE", "itemImage"),
    )


def parse_permit(row: dict[str, Any]) -> DrugPermit:
    """e약은요(getDrbEasyDrugList) 응답 1건 → DrugPermit.

    공식 명세(IROS_239) 출력 항목 기준. 응답은 camelCase 표기.
    """
    return DrugPermit(
        item_seq=_text(row, "itemSeq", "ITEM_SEQ"),
        item_name=_text(row, "itemName", "ITEM_NAME"),
        entp_name=_text(row, "entpName", "ENTP_NAME"),
        efficacy=_text(row, "efcyQesitm", "EFCY_QESITM"),
        use_method=_text(row, "useMethodQesitm", "USE_METHOD_QESITM"),
        warning=_text(row, "atpnWarnQesitm", "ATPN_WARN_QESITM"),
        caution=_text(row, "atpnQesitm", "ATPN_QESITM"),
        interaction=_text(row, "intrcQesitm", "INTRC_QESITM"),
        side_effect=_text(row, "seQesitm", "SE_QESITM"),
        storage=_text(row, "depositMethodQesitm", "DEPOSIT_METHOD_QESITM"),
        open_date=_text(row, "openDe", "OPEN_DE"),
        update_date=_text(row, "updateDe", "UPDATE_DE"),
        image_url=_text(row, "itemImage", "ITEM_IMAGE"),
    )


def parse_product(row: dict[str, Any]) -> DrugProduct:
    """제품허가 상세(Service07 getDrugPrdtPrmsnDtlInq06) 응답 1건 → DrugProduct.

    실제 라이브 응답(UPPER_SNAKE) 필드명 기준.
    """
    return DrugProduct(
        item_seq=_text(row, "ITEM_SEQ", "item_seq", "itemSeq"),
        item_name=_text(row, "ITEM_NAME", "item_name", "itemName"),
        item_eng_name=_text(row, "ITEM_ENG_NAME", "itemEngName"),
        entp_name=_text(row, "ENTP_NAME", "entpName"),
        entp_eng_name=_text(row, "ENTP_ENG_NAME", "entpEngName"),
        bizrno=_text(row, "BIZRNO", "bizrno"),
        main_ingredient=_text(row, "MAIN_ITEM_INGR", "mainItemIngr"),
        main_ingredient_eng=_text(row, "MAIN_INGR_ENG", "mainIngrEng"),
        material_name=_text(row, "MATERIAL_NAME", "materialName"),
        storage_method=_text(row, "STORAGE_METHOD", "storageMethod"),
        valid_term=_text(row, "VALID_TERM", "validTerm"),
        pack_unit=_text(row, "PACK_UNIT", "packUnit"),
        total_content=_text(row, "TOTAL_CONTENT", "totalContent"),
        atc_code=_text(row, "ATC_CODE", "atcCode"),
        etc_otc_code=_text(row, "ETC_OTC_CODE", "etcOtcCode"),
        permit_kind_name=_text(row, "PERMIT_KIND_NAME", "permitKindName"),
        newdrug_class_name=_text(row, "NEWDRUG_CLASS_NAME", "newdrugClassName"),
        narcotic_kind_code=_text(row, "NARCOTIC_KIND_CODE", "narcoticKindCode"),
        rare_drug_yn=_text(row, "RARE_DRUG_YN", "rareDrugYn"),
        chart=_text(row, "CHART", "chart"),
        item_permit_date=_text(row, "ITEM_PERMIT_DATE", "itemPermitDate"),
        cancel_date=_text(row, "CANCEL_DATE", "cancelDate"),
        cancel_name=_text(row, "CANCEL_NAME", "cancelName"),
        edi_code=_text(row, "EDI_CODE", "ediCode"),
        bar_code=_text(row, "BAR_CODE", "barCode"),
        ee_doc_data=_text(row, "EE_DOC_DATA", "eeDocData"),
        ud_doc_data=_text(row, "UD_DOC_DATA", "udDocData"),
        nb_doc_data=_text(row, "NB_DOC_DATA", "nbDocData"),
    )


def parse_cost(row: dict[str, Any]) -> DrugCost:
    """약가기준(심평원 getDgamtList) 응답 1건 → DrugCost.

    실제 라이브 응답(camelCase) 필드명 기준.
    """
    return DrugCost(
        mds_cd=_text(row, "mdsCd", "MDS_CD"),
        item_name=_text(row, "itmNm", "ITM_NM"),
        manufacturer=_text(row, "mnfEntpNm", "MNF_ENTP_NM"),
        max_price=_decimal(row, "mxCprc", "MX_CPRC"),
        pay_type=_text(row, "payTpNm", "PAY_TP_NM"),
        spc_gnl_type=_text(row, "spcGnlTpNm", "SPC_GNL_TP_NM"),
        injection_path=_text(row, "injcPthNm", "INJC_PTH_NM"),
        gnl_name_code=_text(row, "gnlNmCd", "GNL_NM_CD"),
        unit=_text(row, "unit", "UNIT"),
        spec_name=_text(row, "nomNm", "NOM_NM"),
        meft_div_no=_text(row, "meftDivNo", "MEFT_DIV_NO"),
        substitutable=_text(row, "sbstPsblTpNm", "SBST_PSBL_TP_NM"),
        apply_start_date=_text(row, "adtStaDd", "ADT_STA_DD"),
    )


__all__ = ["parse_grn", "parse_permit", "parse_product", "parse_cost"]
