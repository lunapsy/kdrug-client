"""의존성 없는 최소 .env 로더/생성기.

python-dotenv 를 설치하지 않고도 `.env` 파일을 자동으로 읽어 os.environ 에
채워준다. 이미 설정된 환경변수는 덮어쓰지 않는다 (실제 환경변수가 항상 우선).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

_TEMPLATE = """\
# 공공데이터포털에서 발급받은 인증키 (Decoding/Encoding 모두 지원).
# 키에 '%' 가 있으면 Encoding 키로 자동 판별합니다.
KDRUG_API_KEY=

# 또는 인코딩/디코딩을 분리 (rxstock/Edge Function 시크릿과 동일 이름).
# DRUG_API_KEY_ENCODING=
# DRUG_API_KEY_DECODING=

# (선택) 식약처가 엔드포인트 버전을 바꿨을 때만 사용
# KDRUG_GRN_ENDPOINT=
# KDRUG_PERMIT_ENDPOINT=
# KDRUG_PRICE_ENDPOINT=
"""


def find_dotenv(start: Optional[Path] = None) -> Optional[Path]:
    """현재 디렉터리부터 위로 올라가며 첫 ``.env`` 파일을 찾는다."""
    start = (start or Path.cwd()).resolve()
    for directory in (start, *start.parents):
        candidate = directory / ".env"
        if candidate.is_file():
            return candidate
    return None


def load_dotenv(path: Optional[Path] = None, *, override: bool = False) -> bool:
    """``.env`` 파일을 읽어 os.environ 에 채운다.

    Args:
        path: 명시 경로. None 이면 cwd 부터 상위로 탐색.
        override: True 면 기존 환경변수도 덮어쓴다 (기본 False).

    Returns:
        파일을 찾아 한 줄이라도 읽었으면 True.
    """
    target = path or find_dotenv()
    if not target or not Path(target).is_file():
        return False

    loaded = False
    for raw in Path(target).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            continue
        if override or key not in os.environ:
            os.environ[key] = value
        loaded = True
    return loaded


def create_env_file(path: Optional[Path] = None, *, force: bool = False) -> Path:
    """``.env`` 템플릿 파일을 생성한다.

    Args:
        path: 생성 경로 (기본 ``./.env``).
        force: 이미 있으면 덮어쓸지 여부.

    Returns:
        생성/기존 파일 경로.

    Raises:
        FileExistsError: 파일이 있고 force=False 인 경우.
    """
    target = Path(path) if path else Path.cwd() / ".env"
    if target.exists() and not force:
        raise FileExistsError(f"{target} 가 이미 존재합니다. 덮어쓰려면 force=True.")
    target.write_text(_TEMPLATE, encoding="utf-8")
    return target


__all__ = ["load_dotenv", "find_dotenv", "create_env_file"]
