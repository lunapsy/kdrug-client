# 필드 매핑 레퍼런스

각 API 원본 응답 키가 어떤 dataclass 필드로 정규화되는지 정리한 표입니다.
세 API 공통 조인 키는 `ITEM_SEQ`(품목기준코드)입니다.

## 🟦 PillIdentity — 낱알식별 (`MdcinGrnIdntfcInfoService03`)

| dataclass 필드 | 원본 키 | 의미 |
|----------------|---------|------|
| `item_seq` | `ITEM_SEQ` | 품목기준코드 (조인 키) |
| `item_name` | `ITEM_NAME` | 제품명 |
| `entp_name` | `ENTP_NAME` | 업체명 |
| `bizrno` | `BIZRNO` | 사업자등록번호 |
| `length_long` | `LENG_LONG` | 장축 길이(mm) |
| `length_short` | `LENG_SHORT` | 단축 길이(mm) |
| `thickness` | `THICK` | 두께(mm) |
| `drug_shape` | `DRUG_SHAPE` | 모양 (원형/타원형 등) |
| `form_code_name` | `FORM_CODE_NAME` | 제형 (정제/경질캡슐 등) |
| `is_capsule` | (파생) | `FORM_CODE_NAME` 에 '캡슐' 포함 여부 |
| `color_class1` / `color_class2` | `COLOR_CLASS1` / `COLOR_CLASS2` | 색상 |
| `print_front` / `print_back` | `PRINT_FRONT` / `PRINT_BACK` | 표시(각인) 앞/뒤 |
| `mark_front` / `mark_back` | `MARK_CODE_FRONT_ANAL` / `MARK_CODE_BACK_ANAL` | 마크 코드 |
| `line_front` / `line_back` | `LINE_FRONT` / `LINE_BACK` | 분할선 앞/뒤 |
| `class_no` / `class_name` | `CLASS_NO` / `CLASS_NAME` | 분류번호/분류명 |
| `etc_otc` | `ETC_OTC_NAME` | 전문/일반 구분 |
| `chart` | `CHART` | 성상 |
| `image_url` | `ITEM_IMAGE` | 낱알 이미지 URL |

## 🟩 DrugPermit — e약은요 (`DrbEasyDrugInfoService/getDrbEasyDrugList`)

공식 명세(IROS_239) 기준. 환자용 '알기 쉬운 의약품 정보'(Q&A 형식)를 제공한다.
응답 키는 camelCase. (성분·ATC·허가일 등 임상/행정 상세는 이 서비스가 아니라
제품허가 상세 = DrugPrice 에서 제공된다.)

| dataclass 필드 | 원본 키 | 의미 |
|----------------|---------|------|
| `item_seq` | `itemSeq` | 품목기준코드 |
| `item_name` | `itemName` | 제품명 |
| `entp_name` | `entpName` | 업체명 |
| `efficacy` | `efcyQesitm` | 문항1 — 효능 |
| `use_method` | `useMethodQesitm` | 문항2 — 사용법 |
| `warning` | `atpnWarnQesitm` | 문항3 — 주의사항(경고) |
| `caution` | `atpnQesitm` | 문항4 — 주의사항 |
| `interaction` | `intrcQesitm` | 문항5 — 상호작용 |
| `side_effect` | `seQesitm` | 문항6 — 부작용 |
| `storage` | `depositMethodQesitm` | 문항7 — 보관법 |
| `open_date` / `update_date` | `openDe` / `updateDe` | 공개/수정 일자 |
| `image_url` | `itemImage` | 낱알이미지 URL |

## 🟧 DrugProduct — 제품허가 상세 (`DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnDtlInq06`)

`item_seq` 로 정확히 조회되는 상세 오퍼레이션. (목록 오퍼레이션 `getDrugPrdtPrmsnInq07`
은 item_seq 필터가 동작하지 않으므로 사용하지 않음.) `edi_code`(보험코드)는 약가의
`mds_cd` 와 같아 약가 조인 키로 쓰인다.

| dataclass 필드 | 원본 키 | 의미 |
|----------------|---------|------|
| `item_seq` | `ITEM_SEQ` | 품목기준코드 |
| `item_name` / `item_eng_name` | `ITEM_NAME` / `ITEM_ENG_NAME` | 제품명(국/영문) |
| `entp_name` / `entp_eng_name` | `ENTP_NAME` / `ENTP_ENG_NAME` | 업체명(국/영문) |
| `bizrno` | `BIZRNO` | 사업자등록번호 |
| `main_ingredient` | `MAIN_ITEM_INGR` | 주성분 |
| `main_ingredient_eng` | `MAIN_INGR_ENG` | 주성분(영문) |
| `material_name` | `MATERIAL_NAME` | 원료/총량·분량·규격 |
| `storage_method` | `STORAGE_METHOD` | 저장방법 |
| `valid_term` | `VALID_TERM` | 유효기간 |
| `pack_unit` | `PACK_UNIT` | 포장단위 |
| `total_content` | `TOTAL_CONTENT` | 총량 |
| `atc_code` | `ATC_CODE` | ATC 코드 |
| `etc_otc_code` | `ETC_OTC_CODE` | 전문/일반 구분 |
| `permit_kind_name` | `PERMIT_KIND_NAME` | 허가/신고 구분 |
| `newdrug_class_name` | `NEWDRUG_CLASS_NAME` | 신약 구분 |
| `narcotic_kind_code` | `NARCOTIC_KIND_CODE` | 마약류 구분 |
| `rare_drug_yn` | `RARE_DRUG_YN` | 희귀의약품 여부 |
| `chart` | `CHART` | 성상 |
| `item_permit_date` | `ITEM_PERMIT_DATE` | 허가일자 |
| `cancel_date` / `cancel_name` | `CANCEL_DATE` / `CANCEL_NAME` | 취소일/상태 |
| `edi_code` / `bar_code` | `EDI_CODE` / `BAR_CODE` | 보험코드/바코드 |
| `ee_doc_data` | `EE_DOC_DATA` | 효능효과 (HTML) |
| `ud_doc_data` | `UD_DOC_DATA` | 용법용량 (HTML) |
| `nb_doc_data` | `NB_DOC_DATA` | 사용상 주의사항 (HTML) |

## 🟨 DrugCost — 약가기준 (`dgamtCrtrInfoService1.2/getDgamtList`, 심평원)

식약처(1471000)가 아닌 **건강보험심사평가원(B551182)** 서비스. 인증 파라미터는
`ServiceKey`(대문자), 포맷은 `_type=json`. **ITEM_SEQ 가 없어** 제품코드(`mds_cd` =
제품허가 `EDI_CODE` 보험코드) 또는 품목명으로 조회한다. 응답 키는 camelCase.
비급여/삭제 품목은 상한가(`max_price`)가 없다.

| dataclass 필드 | 원본 키 | 의미 |
|----------------|---------|------|
| `mds_cd` | `mdsCd` | 제품코드 (= 보험코드 EDI_CODE, 정확 조인 키) |
| `item_name` | `itmNm` | 품목명 |
| `manufacturer` | `mnfEntpNm` | 제조업체명 |
| `max_price` | `mxCprc` | **상한가(원)** — `Decimal` |
| `pay_type` | `payTpNm` | 급여구분 |
| `spc_gnl_type` | `spcGnlTpNm` | 전문/일반 |
| `injection_path` | `injcPthNm` | 투여경로 |
| `gnl_name_code` | `gnlNmCd` | 주성분코드 |
| `unit` | `unit` | 규격단위 |
| `spec_name` | `nomNm` | 규격명 |
| `meft_div_no` | `meftDivNo` | 효능군분류번호 |
| `substitutable` | `sbstPsblTpNm` | 대체가능여부 |
| `apply_start_date` | `adtStaDd` | 적용시작일자 |

## 병합 규칙 (`DrugInfo.to_dict()`)

식별 → 복약(e약은요) → 제품허가 → 약가 순으로 채우되, **이미 값이 있는 키는
덮어쓰지 않습니다.** 따라서 같은 의미 필드가 여러 API에 있으면 먼저 들어온 값이
유지됩니다.

**조인**: 식약처 3종은 `item_seq` 로, 약가는 제품허가의 보험코드(`edi_code` =
`mds_cd`)로 정확 조인됩니다(보험코드 없으면 품목명 검색).

> 엔드포인트 경로의 버전 숫자(`...Service03`, `...DtlInq06`, `...Service1.2`)는
> 제공기관이 갱신할 수 있습니다. 변경 시 `KdrugClient(grn_endpoint=...)` 등으로
> 오버라이드하거나 `KDRUG_GRN_ENDPOINT`/`KDRUG_COST_ENDPOINT` 환경변수를 쓰세요.
