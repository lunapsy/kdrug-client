"""kdrug CLI — 터미널에서 바로 조회.

사용::

    export KDRUG_API_KEY="발급받은_Decoding_키"
    python -m kdrug --item-seq 202106092
    python -m kdrug --item-name 타이레놀 --json
    kdrug --item-seq 202106092            # 설치 후 콘솔 스크립트

옵션:
    --item-seq SEQ     품목기준코드로 조회 (권장)
    --item-name NAME   제품명으로 조회
    --market           유통 상태(생산·수입실적 + 공급중단)도 함께 조회
    --json             원본 병합 dict 를 JSON 으로 출력
    --api-key KEY      환경변수 대신 직접 키 지정
"""

from __future__ import annotations

import argparse
import json
import sys

from .client import KdrugClient
from .exceptions import KdrugAuthError, KdrugError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="kdrug",
        description="공공데이터포털 의약품 6종 API 통합 조회 (낱알식별·e약은요·제품허가·약가·공급중단·생산수입실적)",
    )
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--item-seq", help="품목기준코드 (예: 202106092)")
    g.add_argument("--item-name", help="제품명 (예: 타이레놀정500밀리그람)")
    g.add_argument("--init", action="store_true",
                   help="현재 폴더에 .env 템플릿을 생성하고 종료")
    parser.add_argument("--api-key", help="인증키 (없으면 KDRUG_API_KEY 환경변수 사용)")
    parser.add_argument("--market", action="store_true",
                        help="유통 상태(생산·수입실적 + 공급중단 보고)도 함께 조회")
    parser.add_argument("--json", action="store_true", help="병합 dict 를 JSON 으로 출력")
    args = parser.parse_args(argv)

    if args.init:
        return _do_init()

    try:
        client = KdrugClient(api_key=args.api_key) if args.api_key else KdrugClient.from_env()
    except KdrugAuthError as e:
        print(f"인증 오류: {e}", file=sys.stderr)
        print("→ 공공데이터포털에서 발급한 Decoding 키를 KDRUG_API_KEY 에 설정하세요.",
              file=sys.stderr)
        return 2

    try:
        result = client.get_drug_info(item_seq=args.item_seq, item_name=args.item_name,
                                      with_market=args.market)
    except KdrugError as e:
        print(f"조회 실패: {e}", file=sys.stderr)
        return 1

    if not result.ok:
        print("데이터를 찾지 못했습니다.", file=sys.stderr)
        if result.errors:
            for api, err in result.errors.items():
                print(f"  [{api}] {err}", file=sys.stderr)
        return 1

    merged = result.info.to_dict()   # --market 이면 유통 상태 필드도 평탄화돼 있음

    if args.json:
        print(json.dumps(merged, ensure_ascii=False, indent=2, default=str))
    else:
        _print_human(result)
        if result.info.market is not None:
            _print_market(result.info.market)
    return 0


def _do_init() -> int:
    """현재 폴더에 .env 템플릿 생성."""
    from ._env import create_env_file
    try:
        path = create_env_file()
    except FileExistsError as e:
        print(f"건너뜀: {e}", file=sys.stderr)
        return 1
    print(f"생성됨: {path}")
    print("→ 파일을 열어 KDRUG_API_KEY= 뒤에 발급받은 Decoding 키를 채우세요.")
    print("  (.env 는 .gitignore 로 보호되어 git 에 올라가지 않습니다.)")
    return 0


def _print_human(result) -> None:
    info = result.info
    print(f"■ {info.item_name}  ({info.item_seq})")
    print(f"  제조/수입: {info.entp_name}")
    print(f"  데이터 출처: {', '.join(info.sources) or '-'}")
    if info.identity:
        i = info.identity
        dims = " × ".join(str(x) for x in (i.length_long, i.length_short, i.thickness)
                          if x is not None)
        print("  [낱알식별]")
        print(f"    제형/모양: {i.form_code_name} / {i.drug_shape}")
        print(f"    치수(mm): {dims or '-'}")
        print(f"    색상: {i.color_class1} {i.color_class2}".rstrip())
        print(f"    식별표시: 앞 '{i.print_front}' / 뒤 '{i.print_back}'")
    if info.permit:
        p = info.permit
        print("  [e약은요 — 환자용 복약정보]")
        if p.efficacy:
            print(f"    효능: {p.efficacy[:60]}{'…' if len(p.efficacy) > 60 else ''}")
        if p.use_method:
            print(f"    사용법: {p.use_method[:60]}{'…' if len(p.use_method) > 60 else ''}")
        if p.storage:
            print(f"    보관법: {p.storage[:60]}{'…' if len(p.storage) > 60 else ''}")
    if info.product:
        pr = info.product
        print("  [제품허가 상세]")
        print(f"    주성분: {pr.main_ingredient or '-'}")
        print(f"    저장방법: {pr.storage_method or '-'}")
        print(f"    ATC: {pr.atc_code or '-'}  허가일: {pr.item_permit_date or '-'}  보험코드: {pr.edi_code or '-'}")
    if info.cost:
        c = info.cost
        print("  [약가 (심평원)]")
        price = f"{c.max_price}원" if c.max_price is not None else "-"
        print(f"    상한가: {price}  급여: {c.pay_type or '-'}  {c.spc_gnl_type or ''}".rstrip())
        print(f"    적용시작: {c.apply_start_date or '-'}  주성분코드: {c.gnl_name_code or '-'}")
    if result.errors:
        print("  ⚠ 일부 API 오류:")
        for api, err in result.errors.items():
            print(f"    [{api}] {err}")


def _print_market(s) -> None:
    print("  [유통 상태 — 생산·수입실적 + 공급중단]")
    mark = "✅ 유통 중" if s.is_marketed else "⛔ 유통 확인 안 됨"
    print(f"    {mark}  (실적: {'있음' if s.has_record else '없음'} / "
          f"중단보고: {'있음' if s.is_suspended else '없음'})")
    if s.has_record:
        unit = "백만원" if s.part == "생산" else "달러"
        print(f"    최근 실적: {s.latest_year} {s.part} {s.latest_amount} {unit}")
    for r in s.suspend_reports:
        if r.is_suspended:
            reason = (r.suspend_reason or "-")[:50]
            print(f"    중단보고: {r.suspend_date} ({r.report_flag}) — {reason}")


if __name__ == "__main__":
    raise SystemExit(main())
