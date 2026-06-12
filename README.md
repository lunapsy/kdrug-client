# kdrug-client

공공데이터포털(data.go.kr)이 제공하는 **의약품 4종 OpenAPI**(식약처 3종 + 심평원
약가)를 하나의 파이썬 클라이언트로 묶어주는 라이브러리입니다.

| API | 서비스/오퍼레이션 (2026-06 현행) | 주는 정보 |
|-----|----------|-----------|
| 🟦 낱알식별 | `MdcinGrnIdntfcInfoService03/getMdcinGrnIdntfcInfoList03` | 알약 외형·치수·색상·식별표시·이미지 |
| 🟩 e약은요 | `DrbEasyDrugInfoService/getDrbEasyDrugList` | 환자용 복약정보 — 효능·사용법·주의·상호작용·부작용·보관·낱알이미지 |
| 🟧 제품허가 상세 | `DrugPrdtPrmsnInfoService07/getDrugPrdtPrmsnDtlInq06` | 주성분·원료·저장·유효기간·ATC·효능/용법/주의 문서·보험코드 |
| 🟨 약가 (심평원) | `dgamtCrtrInfoService1.2/getDgamtList` | 건강보험 상한가·급여구분·전문/일반·투여경로·주성분코드 |

식약처 3종은 **`ITEM_SEQ`(품목기준코드)** 로 조인하고, 심평원 약가는 ITEM_SEQ가
없으므로 **제품허가의 보험코드(`EDI_CODE` = 약가 `mds_cd`)로 정확 조인**합니다
(보험코드가 없으면 품목명으로 검색). `get_drug_info` 한 번이면 네 API를 모두 호출해
**정규화된 하나의 객체**로 합쳐줍니다.

> ✅ 네 엔드포인트 모두 실제 공공데이터포털 키로 **라이브 호출 검증**을 마쳤습니다.
> (예: 리피토정20mg → 상한가 688원이 보험코드 조인으로 채워짐. 비급여/OTC 품목은
> 약가가 없습니다.)
>
> ⚠️ **공공데이터포털 키는 네 API에 각각 "활용신청"이 필요합니다**(약가는 심평원
> 서비스라 별도). 승인 안 된 API는 403 을 반환하고, `get_drug_info` 는 이를
> `result.errors` 에 담은 뒤 승인된 API 결과만 병합합니다(부분 실패 허용). 약가
> 조회를 끄려면 `get_drug_info(..., with_cost=False)`.

- **외부 의존성 0** — 표준 라이브러리(`urllib`)만 사용합니다.
- **부분 실패 허용** — 한 API가 죽어도 나머지 데이터는 그대로 받습니다.
- **표기 흡수** — API마다 다른 `UPPER_SNAKE` / `camelCase` 키를 한 번에 정리합니다.
- **타입 친화적** — `dataclass` 로 반환, IDE 자동완성이 됩니다.
- **CLI 포함** — 터미널에서 `python -m kdrug --item-seq ...` 로 바로 조회.

> ℹ️ 원래 [rxmcp](https://github.com/lunapsy/rxmcp) 프로젝트의 Django 모듈
> `dispenser/kdrug` 에서 출발했으며, 누구나 쓸 수 있도록 프레임워크 의존성을
>걷어내고 독립 패키지로 재구성했습니다.

---

## 설치

```bash
pip install kdrug-client
```

아직 PyPI에 올리기 전이라면 소스에서:

```bash
git clone https://github.com/lunapsy/kdrug-client.git
cd kdrug-client
pip install -e .
```

Python 3.9 이상이면 동작합니다.

---

## 인증키 발급 (5분)

1. [공공데이터포털](https://www.data.go.kr) 로그인
2. 아래 4개 API "활용신청" (보통 즉시~수시간 내 승인)
   - [의약품 낱알식별 정보](https://www.data.go.kr/data/15057639/openapi.do)
   - [의약품개요정보(e약은요)](https://www.data.go.kr/data/15075057/openapi.do)
   - [의약품 제품 허가정보](https://www.data.go.kr/data/15095677/openapi.do)
   - [건강보험심사평가원 약가기준정보(getDgamtList)](https://www.data.go.kr/tcs/dss/selectApiDataDetailView.do) ← 약가, 별도 기관
3. 마이페이지 → 인증키에서 **Decoding(일반 인증키)** 값을 복사
4. 키를 등록 — 아래 둘 중 편한 방법

**방법 A — `.env` 파일 (권장)**

```bash
kdrug --init          # 현재 폴더에 .env 템플릿 생성 (python -m kdrug --init)
```

생성된 `.env` 를 열어 키를 채웁니다:

```dotenv
KDRUG_API_KEY=여기에_Decoding_인증키
```

`from_env()` 와 CLI 가 현재 폴더(및 상위 폴더)의 `.env` 를 **자동으로 읽습니다.**
`.env` 는 `.gitignore` 로 보호되어 **git 에 절대 올라가지 않습니다.** 저장소에는
키를 뺀 `.env.example` 만 포함됩니다.

**방법 B — 셸 환경변수**

```bash
export KDRUG_API_KEY="여기에_Decoding_인증키"
```

> ✅ **Decoding · Encoding 키 모두 지원합니다.** 키에 `%` 가 있으면 Encoding 키로
> 자동 판별해 그대로 사용하고(이중 인코딩 방지), 없으면 Decoding 키로 보고 직접
> 인코딩합니다. 자동 판별을 끄려면 `KdrugClient(api_key=..., key_is_encoded=True)`
> 처럼 명시하세요.
>
> ℹ️ `KDRUG_API_KEY` 외에 `DRUG_API_KEY_ENCODING` / `DRUG_API_KEY_DECODING`
> 환경변수도 인식합니다(rxstock / Supabase Edge Function 시크릿과 동일한 이름이라
> 그대로 재사용 가능). 실제 셸 환경변수가 항상 `.env` 파일보다 우선하며, `.env`
> 자동 로드를 끄려면 `KdrugClient.from_env(use_dotenv=False)`.

---

## 빠른 시작

```python
from kdrug import KdrugClient

client = KdrugClient.from_env()            # KDRUG_API_KEY 환경변수 사용
# client = KdrugClient(api_key="...")      # 직접 넘겨도 됩니다

result = client.get_drug_info(item_seq="200410085")   # 리피토정20mg (급여)

if result.ok:
    info = result.info
    print(info.item_name)                  # 리피토정20밀리그램(...)
    print(info.sources)                    # ['grn', 'permit', 'product', 'cost']
    print(info.identity.length_long)       # 낱알식별 치수
    print(info.product.main_ingredient)    # 아토르바스타틴... (제품허가)
    print(info.cost.max_price)             # 688 (약가 상한가, Decimal)
else:
    print("데이터 없음:", result.errors)
```

평탄화된 단일 dict 로도 받을 수 있습니다 (DB 저장·JSON 직렬화에 편리):

```python
info.to_dict()
# {'item_seq': '200410085', 'item_name': '리피토정20밀리그램...',
#  'main_ingredient': '아토르바스타틴...', 'edi_code': '073400330',
#  'max_price': '688', 'pay_type': '급여',
#  'sources': ['grn', 'permit', 'product', 'cost'], ...}
```

---

## CLI

```bash
export KDRUG_API_KEY="..."

# 사람이 읽기 좋은 요약
python -m kdrug --item-seq 199104100

# 제품명으로 검색
python -m kdrug --item-name 타이레놀

# JSON 출력 (파이프라인용)
python -m kdrug --item-seq 199104100 --json
```

`pip install` 후에는 `kdrug --item-seq 199104100` 처럼 짧게 쓸 수 있습니다.

---

## API 레퍼런스

### `KdrugClient`

| 메서드 | 반환 | 설명 |
|--------|------|------|
| `KdrugClient(api_key=...)` | — | 키를 직접 지정해 생성 |
| `KdrugClient.from_env()` | `KdrugClient` | `KDRUG_API_KEY` 환경변수로 생성 |
| `get_drug_info(item_seq=, item_name=, with_cost=True, strict=False)` | `DrugInfoResult` | **4종 통합 조회 (권장)** |
| `fetch_grn(item_seq=, item_name=, rows=10)` | `list[PillIdentity]` | 낱알식별만 |
| `fetch_permit(...)` | `list[DrugPermit]` | e약은요만 |
| `fetch_product(...)` | `list[DrugProduct]` | 제품허가 상세만 |
| `fetch_cost(mds_cd=, item_name=, manufacturer=)` | `list[DrugCost]` | 약가만 (심평원) |
| `fetch_grn_raw(...)` 등 | `list[dict]` | 가공 전 원본 응답 |

생성자 옵션: `timeout`(기본 8초), `retries`(기본 2회), `grn_endpoint`/`permit_endpoint`/
`product_endpoint`/`cost_endpoint` 오버라이드, `user_agent`.

`get_drug_info` 의 `strict=True` 로 두면 일부 API 실패 시 예외를 던집니다.
기본값(`False`)은 실패를 `result.errors` 에 모으고 받은 데이터만 병합합니다.

### `DrugInfoResult`

- `.info` → `DrugInfo` (병합 결과)
- `.errors` → `{api_name: error_msg}` (실패한 API)
- `.ok` / `bool(result)` → 하나 이상 데이터를 받았는가

### dataclass

- `DrugInfo` — `item_seq`, `item_name`, `entp_name`, `sources`, `identity`, `permit`, `product`, `cost`, `.to_dict()`
- `PillIdentity` — 낱알식별 (치수·색상·식별표시·이미지)
- `DrugPermit` — e약은요 (효능·사용법·주의·부작용·보관·낱알이미지)
- `DrugProduct` — 제품허가 상세 (성분·ATC·저장·허가일·효능/용법/주의 문서·보험코드)
- `DrugCost` — 약가 (`max_price` 상한가 `Decimal`·급여구분·주성분코드)

전체 필드는 [`docs/fields.md`](docs/fields.md) 에 표로 정리돼 있습니다.

---

## 예외 처리

```python
from kdrug import KdrugError, KdrugAuthError, KdrugHTTPError, KdrugResponseError

try:
    result = client.get_drug_info(item_seq="199104100", strict=True)
except KdrugAuthError:
    ...   # 인증키 누락/오류
except KdrugHTTPError as e:
    ...   # 네트워크/HTTP 실패 (e.status_code)
except KdrugResponseError as e:
    ...   # 공공API resultCode 오류 (e.result_code)
except KdrugError:
    ...   # 위 모두의 부모 — 한 번에 잡기
```

공공데이터포털의 "데이터 없음"(resultCode `03`)은 **오류가 아니라 빈 결과**로
처리합니다.

---

## 개발

```bash
pip install -e ".[dev]"
pytest            # 네트워크 없이 동작 (응답을 mock)
```

---

## 라이선스

MIT — 자유롭게 사용/수정/배포하세요. 자세한 내용은 [LICENSE](LICENSE).

이 라이브러리는 공공데이터포털 데이터를 **가공해 전달**할 뿐이며, 데이터의
정확성·최신성은 원 제공기관(식품의약품안전처)에 따릅니다. 임상적 판단의 최종
근거로 사용하기 전 원본을 확인하세요.
