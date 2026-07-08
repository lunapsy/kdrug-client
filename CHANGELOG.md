# Changelog

이 프로젝트는 [Semantic Versioning](https://semver.org/lang/ko/)을 따릅니다.

## [0.3.2] - 2026-07-08

### Docs
- 대표 예시(한/영)에 `with_market=True` + `info.market.is_marketed` 라인 추가 —
  6종 전체 흐름을 첫 예시에서 보여준다. 코드 변경 없음.

## [0.3.1] - 2026-07-08

### Docs
- README 한/영 전면 정합성 검토 — "4개 중 일부만 호출" → 6개로 갱신하고
  `fetch_supply`/`fetch_production` 예시 추가, "약가 조회 끄기" →
  "통합 조회에서 소스 켜고 끄기"(`with_cost`/`with_market`)로 재작성,
  FAQ의 "four APIs" → six 갱신.
- CLI/모델 docstring 의 3종·4종 표기 정리, User-Agent 0.3 으로 갱신.
  코드 동작 변경 없음.

## [0.3.0] - 2026-07-08

### Added — 공급중단·생산수입실적 2종 소스 + 유통 상태 판별

식약처 생산수입공급중단정보(`MdcinPrdctnIncmeSuplyService2`)와
생산·수입실적현황(`MdcinPrdctnImportAcmsltService02`)을 5·6번째 소스로 추가.
**허가만 받아놓고 실제 생산·수입하지 않는 품목**을 걸러낼 수 있게 됐다.

- `SupplyReport`(21 필드) / `ProductionRecord`(8 필드) dataclass +
  `parse_supply` / `parse_production` + `fetch_supply(item_name=/entp_name=)` /
  `fetch_production(item_name=/entp_name=/year=/part=)`.
- **`get_market_status(item_seq=/item_name=)`** — 두 API를 결합해
  `MarketStatus.is_marketed` (실적 있음 + 중단 보고 없음) 하나로 답한다.
  `MarketStatusResult` 는 `DrugInfoResult` 와 같은 `.errors` 부분 실패 패턴.
- **`get_drug_info(with_market=True)`** — 유통 상태를 통합 조회에 포함.
  `info.market` 으로 원본 접근, `info.to_dict()` 평탄화에 `is_marketed` /
  `has_record` / `latest_year` / `latest_amount` / `market_part` /
  `is_suspended` 가 함께 들어간다. 유통 상태만 따로 갱신하려면
  `get_market_status()` 를 그대로 쓰면 된다 (실적은 연 1회, 중단 보고는
  일 1회 갱신이라 분리 갱신이 유용).
- 두 API 모두 **item_seq 검색 미지원**(파라미터가 조용히 무시됨 — 라이브 확인)
  → 품목명 검색 후 응답 `ITEM_SEQ` 클라이언트 매칭. item_seq 만 주면 제품허가
  상세에서 품목명을 먼저 해석한다(허가취하 품목은 `item_name` 직접 전달 필요).
- 실적 API 응답의 `[{"item": {...}}]` 중첩 구조를 `_extract_items` 가 흡수.
- 금액 단위 처리: 생산=백만원, 수입=달러(USD). `ProductionRecord.amount_krw`
  는 생산만 원화 환산(수입은 None).
- CLI `--market` 옵션 — 유통 상태를 함께 출력.
- `KDRUG_SUPPLY_ENDPOINT` / `KDRUG_PRODUCTION_ENDPOINT` 환경변수 오버라이드.
- 실데이터 기반 픽스처 + 유닛 테스트 21건 추가 (레나젤 공급중단, 연도 합산,
  동명 품목 ITEM_SEQ 필터, 허가취하 해석 실패 안내 등).

### Changed
- 문서·docstring 예시 품목을 199104100(한국얀센 타이레놀 — 허가취하로 전 API
  에서 사라짐)에서 202106092(현행 타이레놀정500밀리그람)로 교체.
- README(한/영)·`docs/fields.md` 에 신규 2종 API·107개 필드 반영.

## [0.2.1] - 2026-06-12

### Docs
- README 전면 보강 — `pip install` 기준 설치, 빠른 시작 3단계, 단계별 사용법
  (품목코드/제품명/개별 API/약가 끄기), 결과 다루기 가이드, CLI 출력 예시,
  자주 묻는 질문(FAQ) 추가. 코드 변경 없음.
- **영어 README 추가** ([README.en.md](README.en.md)) + 한/영 언어 전환 링크.
- **전체 77개 컬럼 완전 수록** — `docs/fields.md` 를 한·영 병기 + 원본 API 키
  매핑으로 재작성(PillIdentity 23 · DrugPermit 13 · DrugProduct 28 · DrugCost 13),
  README 에도 전체 필드명 목록 추가.

## [0.2.0] - 2026-06-12

### Added — 약가(심평원) 4번째 소스 통합

건강보험심사평가원 약가기준 서비스(`dgamtCrtrInfoService1.2/getDgamtList`)를
4번째 소스로 추가. 그동안 식약처가 제공하지 않던 **상한가(상한금액)**가 채워진다.

- `DrugCost` dataclass + `parse_cost` + `fetch_cost(mds_cd=/item_name=/manufacturer=)`.
- `get_drug_info` 가 약가를 **제품허가 보험코드(EDI_CODE = mds_cd)로 정확 조인**한다
  (보험코드 없으면 품목명 검색). `with_cost=False` 로 끌 수 있음.
- 심평원 서비스 호환: 인증 파라미터 `ServiceKey`(대문자), 포맷 `_type=json`,
  엔드포인트 host `B551182`. `_fetch` 가 인증 파라미터명을 받도록 일반화.
- 실제 라이브 검증: 리피토정20mg → 상한가 688원이 보험코드 조인으로 정확히 채워짐.
- 실데이터 약가 픽스처 + 조인 테스트 추가.

### Changed (BREAKING) — 명칭 정리

세 번째 슬롯의 이름이 의미와 맞도록 정리됨(제품허가는 약가가 아님).

- `DrugPrice` → **`DrugProduct`**, `parse_price` → `parse_product`,
  `fetch_price` → `fetch_product`, `DrugInfo.price` → `DrugInfo.product`,
  source 라벨 `"price"` → `"product"`. (약가는 새 `DrugCost`/`cost` 가 담당.)
- `DrugProduct` 에서 미사용 `max_price`/`pay_type` 제거(약가는 `DrugCost` 로 이동).
- sources 예시: `["grn", "permit", "product", "cost"]`.

## [0.1.3] - 2026-06-12

### Fixed — 낱알식별 요청 파라미터 표기 오류 (공식 Swagger 스펙 기준)

`getMdcinGrnIdntfcInfoList03` 의 요청 파라미터는 소문자 `item_seq` / `item_name`
인데, 클라이언트가 대문자 `ITEM_SEQ` / `ITEM_NAME` 로 보내고 있었다(Service02 시절
잔재). 이 경우 필터가 무시되어 전체 목록이 반환되므로 소문자로 바로잡았다.
(제품허가 Inq07 의 item_seq 무시 버그와 동일 계열.) 응답 키는 대문자가 맞아
`parse_grn` 은 변경 없음.

- 서비스별 요청 파라미터 표기 확정: 낱알식별=`item_seq`(소문자),
  e약은요=`itemSeq`(camelCase), 제품허가=`item_seq`(소문자). 회귀 테스트 추가.

## [0.1.2] - 2026-06-12

### Fixed — e약은요 응답 필드 매핑 전면 수정 (공식 명세 IROS_239 기준)

`DrbEasyDrugInfoService`(e약은요)의 실제 응답 항목을 공식 명세로 대조한 결과,
기존 `parse_permit` 이 **엉뚱한 서비스(제품허가 상세)의 필드**(`mainIngr`,
`eeDocData`, `storageMethod` 등)를 매핑하고 있어 e약은요 응답과 전혀 맞지 않았다.
실제 e약은요 출력 필드로 바로잡았다.

- `DrugPermit` / `parse_permit` 을 e약은요 실제 필드로 재정의:
  `efficacy`(efcyQesitm) · `use_method`(useMethodQesitm) · `warning`(atpnWarnQesitm)
  · `caution`(atpnQesitm) · `interaction`(intrcQesitm) · `side_effect`(seQesitm)
  · `storage`(depositMethodQesitm) · `image_url`(itemImage) · `open_date`/`update_date`.
- 역할 정리: e약은요(DrugPermit)=환자용 복약정보, 제품허가 상세(DrugPrice)=성분·ATC·
  저장·효능/용법/주의 문서. 두 서비스가 명확히 분리됨.
- 공식 명세 샘플 기반 e약은요 파싱 테스트 추가, CLI 출력도 갱신.

## [0.1.1] - 2026-06-12

### Fixed — 실제 라이브 API 검증으로 발견한 엔드포인트 오류 수정

실제 공공데이터포털 키로 호출 검증한 결과, 구버전 엔드포인트가 폐기(404)되어
있어 바로잡았습니다.

- **낱알식별 엔드포인트**: `MdcinGrnIdntfcInfoService02/getMdcinGrnIdntfcInfoList02`
  → **`MdcinGrnIdntfcInfoService03/getMdcinGrnIdntfcInfoList03`** (구버전은 "API not found" 404)
- **제품허가 엔드포인트**: `DrugPrdtPrmsnInfoService06/getDrugPrdtPrmsnDtlInq05`
  → **`DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnDtlInq06`**
  - 같은 서비스의 목록 오퍼레이션(`getDrugPrdtPrmsnInq07`)은 **item_seq 필터가 동작하지
    않아**(항상 전체 반환) 잘못된 약이 매칭되는 문제가 있어, item_seq 로 정확히
    필터되는 상세 오퍼레이션(`getDrugPrdtPrmsnDtlInq06`)으로 확정.
- `DrugPrice` / `parse_price` 를 제품허가 상세의 실제 필드(주성분·원료·저장방법·
  유효기간·ATC·효능/용법/주의 문서 등)에 맞게 재정의. 약가(상한금액)는 식약처가
  제공하지 않으므로(HIRA 소관) `max_price` 는 비워둠.
- 실제 라이브 응답을 마스킹한 회귀 픽스처(`tests/fixtures/`)와 파싱 테스트 추가.

### Note
- 공공데이터포털 키는 **서비스별로 활용신청·승인이 따로** 필요합니다. 키가 특정
  서비스에 승인되지 않으면 해당 API 는 403 을 반환하며, `get_drug_info` 는 이를
  `result.errors` 에 담고 승인된 API 결과만 병합합니다(부분 실패 허용).

## [0.1.0] - 2026-06-12

### 최초 공개 릴리스

rxmcp 프로젝트의 Django 모듈 `dispenser/kdrug` 에서 출발해, 누구나 쓸 수 있는
독립 패키지로 재구성했습니다.

#### Added
- `KdrugClient` — 공공데이터포털 의약품 3종 API(낱알식별·허가정보·약가기준) 통합 클라이언트
- `get_drug_info()` — `ITEM_SEQ` 하나로 3종을 동시 호출해 `DrugInfo` 로 병합
- `from_env()` — `KDRUG_API_KEY` 환경변수로 생성 (기존 Django `from_settings` 대체)
- 정규화 dataclass: `DrugInfo` / `PillIdentity` / `DrugPermit` / `DrugPrice`
- 예외 계층: `KdrugError` / `KdrugAuthError` / `KdrugHTTPError` / `KdrugResponseError`
- `python -m kdrug` CLI (사람용 요약 / `--json`)
- 네트워크 mock 단위 테스트, 빠른 시작 예제, 필드 매핑 문서

- `.env` 자동 로드/생성 — 의존성 없는 `load_dotenv()`, `kdrug --init` 으로 `.env` 템플릿 생성. 실제 환경변수가 항상 우선. 저장소에는 키를 뺀 `.env.example` 만 포함.
- **Decoding/Encoding 인증키 모두 지원** — 키에 `%` 가 있으면 Encoding 키로 자동 판별해 그대로 삽입(이중 인코딩 방지), 아니면 직접 인코딩. `key_is_encoded` 로 수동 지정 가능. `DRUG_API_KEY_ENCODING` / `DRUG_API_KEY_DECODING` 환경변수도 인식(rxstock/Edge Function 시크릿 호환).

#### Changed (원본 대비)
- **Django 의존성 제거** — `urllib` 표준 라이브러리만 사용, 어떤 프로젝트에서도 동작
- 결과를 Django `Drug` 모델 대신 프레임워크 비종속 dataclass 로 반환
- 부분 실패 허용 + API별 오류 리포트(`result.errors`)
- 공공API "데이터 없음"(resultCode `03`) 을 오류가 아닌 빈 결과로 처리
- 5xx 응답에 한해 재시도(`retries`), 4xx 는 즉시 실패
- 로그에 인증키 마스킹 유지

[0.1.0]: https://github.com/lunapsy/kdrug-client/releases/tag/v0.1.0
