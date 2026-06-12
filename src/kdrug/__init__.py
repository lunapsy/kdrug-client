"""kdrug-client — 공공데이터포털 의약품 4종 OpenAPI 통합 클라이언트.

식약처(낱알식별 · e약은요 · 제품허가 상세)와 건강보험심사평가원(약가) 의 네 가지
의약품 API를 한 번에 묶어준다. 식약처 3종은 ``ITEM_SEQ`` 로, 약가는 제품허가의
보험코드(EDI_CODE = mds_cd) 로 정확 조인된다.

빠른 시작::

    from kdrug import KdrugClient

    client = KdrugClient.from_env()                  # KDRUG_API_KEY 환경변수
    result = client.get_drug_info(item_seq="199104100")
    if result.ok:
        info = result.info
        print(info.item_name, info.cost.max_price if info.cost else None)

인증키는 Decoding/Encoding 키 모두 지원한다(키에 '%' 가 있으면 Encoding 으로 자동
판별, 이중 인코딩 방지). ``DRUG_API_KEY_ENCODING`` / ``DRUG_API_KEY_DECODING``
환경변수도 인식한다.

공개 API:
  KdrugClient       — 메인 클라이언트
  DrugInfoResult    — get_drug_info 반환 타입
  DrugInfo / PillIdentity / DrugPermit / DrugProduct / DrugCost — 정규화 dataclass
  KdrugError 계층   — 예외
"""

from .client import KdrugClient, DrugInfoResult
from .exceptions import (
    KdrugError,
    KdrugAuthError,
    KdrugHTTPError,
    KdrugResponseError,
)
from .models import DrugInfo, DrugPermit, DrugProduct, DrugCost, PillIdentity
from .parsers import parse_grn, parse_permit, parse_product, parse_cost
from ._env import load_dotenv, create_env_file, find_dotenv

__version__ = "0.2.1"

__all__ = [
    "KdrugClient",
    "DrugInfoResult",
    "DrugInfo",
    "PillIdentity",
    "DrugPermit",
    "DrugProduct",
    "DrugCost",
    "KdrugError",
    "KdrugAuthError",
    "KdrugHTTPError",
    "KdrugResponseError",
    "parse_grn",
    "parse_permit",
    "parse_product",
    "parse_cost",
    "load_dotenv",
    "create_env_file",
    "find_dotenv",
    "__version__",
]
