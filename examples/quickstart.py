"""kdrug-client 빠른 시작 예제.

실행 전:
    export KDRUG_API_KEY="공공데이터포털에서_발급받은_Decoding_키"
    python examples/quickstart.py
"""

from kdrug import KdrugClient, KdrugError


def main() -> None:
    # 1) 환경변수(KDRUG_API_KEY)로 클라이언트 생성
    client = KdrugClient.from_env()
    # 또는 직접: client = KdrugClient(api_key="...")

    item_seq = "199104100"  # 예시 품목기준코드

    # 2) 3종 API를 한 번에 — 일부 실패해도 받은 데이터만 병합
    result = client.get_drug_info(item_seq=item_seq)

    if not result.ok:
        print("데이터 없음:", result.errors)
        return

    info = result.info
    print("제품명 :", info.item_name)
    print("출처   :", info.sources)              # ['grn', 'permit', 'price']

    if info.identity:
        print("치수   :", info.identity.length_long, info.identity.length_short)
        print("색상   :", info.identity.color_class1)
    if info.permit:                       # e약은요 — 환자용 복약정보
        print("효능   :", info.permit.efficacy[:40])
        print("사용법 :", info.permit.use_method[:40])
    if info.product:                      # 제품허가 상세
        print("주성분 :", info.product.main_ingredient)
        print("ATC    :", info.product.atc_code)
    if info.cost:                         # 약가 (심평원)
        print("상한가 :", info.cost.max_price, "원  급여:", info.cost.pay_type)

    # 3) 평탄화된 단일 dict 로도 쓸 수 있음 (DB 저장/JSON 직렬화에 편리)
    print("\n병합 dict:")
    for k, v in info.to_dict().items():
        print(f"  {k}: {v}")

    # 4) 개별 API 만 호출하고 싶을 때
    pills = client.fetch_grn(item_name="타이레놀", rows=5)
    print(f"\n'타이레놀' 낱알식별 결과 {len(pills)} 건")


if __name__ == "__main__":
    try:
        main()
    except KdrugError as e:
        print("오류:", e)
