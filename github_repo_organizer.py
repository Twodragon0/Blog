#!/usr/bin/env python3
"""
GitHub 저장소 정리 및 통폐합 스크립트
GitHub API를 사용하여 저장소를 정리합니다.
"""

import os
import sys
import json
import logging
import subprocess
from typing import List, Dict, Optional

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# GitHub CLI 명령어로 저장소 정리
GITHUB_CLI_COMMANDS = {
    "archive": "gh repo archive {owner}/{repo}",
    "rename": "gh repo rename {owner}/{old_name} {new_name}",
    "transfer": "gh repo transfer {owner}/{repo} {new_owner}",
    "list": "gh repo list {owner} --limit 100 --json name,isArchived,isFork,description"
}


def check_gh_cli() -> bool:
    """GitHub CLI가 설치되어 있는지 확인합니다."""
    try:
        result = subprocess.run(['gh', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def archive_repository(owner: str, repo_name: str) -> bool:
    """저장소를 Archive 처리합니다."""
    if not check_gh_cli():
        logger.error("GitHub CLI (gh)가 설치되어 있지 않습니다.")
        logger.info("설치 방법: brew install gh 또는 https://cli.github.com/")
        return False
    
    try:
        cmd = GITHUB_CLI_COMMANDS["archive"].format(owner=owner, repo=repo_name)
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ {repo_name} 저장소 Archive 처리 완료")
            return True
        else:
            logger.error(f"❌ {repo_name} Archive 처리 실패: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ {repo_name} Archive 처리 중 오류: {e}")
        return False


def rename_repository(owner: str, old_name: str, new_name: str) -> bool:
    """저장소 이름을 변경합니다."""
    if not check_gh_cli():
        logger.error("GitHub CLI (gh)가 설치되어 있지 않습니다.")
        return False
    
    try:
        cmd = GITHUB_CLI_COMMANDS["rename"].format(owner=owner, old_name=old_name, new_name=new_name)
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ {old_name} → {new_name} 이름 변경 완료")
            return True
        else:
            logger.error(f"❌ {old_name} 이름 변경 실패: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ {old_name} 이름 변경 중 오류: {e}")
        return False


def list_repositories(owner: str) -> List[Dict]:
    """저장소 목록을 가져옵니다."""
    if not check_gh_cli():
        logger.warning("GitHub CLI가 없어 기본 저장소 목록을 사용합니다.")
        return []
    
    try:
        cmd = GITHUB_CLI_COMMANDS["list"].format(owner=owner)
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            repos = json.loads(result.stdout)
            return repos
        else:
            logger.error(f"저장소 목록 가져오기 실패: {result.stderr}")
            return []
    except Exception as e:
        logger.error(f"저장소 목록 가져오기 중 오류: {e}")
        return []


def generate_consolidation_guide() -> str:
    """저장소 통합 가이드를 생성합니다."""
    guide = """# GitHub 저장소 통합 가이드

## IoT 프로젝트 통합 방법

### 방법 1: Git Subtree를 사용한 통합

```bash
# 1. 새 저장소 생성
git init iot-projects
cd iot-projects

# 2. esp32-openwrt를 subtree로 추가
git subtree add --prefix=esp32-openwrt https://github.com/Twodragon0/esp32-openwrt.git main --squash

# 3. OpenWRT-IPFS를 subtree로 추가
git subtree add --prefix=openwrt-ipfs https://github.com/Twodragon0/OpenWRT-IPFS.git main --squash

# 4. GitHub에 푸시
git remote add origin https://github.com/Twodragon0/iot-projects.git
git push -u origin main
```

### 방법 2: Git Submodule을 사용한 통합

```bash
# 1. 새 저장소 생성
git init iot-projects
cd iot-projects

# 2. 기존 저장소를 submodule로 추가
git submodule add https://github.com/Twodragon0/esp32-openwrt.git esp32-openwrt
git submodule add https://github.com/Twodragon0/OpenWRT-IPFS.git openwrt-ipfs

# 3. GitHub에 푸시
git remote add origin https://github.com/Twodragon0/iot-projects.git
git push -u origin main
```

### 방법 3: 단순 병합 (히스토리 보존)

```bash
# 1. 새 저장소 생성
git init iot-projects
cd iot-projects

# 2. esp32-openwrt 병합
git remote add esp32 https://github.com/Twodragon0/esp32-openwrt.git
git fetch esp32
git merge --allow-unrelated-histories esp32/main
mkdir -p esp32-openwrt
git mv * esp32-openwrt/ 2>/dev/null || true
git mv esp32-openwrt/* esp32-openwrt/ 2>/dev/null || true
git commit -m "Merge esp32-openwrt into iot-projects"

# 3. OpenWRT-IPFS 병합
git remote add ipfs https://github.com/Twodragon0/OpenWRT-IPFS.git
git fetch ipfs
git merge --allow-unrelated-histories ipfs/main
mkdir -p openwrt-ipfs
git mv * openwrt-ipfs/ 2>/dev/null || true
git mv openwrt-ipfs/* openwrt-ipfs/ 2>/dev/null || true
git commit -m "Merge OpenWRT-IPFS into iot-projects"

# 4. GitHub에 푸시
git remote set-url origin https://github.com/Twodragon0/iot-projects.git
git push -u origin main
```

## 저장소 Archive 처리

```bash
# GitHub CLI 사용
gh repo archive Twodragon0/audit-points
gh repo archive Twodragon0/prowler
gh repo archive Twodragon0/DevSecOps

# 또는 웹 인터페이스에서
# Settings → Danger Zone → Archive this repository
```

## 저장소 이름 변경

```bash
# AWS 저장소 이름 변경
gh repo rename Twodragon0/AWS aws-iam-policies
```

"""
    return guide


def main():
    """메인 실행 함수"""
    owner = "Twodragon0"
    
    print("="*60)
    print("GitHub 저장소 정리 도구")
    print("="*60)
    print()
    
    # GitHub CLI 확인
    if not check_gh_cli():
        print("⚠️  GitHub CLI (gh)가 설치되어 있지 않습니다.")
        print("설치 방법:")
        print("  macOS: brew install gh")
        print("  또는: https://cli.github.com/")
        print()
        print("GitHub CLI 없이도 수동으로 정리할 수 있습니다.")
        print("자세한 내용은 REPO_ORGANIZATION_PLAN.md를 참고하세요.")
        return
    
    print("✅ GitHub CLI가 설치되어 있습니다.")
    print()
    
    # 저장소 목록 가져오기
    print("📋 저장소 목록 가져오는 중...")
    repos = list_repositories(owner)
    
    if repos:
        print(f"\n총 {len(repos)}개의 저장소를 찾았습니다:")
        for repo in repos:
            status = "📦 Archived" if repo.get('isArchived') else "✅ Active"
            fork_status = "🔀 Forked" if repo.get('isFork') else "⭐ Original"
            print(f"  {status} {fork_status} {repo.get('name')}")
    
    print("\n" + "="*60)
    print("정리 작업을 시작하시겠습니까?")
    print("="*60)
    print()
    print("다음 작업이 수행됩니다:")
    print("1. 포크된 저장소 Archive 처리 (audit-points, prowler, DevSecOps)")
    print("2. 저장소 이름 변경 (AWS → aws-iam-policies)")
    print()
    print("⚠️  주의: 이 작업은 되돌릴 수 없습니다!")
    print()
    
    # 통합 가이드 생성
    guide = generate_consolidation_guide()
    with open("REPO_CONSOLIDATION_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(guide)
    
    logger.info("저장소 통합 가이드 생성 완료: REPO_CONSOLIDATION_GUIDE.md")
    
    print("📝 저장소 통합 가이드가 생성되었습니다: REPO_CONSOLIDATION_GUIDE.md")
    print()
    print("자동 실행을 원하시면 다음 명령어를 실행하세요:")
    print("  python github_repo_organizer.py --auto")
    print()
    print("또는 수동으로 다음 명령어를 실행하세요:")
    print("  gh repo archive Twodragon0/audit-points")
    print("  gh repo archive Twodragon0/prowler")
    print("  gh repo archive Twodragon0/DevSecOps")
    print("  gh repo rename Twodragon0/AWS aws-iam-policies")


if __name__ == "__main__":
    if "--auto" in sys.argv:
        # 자동 실행 모드
        owner = "Twodragon0"
        
        # 포크된 저장소 Archive 처리
        forked_repos = ["audit-points", "prowler", "DevSecOps"]
        for repo in forked_repos:
            archive_repository(owner, repo)
        
        # 저장소 이름 변경
        rename_repository(owner, "AWS", "aws-iam-policies")
    else:
        main()

