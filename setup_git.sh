#!/usr/bin/env bash
# kdrug-client 를 깨끗한 git 저장소로 만들고 GitHub 에 올리는 스크립트.
# 본인 Mac 의 Terminal 에서 한 번만 실행하세요.
#
#   cd "/Users/lunap/Documents/Claude/Projects/kdrug-client"
#   bash setup_git.sh
#
# GitHub CLI(gh)가 있으면 저장소 생성+푸시까지 자동, 없으면 로컬 커밋까지만 하고
# 푸시 방법을 안내합니다.

set -euo pipefail

REPO_NAME="kdrug-client"
GH_USER="lunapsy"
REMOTE_URL="https://github.com/${GH_USER}/${REPO_NAME}.git"

cd "$(dirname "$0")"

echo "▶ 임시/캐시 파일 정리"
rm -rf .git .pytest_cache pytest-cache-files-* *.egg-info src/*.egg-info \
       _probe_overwrite \
       src/kdrug/__pycache__ tests/__pycache__ 2>/dev/null || true

echo "▶ git 저장소 초기화"
git init -q
git branch -M main
git add -A
git commit -q -m "feat: 공공데이터포털 의약품 4종 API 통합 클라이언트 kdrug-client v0.2.0

낱알식별·e약은요·제품허가(식약처)·약가(심평원)를 통합 조회하는 의존성 없는 파이썬
클라이언트. rxmcp 의 Django 모듈 dispenser/kdrug 에서 출발해 재구성 후 4종으로 확장.

- KdrugClient.get_drug_info(): 4종 동시 호출 + DrugInfo 병합 (부분 실패 허용)
  · 식약처 3종=ITEM_SEQ, 약가=제품허가 보험코드(EDI=mds_cd) 정확 조인
- from_env(): KDRUG_API_KEY / DRUG_API_KEY_ENCODING·DECODING / .env 자동 로드
- Decoding·Encoding 키 자동판별, 'kdrug --init' .env 생성
- 라이브 검증으로 엔드포인트/필드/파라미터 현행화:
  · 낱알식별 Service03(소문자 item_seq), 제품허가 Service07/DtlInq06
  · e약은요 공식명세(IROS_239) 환자용 복약정보, 약가 getDgamtList(상한가)
- dataclass(identity/permit/product/cost) 반환, CLI, 실데이터 픽스처 테스트 31개
- 외부 의존성 0 (표준 urllib 만 사용)"

echo "✓ 로컬 커밋 완료"
git --no-pager log --oneline -1

echo "▶ 원격 연결"
git remote add origin "$REMOTE_URL" 2>/dev/null || git remote set-url origin "$REMOTE_URL"

# 주의: GitHub 의 main 에는 이미 .env 기능이 빠진 초기 버전이 올라가 있고,
# setup_git.sh 는 새 루트 커밋을 만들어 히스토리가 다르므로 일반 push 는 거부된다.
# 저장소가 새 것이고 단독 사용이라 완성본으로 교체하는 --force 가 안전하다.
if command -v gh >/dev/null 2>&1; then
  echo "▶ gh CLI 로 GitHub 저장소 확인 + 푸시(완성본으로 교체)"
  if gh repo view "${GH_USER}/${REPO_NAME}" >/dev/null 2>&1; then
    echo "  (저장소가 이미 있어 완성본으로 강제 푸시)"
    git push -u origin main --force
  else
    gh repo create "${REPO_NAME}" --public --source=. --remote=origin --push
  fi
  echo "✓ 완료:  ${REMOTE_URL%.git}"
else
  echo "ℹ gh CLI 가 없습니다. 아래로 완성본을 올리세요:"
  echo "     git push -u origin main --force"
  echo "   (저장소가 아직 없다면 GitHub 웹에서 빈 저장소 '${REPO_NAME}' 먼저 생성)"
fi
