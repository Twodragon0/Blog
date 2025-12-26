#!/bin/bash
# Private 저장소 통합 수동 스크립트
# working tree 문제 해결

set -e

OWNER="Twodragon0"
TARGET_REPO="private-projects"
TEMP_DIR="/tmp/github-consolidate-$$"

# Private 저장소 목록 (online-course, crypto 제외)
REPOS=("Occupational_Safety" "ISMS-P" "wordpress" "seniordragon")

echo "=== Private 저장소 통합 시작 ==="

# 임시 디렉토리 생성
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

# 통합 저장소 클론
echo "📦 통합 저장소 클론 중..."
git clone "https://github.com/${OWNER}/${TARGET_REPO}.git" "$TARGET_REPO"
cd "$TARGET_REPO"

# 각 저장소 통합
for repo in "${REPOS[@]}"; do
    echo ""
    echo "🔄 ${repo} 통합 중..."
    
    # 원격 저장소 추가
    git remote add "${repo}" "https://github.com/${OWNER}/${repo}.git" || true
    
    # Fetch
    git fetch "${repo}" main || git fetch "${repo}" master || continue
    
    # Branch 확인
    BRANCH="main"
    git ls-remote --heads "${repo}" main > /dev/null 2>&1 || BRANCH="master"
    
    # Subtree 추가
    if git subtree add --prefix="${repo}" "${repo}" "${BRANCH}" --squash; then
        echo "✅ ${repo} 통합 완료"
    else
        echo "❌ ${repo} 통합 실패"
    fi
    
    # 원격 제거
    git remote remove "${repo}" || true
done

# 푸시
echo ""
echo "📤 변경사항 푸시 중..."
git push origin main || git push origin master

echo ""
echo "✅ 통합 완료!"

# 정리
cd /Users/yong/Desktop/Blog
rm -rf "$TEMP_DIR"

