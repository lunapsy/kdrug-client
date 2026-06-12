"""kdrug CLI — 터미널에서 바로 조회.

사용::

    export KDRUG_API_KEY="발급받은_Decoding_키"
    python -m kdrug --item-seq 199104100
    python -m kdrug --item-name 타이레놀 --json
    kdrug --item-seq 199104100            # 설치 후 콘솔 스크립트

옵션:
    --item-seq SEQ     품목기준코드로 조회 (권장)
    --item-name NAME   제품명으로 조회
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
        description="공공데이터포털 의약품 3종 API 통합 조회 (낱알식별·허가정보·약가기준)",
    )
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--item-seq", help="품목기준코드 (예: 199104100)")
    g.add_argument("--item-name", help="제품명 (예: 타이레놀정500밀리그람)")
    g.add_argument("--init", action="store_true",
                   help="현재 폴더에 .env 템플릿을 생성하고 종료")
    parser.add_argument("--api-key", help="인증키 (없으면 KDRUG_API_KEY 환경변수 사용)")
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
        result = client.get_drug_info(item_seq=args.item_seq, item_name=args.item_name)
    except KdrugError as e:
        print(f"조회 실패: {e}", file=sys.stderr)
        return 1

    if not result.ok:
        print("데이터를 찾지 못했습니다.", file=sys.stderr)
        if result.errors:
            for api, err in result.errors.items():
                print(f"  [{api}] {err}", file=sys.stderr)
        return 1

    merged = result.info.to_dict()

    if args.json:
        print(json.dumps(merged, ensure_ascii=False, indent=2, default=str))
    else:
        _print_human(result)
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


if __name__ == "__main__":
    raise SystemExit(main())
