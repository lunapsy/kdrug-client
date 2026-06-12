# kdrug-client

[한국어](README.md) · **English**

[![PyPI](https://img.shields.io/pypi/v/kdrug-client.svg)](https://pypi.org/project/kdrug-client/)
[![Python](https://img.shields.io/pypi/pyversions/kdrug-client.svg)](https://pypi.org/project/kdrug-client/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A Python client that queries **four Korean government drug OpenAPIs** (three from
the MFDS + one drug-price API from HIRA) with **a single call**.

```python
from kdrug import KdrugClient

client = KdrugClient.from_env()
info = client.get_drug_info(item_name="타이레놀정500밀리그람").info

print(info.product.main_ingredient)   # acetaminophen
print(info.identity.drug_shape)       # shape
print(info.permit.efficacy)           # patient-friendly indications
print(info.cost.max_price)            # ceiling price (if reimbursed)
```

Instead of calling four separate government APIs and reconciling their different
response formats by hand, this library does it for you. (The data is Korean.)

| What | Source API | Information |
|------|-----------|-------------|
| 🟦 **Shape & color** | Pill identification | shape, dimensions, color, imprint, image |
| 🟩 **Patient info** | e약은요 (easy drug info) | efficacy, usage, precautions, side effects, storage |
| 🟧 **Permit detail** | Product permit detail | ingredient, ATC, storage, documents, insurance code |
| 🟨 **Price** | HIRA drug price | NHI ceiling price, reimbursement type, Rx/OTC |

**Highlights**
- 🪶 **Zero dependencies** — standard library (`urllib`) only.
- 🔗 **Automatic join** — one item code calls all four APIs and merges into one object.
- 🛟 **Partial-failure tolerant** — if one API is blocked (403/error), you still get the rest.
- 🧩 **Typed** — returns `dataclass`es for IDE autocompletion.
- 💻 **CLI included** — `kdrug --item-name 타이레놀` in the terminal.

---

## Table of contents
1. [Install](#install)
2. [Quick start (3 steps)](#quick-start-3-steps)
3. [Getting an API key](#getting-an-api-key)
4. [Usage](#usage)
5. [Working with the result](#working-with-the-result)
6. [CLI](#cli)
7. [API reference](#api-reference)
8. [Error handling](#error-handling)
9. [FAQ](#faq)

---

## Install

```bash
pip install kdrug-client
```

Requires Python 3.9+. A `kdrug` command-line tool is installed too.

---

## Quick start (3 steps)

### 1. Install
```bash
pip install kdrug-client
```

### 2. Register your API key
Get a key from the Korean public data portal ([see below](#getting-an-api-key))
and set it as an environment variable:
```bash
export KDRUG_API_KEY="your_Decoding_service_key"
```

### 3. Query
```python
from kdrug import KdrugClient

client = KdrugClient.from_env()

result = client.get_drug_info(item_name="타이레놀정500밀리그람")

if result.ok:
    info = result.info
    print("name      :", info.item_name)
    print("ingredient :", info.product.main_ingredient if info.product else "-")
    print("efficacy   :", info.permit.efficacy if info.permit else "-")
else:
    print("not found:", result.errors)
```

Or from the terminal:
```bash
kdrug --item-name 타이레놀정500밀리그람
```

---

## Getting an API key

> The key is **free** and takes about 5–10 minutes. One account's key works for
> all four APIs, but you must **request access to each API separately**.

1. Sign up / log in at the [public data portal](https://www.data.go.kr).
2. Request access ("활용신청") on each of the four API pages
   (usually auto-approved within minutes to a few hours):
   - [Pill identification](https://www.data.go.kr/data/15057639/openapi.do)
   - [e약은요 (easy drug info)](https://www.data.go.kr/data/15075057/openapi.do)
   - [Product permit info](https://www.data.go.kr/data/15095677/openapi.do)
   - [HIRA drug price](https://www.data.go.kr/tcs/dss/selectApiDataDetailView.do) (separate agency)
3. In **My Page → Open API → keys**, copy the **`Decoding` (general service key)**.

> 💡 You don't need all four. If you don't need price, request only the first
> three — unrequested APIs are simply skipped (partial-failure tolerant).

### Registering the key

**Option A — `.env` file (recommended)**
```bash
kdrug --init          # creates a .env template in the current folder
```
Open `.env` and fill in the key:
```dotenv
KDRUG_API_KEY=your_Decoding_service_key
```
`from_env()` and the CLI auto-read `.env` from the current (and parent) folders.
`.env` is protected from being committed to git.

**Option B — shell environment variable**
```bash
export KDRUG_API_KEY="your_Decoding_service_key"
```

**Option C — directly in code (quick test)**
```python
client = KdrugClient(api_key="your_service_key")
```

> ✅ Both **Decoding and Encoding** keys are supported automatically (a key
> containing `%` is treated as Encoding). `DRUG_API_KEY_ENCODING` /
> `DRUG_API_KEY_DECODING` env vars are also recognized.

---

## Usage

### When you know the item code (ITEM_SEQ) — most precise
```python
result = client.get_drug_info(item_seq="200410085")
```

### When you only know the product name
```python
result = client.get_drug_info(item_name="리피토정20밀리그램")
```
Partial name matches work; if several match, the first is used.

> 💡 **To find an item code:** search by name first to get an `item_seq`, then
> query precisely by that code.
> ```python
> for h in client.fetch_grn(item_name="리피토정"):
>     print(h.item_seq, h.item_name)
> ```

### Calling only some of the four APIs
```python
pills    = client.fetch_grn(item_name="타이레놀")     # pill identification
guides   = client.fetch_permit(item_seq="202106092")  # e약은요
products = client.fetch_product(item_seq="202106092") # product permit detail
costs    = client.fetch_cost(mds_cd="073400330")      # price (by insurance code)
costs    = client.fetch_cost(item_name="리피토정20밀리그램")
```
Each returns a **list** (a search may return several rows).

### Turning off the price lookup
```python
result = client.get_drug_info(item_seq="202106092", with_cost=False)
```

---

## Working with the result

`get_drug_info()` returns a `DrugInfoResult`:
```python
result.ok            # True = got data from at least one API
result.errors        # {'permit': '...'} — only failed APIs
info = result.info   # the merged DrugInfo
```

`info` holds the four sources (each `None` if absent):
```python
info.item_name       # representative product name
info.sources         # ['grn', 'permit', 'product', 'cost'] — sources actually received

if info.identity:    # 🟦 pill identification
    info.identity.drug_shape, info.identity.color_class1
    info.identity.length_long, info.identity.print_front, info.identity.image_url

if info.permit:      # 🟩 e약은요 (patient)
    info.permit.efficacy, info.permit.use_method
    info.permit.side_effect, info.permit.storage

if info.product:     # 🟧 product permit detail
    info.product.main_ingredient, info.product.atc_code
    info.product.storage_method, info.product.ee_doc_data, info.product.edi_code

if info.cost:        # 🟨 price (HIRA)
    info.cost.max_price, info.cost.pay_type, info.cost.spc_gnl_type
```

### Flatten to a single dict
```python
info.to_dict()
# {'item_seq': '200410085', 'item_name': '리피토정20밀리그램...',
#  'main_ingredient': '...', 'atc_code': 'C10AA05', 'edi_code': '073400330',
#  'max_price': '688', 'pay_type': '급여',
#  'sources': ['grn', 'product', 'cost'], ...}
```

> OTC / non-reimbursed drugs have no NHI price, so `info.cost` may be empty. That's normal.

---

## CLI

```bash
kdrug --item-seq 200410085        # human-readable summary
kdrug --item-name 타이레놀         # search by name
kdrug --item-seq 200410085 --json # JSON output
kdrug --init                      # create a .env template
```

If `kdrug` isn't found, use `python3 -m kdrug --item-name 타이레놀`.

---

## API reference

### `KdrugClient`

| method | returns | description |
|--------|---------|-------------|
| `KdrugClient(api_key=...)` | — | create with an explicit key |
| `KdrugClient.from_env()` | `KdrugClient` | create from env / `.env` |
| `get_drug_info(item_seq=, item_name=, with_cost=True, strict=False)` | `DrugInfoResult` | **4-API merged lookup (recommended)** |
| `fetch_grn(item_seq=, item_name=, rows=10)` | `list[PillIdentity]` | pill identification |
| `fetch_permit(...)` | `list[DrugPermit]` | e약은요 |
| `fetch_product(...)` | `list[DrugProduct]` | product permit detail |
| `fetch_cost(mds_cd=, item_name=, manufacturer=)` | `list[DrugCost]` | price (HIRA) |
| `fetch_grn_raw(...)` etc. | `list[dict]` | raw, unparsed responses |

Constructor options: `timeout` (default 8s), `retries` (default 2),
`grn_endpoint`/`permit_endpoint`/`product_endpoint`/`cost_endpoint` overrides, `user_agent`.

### `DrugInfoResult`
- `.info` → `DrugInfo` (merged)
- `.errors` → `{api_name: error_msg}` (failed APIs only)
- `.ok` / `bool(result)` → received data from at least one API

### dataclasses
- `DrugInfo` — `item_seq`, `item_name`, `entp_name`, `sources`, `identity`, `permit`, `product`, `cost`, `.to_dict()`
- `PillIdentity` — pill identification (dimensions, color, imprint, image)
- `DrugPermit` — e약은요 (efficacy, usage, precautions, side effects, storage, image)
- `DrugProduct` — product permit detail (ingredient, ATC, storage, permit date, documents, insurance code)
- `DrugCost` — price (`max_price` ceiling `Decimal`, reimbursement type, ingredient code)

### All fields (77)

Bilingual descriptions and raw-API-key mapping are in
[`docs/fields.md`](docs/fields.md). Field names at a glance:

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

---

## Error handling

```python
from kdrug import KdrugError, KdrugAuthError, KdrugHTTPError, KdrugResponseError

try:
    result = client.get_drug_info(item_seq="200410085", strict=True)
except KdrugAuthError:
    ...   # missing/invalid key
except KdrugHTTPError as e:
    ...   # network/HTTP failure (e.status_code)
except KdrugResponseError as e:
    ...   # API resultCode error (e.result_code)
except KdrugError:
    ...   # base class — catch them all
```

By default (`strict=False`) no exception is raised: failed APIs go into
`result.errors` and only the successful data is merged. The portal's
"no data" (resultCode `03`) is treated as an empty result, not an error.

---

## FAQ

**Q. What is `item_seq`?**
The item serial code — a unique number per drug. If you don't know it, search by
`item_name` (product name).

**Q. One of the APIs returns 403 (Forbidden).**
You haven't been approved for that API yet. Request access on the portal.
Approval can take minutes to hours to propagate to your key. Meanwhile the
approved APIs still return data.

**Q. For some drugs, e약은요 (or another source) is empty.**
**That's not a bug.** Each of the four APIs covers a different set of drugs.
e약은요, for example, mostly covers common drugs, so some prescription drugs
(e.g. Lipitor) may have an empty `info.permit`. In that case `result.errors` is
empty (it isn't an error) and the other sources are merged normally. Check
`info.sources` to see which sources you actually received.

**Q. `info.cost` (price) is empty.**
OTC / non-reimbursed drugs have no NHI price. That's normal.

**Q. Authentication fails even with a key.**
Make sure you use the `Decoding` (general) service key. (Encoding keys are also
auto-supported, but Decoding is recommended when handling it yourself.)

**Q. What if an endpoint changes?**
Government APIs occasionally bump versions. Override the URL via constructor args
or `KDRUG_*_ENDPOINT` env vars.

---

## Development

```bash
git clone https://github.com/lunapsy/kdrug-client.git
cd kdrug-client
pip install -e ".[dev]"
pytest            # runs offline (responses are mocked)
```

Issues and PRs welcome: https://github.com/lunapsy/kdrug-client

---

## License

MIT — use, modify, and distribute freely. See [LICENSE](LICENSE).

> This library merely **relays** public-portal data; accuracy and currency
> depend on the original providers (MFDS and HIRA). Verify against the source
> before using it as a basis for any clinical decision.
