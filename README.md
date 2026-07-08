# kdrug-client

**한국어** · [English](README.en.md)

[![PyPI](https://img.shields.io/pypi/v/kdrug-client.svg)](https://pypi.org/project/kdrug-client/)
[![Python](https://img.shields.io/pypi/pyversions/kdrug-client.svg)](https://pypi.org/project/kdrug-client/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

공공데이터포털(data.go.kr)의 **의약품 6종 OpenAPI**(식약처 5종 + 심평원 약가)를
파이썬에서 **한 줄로** 조회하게 해주는 라이브러리입니다.

```python
from kdrug import KdrugClient

client = KdrugClient.from_env()
info = client.get_drug_info(item_name="타이레놀정500밀리그람", with_market=True).info

print(info.product.main_ingredient)   # 아세트아미노펜
print(info.identity.drug_shape)       # 장방형 (모양)
print(info.permit.efficacy)           # 이 약은 발열 및 통증에...
print(info.cost.max_price)            # 상한가 (급여 의약품인 경우)
print(info.market.is_marketed)        # 실제 유통 중인가 (with_market=True)
```

원래는 흩어진 6개의 정부 API를 각각 호출하고, 서로 다른 응답 형식을 일일이
맞춰야 했습니다. 이 라이브러리가 그걸 대신합니다.

| 무엇을 | 어디서 (API) | 어떤 정보 |
|--------|-------------|-----------|
| 🟦 **모양·색** | 낱알식별 | 알약 외형·치수·색상·식별표시(각인)·이미지 |
| 🟩 **복약정보** | e약은요 | 효능·사용법·주의·부작용·보관법 (환자용 쉬운 설명) |
| 🟧 **허가정보** | 제품허가 상세 | 주성분·ATC·저장·유효기간·효능/용법/주의 문서·보험코드 |
| 🟨 **약가** | 심평원 약가 | 건강보험 상한가·급여구분·전문/일반 |
| 🟥 **공급중단** | 생산수입공급중단 | 중단 보고·최종공급일·중단사유·자사재고량 |
| 🟪 **유통실적** | 생산·수입실적 | 연도별 생산/수입 금액 — 허가만 있는 유령 품목 판별 |

**특징**
- 🪶 **의존성 0** — 표준 라이브러리(`urllib`)만 씁니다. `pip install` 하나면 끝.
- 🔗 **자동 조인** — 품목기준코드 하나로 여러 API를 호출해 **하나의 객체**로 합쳐줍니다.
- 📦 **유통 상태 판별** — 허가만 살아있고 실제로는 생산·수입되지 않는 품목을
  걸러냅니다. 통합 조회에 포함하거나(`with_market=True`) 따로 조회할 수 있습니다.
- 🛟 **부분 실패 허용** — 한 API가 막혀도(403/오류) 나머지 데이터는 그대로 받습니다.
- 🧩 **타입 친화적** — `dataclass` 반환이라 IDE 자동완성이 됩니다.
- 💻 **CLI 포함** — 터미널에서 `kdrug --item-name 타이레놀` 한 줄로 조회.

---

## 목차
1. [설치](#설치)
2. [빠른 시작 (3단계)](#빠른-시작-3단계)
3. [인증키 발급](#인증키-발급)
4. [사용법](#사용법)
5. [결과 다루기](#결과-다루기)
6. [유통 상태 확인](#유통-상태-확인)
7. [CLI](#cli)
8. [API 레퍼런스](#api-레퍼런스)
9. [예외 처리](#예외-처리)
10. [자주 묻는 질문](#자주-묻는-질문)

---

## 설치

```bash
pip install kdrug-client
```

Python 3.9 이상이면 됩니다. 설치되면 `kdrug` 명령어도 함께 깔립니다.

---

## 빠른 시작 (3단계)

### 1. 설치
```bash
pip install kdrug-client
```

### 2. 인증키 등록
공공데이터포털에서 키를 발급받아([아래 안내](#인증키-발급)) 환경변수로 등록합니다.
```bash
export KDRUG_API_KEY="발급받은_Decoding_인증키"
```

### 3. 조회
```python
from kdrug import KdrugClient

client = KdrugClient.from_env()

# 제품명으로 검색
result = client.get_drug_info(item_name="타이레놀정500밀리그람")

if result.ok:
    info = result.info
    print("제품명:", info.item_name)
    print("주성분:", info.product.main_ingredient if info.product else "-")
    print("효능  :", info.permit.efficacy if info.permit else "-")
else:
    print("못 찾음:", result.errors)
```

끝입니다. 터미널에서 바로 확인하고 싶으면:
```bash
kdrug --item-name 타이레놀정500밀리그람
```

---

## 인증키 발급

> 키는 **무료**이고, 발급에 5~10분이면 됩니다. 한 계정의 키 하나로 6개 API를
> 모두 쓸 수 있지만, **API마다 "활용신청"을 따로 해야** 합니다.

1. [공공데이터포털](https://www.data.go.kr) 회원가입 / 로그인
2. 아래 6개 API 페이지에서 각각 **활용신청** (보통 즉시~수시간 내 자동 승인)
   - [의약품 낱알식별 정보](https://www.data.go.kr/data/15057639/openapi.do)
   - [의약품개요정보(e약은요)](https://www.data.go.kr/data/15075057/openapi.do)
   - [의약품 제품 허가정보](https://www.data.go.kr/data/15095677/openapi.do)
   - [건강보험심사평가원 약가기준정보](https://www.data.go.kr/tcs/dss/selectApiDataDetailView.do) ← 약가(별도 기관)
   - [의약품 생산수입공급중단정보](https://www.data.go.kr/data/15057899/openapi.do) ← 유통 상태용
   - [의약품 생산·수입실적현황](https://www.data.go.kr/data/15056880/openapi.do) ← 유통 상태용
3. **마이페이지 → 오픈API → 인증키 발급** 에서 **`일반 인증키 (Decoding)`** 값을 복사

> 💡 6개 다 신청하지 않아도 됩니다. 예를 들어 약가가 필요 없으면 신청을 빼세요.
> 신청 안 한 API는 자동으로 건너뜁니다(부분 실패 허용). 마지막 2개는
> `get_market_status()`(유통 상태)를 쓸 때만 필요합니다.

### 키 등록 방법

**방법 A — `.env` 파일 (권장, 한 번만 설정)**
```bash
kdrug --init          # 현재 폴더에 .env 템플릿 생성
```
생성된 `.env` 를 열어 키를 채웁니다:
```dotenv
KDRUG_API_KEY=여기에_Decoding_인증키
```
`from_env()` 와 CLI 가 현재(및 상위) 폴더의 `.env` 를 **자동으로 읽습니다.**
`.env` 는 git 에 올라가지 않게 보호됩니다.

**방법 B — 셸 환경변수**
```bash
export KDRUG_API_KEY="여기에_Decoding_인증키"
```

**방법 C — 코드에 직접 (간단 테스트용)**
```python
client = KdrugClient(api_key="여기에_인증키")
```

> ✅ **Decoding · Encoding 키 모두 자동 지원.** 키에 `%` 가 있으면 Encoding 키로
> 자동 판별합니다. `DRUG_API_KEY_ENCODING` / `DRUG_API_KEY_DECODING` 환경변수도
> 인식합니다.

---

## 사용법

### 품목기준코드(ITEM_SEQ)를 알 때 — 가장 정확

`item_seq`(품목기준코드)는 의약품의 고유 번호입니다. 알고 있다면 이게 가장 정확합니다.
```python
result = client.get_drug_info(item_seq="200410085")
```

### 제품명만 알 때

```python
result = client.get_drug_info(item_name="리피토정20밀리그램")
```
제품명은 부분 일치도 됩니다. 여러 개가 잡히면 첫 번째가 사용됩니다.

> 💡 **품목기준코드를 모를 때 찾는 법:** 먼저 이름으로 검색해 `item_seq` 를 얻고,
> 그 코드로 정확 조회하세요.
> ```python
> hits = client.fetch_grn(item_name="리피토정")     # 후보 목록
> for h in hits:
>     print(h.item_seq, h.item_name)
> ```

### 6개 중 일부만 호출하고 싶을 때

```python
# 낱알식별만 (모양·색·치수)
pills = client.fetch_grn(item_name="타이레놀")

# e약은요만 (환자용 복약정보)
guides = client.fetch_permit(item_seq="202106092")

# 제품허가 상세만 (성분·문서)
products = client.fetch_product(item_seq="202106092")

# 약가만 (상한가) — 보험코드(mds_cd)나 제품명으로
costs = client.fetch_cost(mds_cd="073400330")
costs = client.fetch_cost(item_name="리피토정20밀리그램")

# 공급중단 보고만 (품목명/업체명 — item_seq 검색은 미지원)
reports = client.fetch_supply(entp_name="한미약품")

# 생산·수입실적만 (품목명/업체명/연도/구분)
records = client.fetch_production(year="2024", part="수입")
```
각 메서드는 **리스트**를 돌려줍니다(검색 결과가 여러 건일 수 있으므로).

### 통합 조회에서 소스 켜고 끄기

약가(심평원)를 빼려면 `with_cost=False`, 유통 상태(실적+공급중단)를
포함하려면 `with_market=True`:
```python
result = client.get_drug_info(item_seq="202106092", with_cost=False)
result = client.get_drug_info(item_seq="202106092", with_market=True)
```

---

## 결과 다루기

`get_drug_info()` 는 `DrugInfoResult` 를 돌려줍니다.

```python
result = client.get_drug_info(item_seq="200410085")

result.ok            # True = 하나 이상의 API에서 데이터를 받음
result.errors        # {'permit': '...'} 처럼 실패한 API만 기록
info = result.info   # 병합된 DrugInfo
```

`info` 안에는 출처별 원본이 각각 들어 있습니다(없으면 `None`):

```python
info.item_name       # 대표 제품명
info.sources         # ['grn', 'permit', 'product', 'cost'] — 실제로 받은 출처

# 🟦 낱알식별
if info.identity:
    info.identity.drug_shape      # 모양 (예: 원형)
    info.identity.color_class1    # 색
    info.identity.length_long     # 장축 길이(mm)
    info.identity.print_front     # 앞면 각인
    info.identity.image_url       # 알약 사진 URL

# 🟩 e약은요 (환자용)
if info.permit:
    info.permit.efficacy          # 효능
    info.permit.use_method        # 사용법
    info.permit.side_effect       # 부작용
    info.permit.storage           # 보관법

# 🟧 제품허가 상세
if info.product:
    info.product.main_ingredient  # 주성분
    info.product.atc_code         # ATC 코드
    info.product.storage_method   # 저장방법
    info.product.ee_doc_data      # 효능효과 문서(HTML)
    info.product.edi_code         # 보험코드

# 🟨 약가 (심평원)
if info.cost:
    info.cost.max_price           # 상한가 (Decimal, 원)
    info.cost.pay_type            # 급여/비급여
    info.cost.spc_gnl_type        # 전문/일반

# 🟥🟪 유통 상태 — with_market=True 로 조회했을 때만 채워짐
if info.market:
    info.market.is_marketed       # 실제 유통 중인가 (실적 있음 + 중단 없음)
    info.market.latest_year       # 최근 실적 연도
    info.market.suspend_reports   # 중단 보고 원본 리스트
```

### 하나의 dict 로 평탄화

DB 저장이나 JSON 응답에 편한 형태:
```python
info.to_dict()
# {'item_seq': '200410085',
#  'item_name': '리피토정20밀리그램(아토르바스타틴칼슘삼수화물)',
#  'drug_shape': '원형', 'color1': '하양',
#  'main_ingredient': '[M215219]아토르바스타틴칼슘삼수화물',
#  'atc_code': 'C10AA05', 'edi_code': '073400330',
#  'max_price': '688', 'pay_type': '급여',
#  'sources': ['grn', 'product', 'cost'], ...}
```

`with_market=True` 로 조회했다면 유통 상태 필드(`is_marketed` `has_record`
`latest_year` `latest_amount` `market_part` `is_suspended`)도 같은 dict 에
평탄화됩니다 — [유통 상태 확인](#유통-상태-확인) 참조.

> 비급여/일반의약품(OTC)은 보험 약가가 없어 `info.cost` 가 비어 있을 수 있습니다.
> 정상입니다.

---

## 유통 상태 확인

허가는 살아있는데 **실제로는 생산도 수입도 하지 않는 품목**이 있습니다.
생산·수입실적과 공급중단 보고 2종 API를 결합해 "이 약이 실제로 시장에
공급되고 있는가?"를 한 번에 답합니다.

**방법 1 — 통합 조회에 포함** (`with_market=True`): 유통 상태 필드가
`to_dict()` 평탄화에 함께 들어갑니다.

```python
result = client.get_drug_info(item_seq="202106092", with_market=True)

info = result.info
info.market.is_marketed    # 원본 dataclass 로 접근
info.to_dict()             # 평탄화 dict 에 유통 필드 포함:
# {'item_name': '타이레놀정500밀리그람...', 'atc_code': 'N02BE01', ...
#  'is_marketed': True, 'has_record': True, 'latest_year': '2024',
#  'latest_amount': '27343800', 'market_part': '수입', 'is_suspended': False,
#  'sources': ['grn', 'permit', 'product', 'market']}
```

**방법 2 — 유통 상태만 따로 조회/갱신** (`get_market_status()`):
실적은 연 1회, 공급중단 보고는 일 1회 갱신되므로 유통 상태만 주기적으로
다시 확인할 때 유용합니다.

```python
result = client.get_market_status(item_seq="202106092")
s = result.status

s.is_marketed      # True = 생산/수입 실적 있음 + 공급중단 보고 없음
s.has_record       # 생산/수입 실적 존재 여부 (식약처 연간 집계)
s.latest_year      # 가장 최근 실적 연도 — "2024"
s.latest_amount    # 그 해 실적 합계 (단위는 s.part 참조 — 아래 주의)
s.part             # "생산" 또는 "수입"
s.is_suspended     # 공급중단 보고 존재 여부
s.suspend_reports  # SupplyReport 리스트 — 중단사유·최종공급일·자사재고량
s.records          # ProductionRecord 리스트 — 연도별 원본 실적
```

두 API 를 따로 쓸 수도 있습니다:

```python
# 공급중단 보고 검색 (업체명/품목명)
reports = client.fetch_supply(entp_name="한미약품")
for r in reports:
    print(r.suspend_date, r.is_suspended, r.suspend_reason)

# 생산·수입실적 검색 (연도/구분/업체명/품목명)
records = client.fetch_production(year="2024", part="수입", rows=20)
for r in records:
    print(r.year, r.part, r.amount)
```

> **⚠️ 금액 단위가 구분마다 다릅니다** — 생산은 **백만원**, 수입은 **달러(USD)**.
> 생산 실적의 원화 환산은 `record.amount_krw` 를 쓰세요 (수입은 환율이 필요해 `None`).

> **⚠️ 두 API 모두 item_seq 검색이 안 됩니다** (파라미터를 보내도 무시 — 라이브 확인).
> 그래서 품목명으로 검색한 뒤 응답의 `ITEM_SEQ` 로 클라이언트가 매칭합니다.
> `item_seq` 만 넘기면 제품허가 상세에서 품목명을 먼저 해석합니다(API 1회 추가).

> **⚠️ 허가취하 품목은 `item_name` 을 함께 넘기세요** — 허가가 취하되면 제품허가
> API에서 사라져 품목명 해석이 불가능합니다. 공급중단된 품목일수록 흔한 경우입니다:
> `client.get_market_status(item_seq=seq, item_name="레나젤정800(세벨라머염산염)")`

---

## CLI

설치하면 `kdrug` 명령을 바로 쓸 수 있습니다.

```bash
# 품목기준코드로 조회 (사람이 읽기 좋은 요약)
kdrug --item-seq 200410085

# 제품명으로 검색
kdrug --item-name 타이레놀

# JSON 출력 (다른 도구로 넘기기 좋음)
kdrug --item-seq 200410085 --json

# 유통 상태까지 함께 조회
kdrug --item-seq 202106092 --market

# .env 템플릿 만들기
kdrug --init
```

출력 예시:
```
■ 리피토정20밀리그램(아토르바스타틴칼슘삼수화물)  (200410085)
  제조/수입: 비아트리스코리아(주)
  데이터 출처: grn, product, cost
  [낱알식별]
    제형/모양: 필름코팅정 / 원형
    치수(mm): 7.5 × 7.5 × 4.5
    색상: 하양
    식별표시: 앞 'ATV' / 뒤 '20'
  [제품허가 상세]
    주성분: [M215219]아토르바스타틴칼슘삼수화물
    ATC: C10AA05  허가일: 20041025  보험코드: 073400330
  [약가 (심평원)]
    상한가: 688원  급여: 급여  전문
```

> `kdrug` 가 인식되지 않으면 `python3 -m kdrug --item-name 타이레놀` 로 쓰세요.

---

## API 레퍼런스

### `KdrugClient`

| 메서드 | 반환 | 설명 |
|--------|------|------|
| `KdrugClient(api_key=...)` | — | 키를 직접 지정해 생성 |
| `KdrugClient.from_env()` | `KdrugClient` | 환경변수/`.env` 로 생성 |
| `get_drug_info(item_seq=, item_name=, with_cost=True, with_market=False, strict=False)` | `DrugInfoResult` | **통합 조회 (권장)** — `with_market=True` 면 유통 상태 포함 |
| `get_market_status(item_seq=, item_name=, rows=50, strict=False)` | `MarketStatusResult` | **유통 상태 (실적+공급중단 결합)** |
| `fetch_grn(item_seq=, item_name=, rows=10)` | `list[PillIdentity]` | 낱알식별만 |
| `fetch_permit(...)` | `list[DrugPermit]` | e약은요만 |
| `fetch_product(...)` | `list[DrugProduct]` | 제품허가 상세만 |
| `fetch_cost(mds_cd=, item_name=, manufacturer=)` | `list[DrugCost]` | 약가만 (심평원) |
| `fetch_supply(item_name=, entp_name=)` | `list[SupplyReport]` | 공급중단 보고만 |
| `fetch_production(item_name=, entp_name=, year=, part=)` | `list[ProductionRecord]` | 생산·수입실적만 |
| `fetch_grn_raw(...)` 등 | `list[dict]` | 가공 전 원본 응답 |

생성자 옵션: `timeout`(기본 8초), `retries`(기본 2회),
`grn_endpoint`/`permit_endpoint`/`product_endpoint`/`cost_endpoint`/
`supply_endpoint`/`production_endpoint` 오버라이드, `user_agent`.

### `DrugInfoResult`
- `.info` → `DrugInfo` (병합 결과)
- `.errors` → `{api_name: error_msg}` (실패한 API만)
- `.ok` / `bool(result)` → 하나 이상 데이터를 받았는가

### `MarketStatusResult`
- `.status` → `MarketStatus` (유통 상태 — `is_marketed` / `has_record` / `is_suspended`)
- `.errors` → `{api_name: error_msg}` (실패한 API만)
- `.ok` / `bool(result)` → 실적 또는 중단 보고를 하나라도 확인했는가

### dataclass
- `DrugInfo` — `item_seq`, `item_name`, `entp_name`, `sources`, `identity`, `permit`, `product`, `cost`, `.to_dict()`
- `PillIdentity` — 낱알식별 (치수·색상·식별표시·이미지)
- `DrugPermit` — e약은요 (효능·사용법·주의·부작용·보관·낱알이미지)
- `DrugProduct` — 제품허가 상세 (성분·ATC·저장·허가일·효능/용법/주의 문서·보험코드)
- `DrugCost` — 약가 (`max_price` 상한가 `Decimal`·급여구분·주성분코드)
- `SupplyReport` — 공급중단 보고 (`is_suspended`·중단사유·최종공급일·자사재고량)
- `ProductionRecord` — 생산·수입실적 (`amount` `Decimal`·`is_production`/`is_import`·`amount_krw`)
- `MarketStatus` — 유통 상태 요약 (`is_marketed`·최근 실적·중단 보고)

### 전체 필드 목록 (107개)

한·영 설명과 원본 API 키 매핑은 [`docs/fields.md`](docs/fields.md) 에 표로 정리돼
있습니다. 필드명만 한눈에:

**🟦 PillIdentity (23)** — `item_seq` `item_name` `entp_name` `bizrno`
`length_long` `length_short` `thickness` `drug_shape` `form_code_name`
`is_capsule` `color_class1` `color_class2` `print_front` `print_back`
`mark_front` `mark_back` `line_front` `line_back` `class_no` `class_name`
`etc_otc` `chart` `image_url`

**🟩 DrugPermit (13)** — `item_seq` `item_name` `entp_name` `efficacy`
`use_method` `warning` `caution` `interaction` `side_effect` `storage`
`open_date` `update_date` `image_url`

**🟧 DrugProduct (28)** — `item_seq` `item_name` `item_eng_name` `entp_name`
`entp_eng_name` `bizrno` `main_ingredient` `main_ingredient_eng` `material_name`
`storage_method` `valid_term` `pack_unit` `total_content` `atc_code`
`etc_otc_code` `permit_kind_name` `newdrug_class_name` `narcotic_kind_code`
`rare_drug_yn` `chart` `item_permit_date` `cancel_date` `cancel_name` `edi_code`
`bar_code` `ee_doc_data` `ud_doc_data` `nb_doc_data`

**🟨 DrugCost (13)** — `mds_cd` `item_name` `manufacturer` `max_price` `pay_type`
`spc_gnl_type` `injection_path` `gnl_name_code` `unit` `spec_name` `meft_div_no`
`substitutable` `apply_start_date`

**🟥 SupplyReport (21)** — `item_seq` `item_name` `edi_code` `entp_name`
`entp_seq` `bizrno` `report_flag` `report_seq` `report_progress` `supply_yn`
`last_supply_date` `suspend_date` `suspend_flag` `inventory_date` `inventory_qty`
`suspend_reason` `shortage_risk` `supply_plan` `report_date` `processed_date`
`address` (+ `is_suspended` 속성)

**🟪 ProductionRecord (8)** — `item_seq` `item_name` `entp_name` `entp_seq`
`bizrno` `year` `part` `amount` (+ `is_production` `is_import` `amount_krw` 속성)

**MarketStatus (9)** — `item_seq` `item_name` `has_record` `latest_year`
`latest_amount` `part` `records` `is_suspended` `suspend_reports`
(+ `is_marketed` 속성)

---

## 예외 처리

```python
from kdrug import KdrugError, KdrugAuthError, KdrugHTTPError, KdrugResponseError

try:
    result = client.get_drug_info(item_seq="200410085", strict=True)
except KdrugAuthError:
    ...   # 인증키 누락/오류
except KdrugHTTPError as e:
    ...   # 네트워크/HTTP 실패 (e.status_code)
except KdrugResponseError as e:
    ...   # 공공API resultCode 오류 (e.result_code)
except KdrugError:
    ...   # 위 모두의 부모 — 한 번에 잡기
```

기본값(`strict=False`)은 예외를 던지지 않고, 실패한 API를 `result.errors` 에
모은 뒤 **성공한 데이터만 병합**합니다. 공공API의 "데이터 없음"(resultCode `03`)은
오류가 아니라 빈 결과로 처리합니다.

---

## 자주 묻는 질문

**Q. `item_seq` 가 뭔가요?**
품목기준코드 — 의약품마다 부여된 고유 번호입니다. 모르면 `item_name`(제품명)으로
검색하면 됩니다.

**Q. 어떤 API는 403(Forbidden)이 떠요.**
그 API에 대한 **활용신청이 아직 승인되지 않은** 것입니다. 공공데이터포털에서 해당
API를 활용신청하세요. 승인 직후 키에 반영되기까지 수십 분~수 시간 걸릴 수 있습니다.
그동안에도 승인된 API 결과는 정상적으로 받습니다.

**Q. 약에 따라 e약은요(또는 특정 소스)가 비어 있어요.**
**버그가 아닙니다.** 네 API는 각각 수록 범위가 다릅니다. 예를 들어 e약은요는
타이레놀처럼 흔한 약 위주로 채워져 있어, 일부 전문의약품(예: 리피토)은 `info.permit`
이 비어 있을 수 있습니다. 이 경우 `result.errors` 는 비어 있고(오류가 아니므로)
나머지 소스는 정상 병합됩니다. `info.sources` 로 실제 받은 소스를 확인하세요.

**Q. `info.cost`(약가)가 비어 있어요.**
일반의약품(OTC)·비급여 품목은 건강보험 약가가 없습니다. 정상입니다.

**Q. 키를 넣었는데 인증 오류가 나요.**
`Decoding(일반 인증키)` 값을 쓰는지 확인하세요. (Encoding 키도 자동 지원하지만,
직접 다룰 땐 Decoding 권장.)

**Q. 엔드포인트가 바뀌면요?**
정부 API는 가끔 버전을 올립니다. 생성자 인자나 `KDRUG_*_ENDPOINT` 환경변수로
주소를 덮어쓸 수 있습니다.

---

## 개발 / 기여

```bash
git clone https://github.com/lunapsy/kdrug-client.git
cd kdrug-client
pip install -e ".[dev]"
pytest            # 네트워크 없이 동작 (응답을 mock)
```

이슈·PR 환영합니다: https://github.com/lunapsy/kdrug-client

---

## 라이선스

MIT — 자유롭게 사용/수정/배포하세요. 자세한 내용은 [LICENSE](LICENSE).

> 이 라이브러리는 공공데이터포털 데이터를 **가공해 전달**할 뿐이며, 데이터의
> 정확성·최신성은 원 제공기관(식품의약품안전처·건강보험심사평가원)을 따릅니다.
> 임상적 판단의 최종 근거로 쓰기 전 원본을 확인하세요.
