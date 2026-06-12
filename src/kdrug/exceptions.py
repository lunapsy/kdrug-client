"""kdrug-client 예외 계층.

KdrugError
├── KdrugAuthError      — 인증키 누락/오류
├── KdrugHTTPError      — 네트워크/HTTP 실패 (status_code 보유)
└── KdrugResponseError  — 응답 파싱 실패 또는 공공API resultCode 오류 (result_code 보유)
"""

from __future__ import annotations


class KdrugError(RuntimeError):
    """모든 kdrug-client 예외의 베이스. `except KdrugError` 로 한 번에 잡을 수 있다."""


class KdrugAuthError(KdrugError):
    """인증키가 없거나 잘못됨."""


class KdrugHTTPError(KdrugError):
    """HTTP 요청 실패 (timeout, 네트워크 오류, 4xx/5xx)."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class KdrugResponseError(KdrugError):
    """응답 본문 파싱 실패 또는 공공데이터포털 resultCode 오류."""

    def __init__(self, message: str, *, result_code: str | None = None) -> None:
        super().__init__(message)
        self.result_code = result_code
