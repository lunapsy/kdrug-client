# Field Reference / 필드 레퍼런스

[English](#field-reference--필드-레퍼런스) · [한국어](#한국어)

Complete column list for every dataclass. The common join key for the three
MFDS services is `ITEM_SEQ` (item serial code); the HIRA price service has no
`ITEM_SEQ` and joins via `mds_cd` (= product permit `EDI_CODE`, the insurance code).

모든 dataclass의 전체 컬럼입니다. 식약처 3종의 공통 조인 키는 `ITEM_SEQ`(품목기준코드),
심평원 약가는 `ITEM_SEQ`가 없어 `mds_cd`(= 제품허가 `EDI_CODE` 보험코드)로 조인합니다.

---

## 🟦 PillIdentity — 낱알식별 / Pill identification
`MdcinGrnIdntfcInfoService03 / getMdcinGrnIdntfcInfoList03` — 23 fields

| field | API key | 설명 (KR) | description (EN) |
|-------|---------|-----------|------------------|
| `item_seq` | `ITEM_SEQ` | 품목기준코드 (조인 키) | item serial code (join key) |
| `item_name` | `ITEM_NAME` | 제품명 | product name |
| `entp_name` | `ENTP_NAME` | 업체명 | company name |
| `bizrno` | `BIZRNO` | 사업자등록번호 | business registration no. |
| `length_long` | `LENG_LONG` | 장축 길이(mm) | long axis length (mm) |
| `length_short` | `LENG_SHORT` | 단축 길이(mm) | short axis length (mm) |
| `thickness` | `THICK` | 두께(mm) | thickness (mm) |
| `drug_shape` | `DRUG_SHAPE` | 모양 (원형/타원형 등) | shape (round/oval/…) |
| `form_code_name` | `FORM_CODE_NAME` | 제형 (정제/캡슐 등) | dosage form |
| `is_capsule` | (derived) | 캡슐 여부 (제형에서 추론) | capsule? (derived from form) |
| `color_class1` | `COLOR_CLASS1` | 색상 1 | color 1 |
| `color_class2` | `COLOR_CLASS2` | 색상 2 | color 2 |
| `print_front` | `PRINT_FRONT` | 앞면 표시(각인) | front imprint |
| `print_back` | `PRINT_BACK` | 뒷면 표시(각인) | back imprint |
| `mark_front` | `MARK_CODE_FRONT_ANAL` | 앞면 마크 | front mark code |
| `mark_back` | `MARK_CODE_BACK_ANAL` | 뒷면 마크 | back mark code |
| `line_front` | `LINE_FRONT` | 앞면 분할선 | front score line |
| `line_back` | `LINE_BACK` | 뒷면 분할선 | back score line |
| `class_no` | `CLASS_NO` | 분류번호 | class number |
| `class_name` | `CLASS_NAME` | 분류명 | class name |
| `etc_otc` | `ETC_OTC_NAME` | 전문/일반 구분 | Rx / OTC |
| `chart` | `CHART` | 성상 | appearance text |
| `image_url` | `ITEM_IMAGE` | 낱알 이미지 URL | pill image URL |

---

## 🟩 DrugPermit — e약은요 / Patient drug info
`DrbEasyDrugInfoService / getDrbEasyDrugList` (official spec IROS_239) — 13 fields

Patient-friendly "easy drug info" (Q&A). Camel-case response keys.
환자용 '알기 쉬운 의약품 정보'(Q&A). 응답 키는 camelCase.

| field | API key | 설명 (KR) | description (EN) |
|-------|---------|-----------|------------------|
| `item_seq` | `itemSeq` | 품목기준코드 | item serial code |
| `item_name` | `itemName` | 제품명 | product name |
| `entp_name` | `entpName` | 업체명 | company name |
| `efficacy` | `efcyQesitm` | 문항1 — 효능 | Q1 — efficacy / indications |
| `use_method` | `useMethodQesitm` | 문항2 — 사용법 | Q2 — how to use |
| `warning` | `atpnWarnQesitm` | 문항3 — 주의사항(경고) | Q3 — warnings |
| `caution` | `atpnQesitm` | 문항4 — 주의사항 | Q4 — precautions |
| `interaction` | `intrcQesitm` | 문항5 — 상호작용 | Q5 — interactions |
| `side_effect` | `seQesitm` | 문항6 — 부작용 | Q6 — side effects |
| `storage` | `depositMethodQesitm` | 문항7 — 보관법 | Q7 — storage |
| `open_date` | `openDe` | 공개일자 | disclosure date |
| `update_date` | `updateDe` | 수정일자 | update date |
| `image_url` | `itemImage` | 낱알이미지 URL | pill image URL |

---

## 🟧 DrugProduct — 제품허가 상세 / Product permit detail
`DrugPrdtPrmsnInfoService07 / getDrugPrdtPrmsnDtlInq06` — 28 fields

`item_seq` 로 정확 조회되는 상세 오퍼레이션. `edi_code`(보험코드)는 약가 `mds_cd` 와 동일.
Detail op queried exactly by `item_seq`. `edi_code` equals the price service `mds_cd`.

| field | API key | 설명 (KR) | description (EN) |
|-------|---------|-----------|------------------|
| `item_seq` | `ITEM_SEQ` | 품목기준코드 | item serial code |
| `item_name` | `ITEM_NAME` | 제품명 | product name |
| `item_eng_name` | `ITEM_ENG_NAME` | 영문 제품명 | English product name |
| `entp_name` | `ENTP_NAME` | 업체명 | company name |
| `entp_eng_name` | `ENTP_ENG_NAME` | 영문 업체명 | English company name |
| `bizrno` | `BIZRNO` | 사업자등록번호 | business registration no. |
| `main_ingredient` | `MAIN_ITEM_INGR` | 주성분 | main ingredient |
| `main_ingredient_eng` | `MAIN_INGR_ENG` | 주성분(영문) | main ingredient (EN) |
| `material_name` | `MATERIAL_NAME` | 원료/총량·분량·규격 | raw material / content spec |
| `storage_method` | `STORAGE_METHOD` | 저장방법 | storage method |
| `valid_term` | `VALID_TERM` | 유효기간 | validity term |
| `pack_unit` | `PACK_UNIT` | 포장단위 | packaging unit |
| `total_content` | `TOTAL_CONTENT` | 총량 | total content |
| `atc_code` | `ATC_CODE` | ATC 코드 | ATC code |
| `etc_otc_code` | `ETC_OTC_CODE` | 전문/일반 구분 | Rx / OTC |
| `permit_kind_name` | `PERMIT_KIND_NAME` | 허가/신고 구분 | permit/notification type |
| `newdrug_class_name` | `NEWDRUG_CLASS_NAME` | 신약 구분 | new-drug class |
| `narcotic_kind_code` | `NARCOTIC_KIND_CODE` | 마약류 구분 | narcotic class code |
| `rare_drug_yn` | `RARE_DRUG_YN` | 희귀의약품 여부 | orphan drug? |
| `chart` | `CHART` | 성상 | appearance text |
| `item_permit_date` | `ITEM_PERMIT_DATE` | 허가일자 | permit date |
| `cancel_date` | `CANCEL_DATE` | 취소일자 | cancellation date |
| `cancel_name` | `CANCEL_NAME` | 상태 (정상/취소/취하) | status (active/cancelled/…) |
| `edi_code` | `EDI_CODE` | 보험코드 (= 약가 mds_cd) | insurance code (= price mds_cd) |
| `bar_code` | `BAR_CODE` | 바코드 | barcode |
| `ee_doc_data` | `EE_DOC_DATA` | 효능효과 (HTML) | efficacy document (HTML) |
| `ud_doc_data` | `UD_DOC_DATA` | 용법용량 (HTML) | dosage document (HTML) |
| `nb_doc_data` | `NB_DOC_DATA` | 사용상 주의사항 (HTML) | precautions document (HTML) |

---

## 🟨 DrugCost — 약가기준 / Drug price (HIRA)
`dgamtCrtrInfoService1.2 / getDgamtList` (org B551182) — 13 fields

심평원 서비스. 인증 파라미터 `ServiceKey`(대문자), 포맷 `_type=json`. `ITEM_SEQ` 없음 →
`mds_cd`(=보험코드) 또는 품목명으로 조회. 비급여/삭제 품목은 상한가 없음.
HIRA service. Auth param `ServiceKey` (capital), format `_type=json`. No `ITEM_SEQ` →
query by `mds_cd` (insurance code) or product name. Non-reimbursed items have no price.

| field | API key | 설명 (KR) | description (EN) |
|-------|---------|-----------|------------------|
| `mds_cd` | `mdsCd` | 제품코드 (= 보험코드, 조인 키) | product code (= insurance code, join key) |
| `item_name` | `itmNm` | 품목명 | product name |
| `manufacturer` | `mnfEntpNm` | 제조업체명 | manufacturer |
| `max_price` | `mxCprc` | **상한가(원)** (`Decimal`) | **ceiling price (KRW)** (`Decimal`) |
| `pay_type` | `payTpNm` | 급여구분 | reimbursement type |
| `spc_gnl_type` | `spcGnlTpNm` | 전문/일반 | Rx / OTC |
| `injection_path` | `injcPthNm` | 투여경로 | route of administration |
| `gnl_name_code` | `gnlNmCd` | 주성분코드 | generic ingredient code |
| `unit` | `unit` | 규격단위 | unit |
| `spec_name` | `nomNm` | 규격명 | specification name |
| `meft_div_no` | `meftDivNo` | 효능군분류번호 | efficacy group no. |
| `substitutable` | `sbstPsblTpNm` | 대체가능여부 | substitutable? |
| `apply_start_date` | `adtStaDd` | 적용시작일자 | price effective date |

---

## Merge order / 병합 규칙 — `DrugInfo.to_dict()`

Filled in order **identity → permit → product → cost**; existing non-empty values
are not overwritten. So when the same field appears in multiple sources, the
earliest one wins.

식별 → 복약(e약은요) → 제품허가 → 약가 순으로 채우되, **이미 값이 있는 키는 덮어쓰지
않습니다.** 같은 의미 필드가 여러 API에 있으면 먼저 들어온 값이 유지됩니다.

> Endpoint version numbers (`…Service03`, `…DtlInq06`, `…Service1.2`) may change.
> Override via constructor args or `KDRUG_*_ENDPOINT` env vars.
>
> 엔드포인트 버전(`…Service03` 등)은 바뀔 수 있습니다. 생성자 인자나
> `KDRUG_*_ENDPOINT` 환경변수로 덮어쓰세요.

---

## 한국어

위 표가 한국어 설명을 포함합니다(`설명 (KR)` 열). 한국어로만 보고 싶으면 각 표의
`field` · `API key` · `설명 (KR)` 열을 참고하세요. 전체 77개 컬럼:
PillIdentity 23 · DrugPermit 13 · DrugProduct 28 · DrugCost 13.
