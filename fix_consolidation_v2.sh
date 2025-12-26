#!/bin/bash
# Private 저장소 통합 수정 스크립트
# 빈 저장소 문제 해결

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

# 빈 저장소인 경우 초기 커밋 생성
if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
    echo "📝 초기 커밋 생성 중..."
    echo "# Private Projects" > README.md
    git add README.md
    git commit -m "Initial commit: Consolidated private projects"
    git push origin main || git push origin master
fi

# 각 저장소 통합
for repo in "${REPOS[@]}"; do
    echo ""
    echo "🔄 ${repo} 통합 중..."
    
    # 원격 저장소 추가
    git remote add "${repo}" "https://github.com/${OWNER}/${repo}.git" 2>/dev/null || true
    
    # Fetch
    if ! git fetch "${repo}" main 2>/dev/null; then
        if ! git fetch "${repo}" master 2>/dev/null; then
            echo "⚠️  ${repo} 브랜치를 찾을 수 없습니다. 건너뜁니다."
            git remote remove "${repo}" 2>/dev/null || true
            continue
        fi
        BRANCH="master"
    else
        BRANCH="main"
    fi
    
    # Subtree 추가
    if git subtree add --prefix="${repo}" "${repo}" "${BRANCH}" --squash; then
        echo "✅ ${repo} 통합 완료"
        # 푸시
        git push origin main || git push origin master
    else
        echo "❌ ${repo} 통합 실패"
    fi
    
    # 원격 제거
    git remote remove "${repo}" 2>/dev/null || true
done

echo ""
echo "✅ 통합 완료!"

# 정리
cd /Users/yong/Desktop/Blog
rm -rf "$TEMP_DIR"

