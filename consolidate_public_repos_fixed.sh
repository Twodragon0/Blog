#!/bin/zsh
# Public 저장소 통합 수정 스크립트
# 브랜치 문제 해결

set -e

OWNER="Twodragon0"

# 카테고리별 저장소 정의
typeset -A CATEGORIES
CATEGORIES[aws-tools]="Lambda security_standards"
CATEGORIES[docker-ipfs-projects]="docker-tools ipfs-kubernetes picam-ipfs ipfs-cluster OpenWRT-IPFS raspi-docker-stacks docker-jetson"
CATEGORIES[iot-projects]="esp32-openwrt"
CATEGORIES[infrastructure-tools]="Okta server-storage"

echo "=== Public 저장소 통합 시작 ==="

for target_repo in "${(@k)CATEGORIES}"; do
    repos=(${(s: :)CATEGORIES[$target_repo]})
    
    echo ""
    echo "============================================================"
    echo "카테고리: $target_repo"
    echo "통합 저장소: $target_repo"
    echo "대상 저장소: ${repos[*]}"
    echo "============================================================"
    echo ""
    
    # 임시 디렉토리 생성
    TEMP_DIR="/tmp/github-consolidate-public-$$"
    mkdir -p "$TEMP_DIR"
    cd "$TEMP_DIR"
    
    # 통합 저장소 클론 또는 생성
    if gh repo view "${OWNER}/${target_repo}" >/dev/null 2>&1; then
        echo "📦 통합 저장소 클론 중..."
        git clone "https://github.com/${OWNER}/${target_repo}.git" "$target_repo"
        cd "$target_repo"
    else
        echo "📦 통합 저장소 생성 중..."
        gh repo create "${OWNER}/${target_repo}" --public --description "Consolidated ${target_repo}"
        git clone "https://github.com/${OWNER}/${target_repo}.git" "$target_repo"
        cd "$target_repo"
    fi
    
    # 빈 저장소인 경우 초기 커밋 생성
    if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
        echo "📝 초기 커밋 생성 중..."
        echo "# ${target_repo}" > README.md
        echo "" >> README.md
        echo "Consolidated repository for related projects." >> README.md
        git add README.md
        git commit -m "Initial commit: Consolidated ${target_repo}"
        git push origin main || git push origin master
    fi
    
    # 각 저장소 통합
    for repo in "${repos[@]}"; do
        echo ""
        echo "🔄 ${repo} 통합 중..."
        
        # 이미 통합되었는지 확인
        if [ -d "$repo" ]; then
            echo "⚠️  ${repo}는 이미 통합되어 있습니다. 건너뜁니다."
            continue
        fi
        
        # 기본 브랜치 확인
        BRANCH=$(gh repo view "${OWNER}/${repo}" --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo "master")
        
        if [ -z "$BRANCH" ] || [ "$BRANCH" = "null" ]; then
            BRANCH="master"
        fi
        
        echo "   브랜치: $BRANCH"
        
        # 원격 저장소 추가
        git remote add "${repo}" "https://github.com/${OWNER}/${repo}.git" 2>/dev/null || true
        
        # Fetch
        if git fetch "${repo}" "${BRANCH}" 2>/dev/null; then
            # Subtree 추가
            if git subtree add --prefix="${repo}" "${repo}" "${BRANCH}" --squash; then
                echo "✅ ${repo} 통합 완료"
                
                # 푸시
                git push origin main || git push origin master
                
                # Archive 처리
                echo "📦 ${repo} Archive 처리 중..."
                gh repo archive "${OWNER}/${repo}" --yes 2>/dev/null || true
            else
                echo "❌ ${repo} Subtree 추가 실패"
            fi
        else
            echo "❌ ${repo} Fetch 실패"
        fi
        
        # 원격 제거
        git remote remove "${repo}" 2>/dev/null || true
    done
    
    # 정리
    cd /Users/yong/Desktop/Blog
    rm -rf "$TEMP_DIR"
    
    echo ""
    echo "✅ ${target_repo} 통합 완료"
done

echo ""
echo "============================================================"
echo "모든 Public 저장소 통합 작업 완료"
echo "============================================================"

