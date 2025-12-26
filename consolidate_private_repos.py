#!/usr/bin/env python3
"""
Private 저장소 통폐합 스크립트
online-course와 crypto를 제외한 private 저장소들을 통합합니다.
"""

import subprocess
import json
import logging
import os
from typing import List, Dict, Optional
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 제외할 저장소 목록
EXCLUDED_REPOS = ['online-course', 'crypto']

# 통합 대상 저장소 이름
CONSOLIDATED_REPO_NAME = 'private-projects'


def check_gh_cli() -> bool:
    """GitHub CLI가 설치되어 있는지 확인합니다."""
    try:
        result = subprocess.run(['gh', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_private_repositories(owner: str) -> List[Dict]:
    """Private 저장소 목록을 가져옵니다."""
    if not check_gh_cli():
        logger.error("GitHub CLI (gh)가 설치되어 있지 않습니다.")
        return []
    
    try:
        # Private 저장소만 필터링하여 가져오기
        cmd = f"gh repo list {owner} --limit 100 --json name,isPrivate,isArchived,description --jq '.[] | select(.isPrivate == true) | select(.isArchived == false)'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            # 각 줄이 JSON 객체이므로 파싱
            repos = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    try:
                        repo = json.loads(line)
                        # 제외 목록에 없는 저장소만 추가
                        if repo.get('name') not in EXCLUDED_REPOS:
                            repos.append(repo)
                    except json.JSONDecodeError:
                        continue
            return repos
        else:
            logger.error(f"저장소 목록 가져오기 실패: {result.stderr}")
            return []
    except Exception as e:
        logger.error(f"저장소 목록 가져오기 중 오류: {e}")
        return []


def create_consolidated_repo(owner: str, repo_name: str) -> bool:
    """통합 저장소를 생성합니다."""
    if not check_gh_cli():
        return False
    
    try:
        # 저장소가 이미 존재하는지 확인
        check_cmd = f"gh repo view {owner}/{repo_name} --json name 2>/dev/null"
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ {repo_name} 저장소가 이미 존재합니다.")
            return True
        
        # 새 저장소 생성 (Private)
        create_cmd = f"gh repo create {owner}/{repo_name} --private --description 'Consolidated private projects repository'"
        result = subprocess.run(create_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ {repo_name} 저장소 생성 완료")
            return True
        else:
            logger.error(f"❌ {repo_name} 저장소 생성 실패: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ 저장소 생성 중 오류: {e}")
        return False


def merge_repository_into_consolidated(owner: str, source_repo: str, target_repo: str, subdirectory: str) -> bool:
    """소스 저장소를 통합 저장소의 하위 디렉토리로 병합합니다."""
    try:
        # 임시 디렉토리 생성
        temp_dir = Path(f"/tmp/github-consolidate-{source_repo}")
        temp_dir.mkdir(exist_ok=True)
        
        # 통합 저장소 클론
        consolidated_path = temp_dir / target_repo
        if consolidated_path.exists():
            subprocess.run(['rm', '-rf', str(consolidated_path)], check=True)
        
        clone_cmd = f"git clone https://github.com/{owner}/{target_repo}.git {consolidated_path}"
        result = subprocess.run(clone_cmd, shell=True, capture_output=True, text=True, cwd=temp_dir)
        
        if result.returncode != 0:
            logger.error(f"❌ 통합 저장소 클론 실패: {result.stderr}")
            return False
        
        # 소스 저장소를 remote로 추가
        source_path = temp_dir / source_repo
        if source_path.exists():
            subprocess.run(['rm', '-rf', str(source_path)], check=True)
        
        clone_source_cmd = f"git clone https://github.com/{owner}/{source_repo}.git {source_path}"
        result = subprocess.run(clone_source_cmd, shell=True, capture_output=True, text=True, cwd=temp_dir)
        
        if result.returncode != 0:
            logger.error(f"❌ 소스 저장소 클론 실패: {result.stderr}")
            return False
        
        # 원래 작업 디렉토리 저장
        original_cwd = os.getcwd()
        
        # 통합 저장소로 이동
        os.chdir(consolidated_path)
        
        # 소스 저장소를 subtree로 추가
        # 먼저 README가 있으면 제거 (충돌 방지)
        readme_path = consolidated_path / "README.md"
        if readme_path.exists():
            subprocess.run(['git', 'rm', 'README.md'], cwd=consolidated_path, capture_output=True)
            subprocess.run(['git', 'commit', '-m', 'Remove default README before merge'], cwd=consolidated_path, capture_output=True)
        
        subtree_cmd = f"git subtree add --prefix={subdirectory} {source_path} main --squash"
        result = subprocess.run(subtree_cmd, shell=True, capture_output=True, text=True, cwd=consolidated_path)
        
        if result.returncode == 0:
            # 푸시
            push_cmd = "git push origin main"
            result = subprocess.run(push_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ {source_repo} → {target_repo}/{subdirectory} 통합 완료")
                return True
            else:
                logger.error(f"❌ 푸시 실패: {result.stderr}")
                return False
        else:
            logger.error(f"❌ Subtree 추가 실패: {result.stderr}")
            return False
        
    except Exception as e:
        logger.error(f"❌ 저장소 통합 중 오류: {e}")
        return False
    finally:
        # 원래 디렉토리로 복귀
        try:
            original_cwd = os.getcwd()
            if '/tmp/github-consolidate' in original_cwd:
                os.chdir('/Users/yong/Desktop/Blog')
        except:
            pass
        # 임시 디렉토리 정리
        try:
            subprocess.run(['rm', '-rf', str(temp_dir)], check=True)
        except:
            pass


def archive_after_consolidation(owner: str, repo_name: str) -> bool:
    """통합 후 원본 저장소를 Archive 처리합니다."""
    if not check_gh_cli():
        return False
    
    try:
        cmd = f"gh repo archive {owner}/{repo_name}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ {repo_name} Archive 처리 완료")
            return True
        else:
            logger.error(f"❌ {repo_name} Archive 처리 실패: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ Archive 처리 중 오류: {e}")
        return False


def generate_consolidation_plan(repos: List[Dict]) -> str:
    """통합 계획을 생성합니다."""
    plan = f"""# Private 저장소 통합 계획

> 생성일: {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}

## 📊 현재 상태

- **통합 대상 Private 저장소**: {len(repos)}개
- **제외된 저장소**: {', '.join(EXCLUDED_REPOS)}
- **통합 저장소 이름**: `{CONSOLIDATED_REPO_NAME}`

## 📁 통합 대상 저장소

"""
    
    for repo in repos:
        plan += f"- **{repo.get('name')}** - {repo.get('description', 'No description')}\n"
    
    plan += f"""
## 🎯 통합 계획

1. **통합 저장소 생성**: `{CONSOLIDATED_REPO_NAME}`
2. **각 저장소를 하위 디렉토리로 통합**:
"""
    
    for repo in repos:
        repo_name = repo.get('name')
        plan += f"   - `{repo_name}` → `{CONSOLIDATED_REPO_NAME}/{repo_name}/`\n"
    
    plan += f"""
3. **통합 완료 후 원본 저장소 Archive 처리**

## ⚠️ 주의사항

- 통합 전에 각 저장소의 중요한 변경사항이 있는지 확인
- 통합 시 Git 히스토리는 보존되지만 squash 병합 사용
- Archive 처리 전에 통합이 성공적으로 완료되었는지 확인

## 📝 실행 방법

### 자동 실행
```bash
python consolidate_private_repos.py --auto
```

### 수동 실행
```bash
# 1. 통합 저장소 생성
gh repo create Twodragon0/{CONSOLIDATED_REPO_NAME} --private

# 2. 각 저장소 통합 (예시)
git clone https://github.com/Twodragon0/{CONSOLIDATED_REPO_NAME}.git
cd {CONSOLIDATED_REPO_NAME}
git subtree add --prefix=repo1 https://github.com/Twodragon0/repo1.git main --squash
git push origin main

# 3. 원본 저장소 Archive
gh repo archive Twodragon0/repo1
```

"""
    
    return plan


def main():
    """메인 실행 함수"""
    owner = "Twodragon0"
    
    print("="*60)
    print("Private 저장소 통합 도구")
    print("="*60)
    print()
    
    # GitHub CLI 확인
    if not check_gh_cli():
        print("⚠️  GitHub CLI (gh)가 설치되어 있지 않습니다.")
        print("설치 방법:")
        print("  macOS: brew install gh")
        print("  또는: https://cli.github.com/")
        return
    
    print("✅ GitHub CLI가 설치되어 있습니다.")
    print()
    
    # Private 저장소 목록 가져오기
    print("📋 Private 저장소 목록 가져오는 중...")
    repos = get_private_repositories(owner)
    
    if not repos:
        print("❌ 통합할 Private 저장소를 찾을 수 없습니다.")
        print("또는 GitHub CLI 인증이 필요할 수 있습니다: gh auth login")
        return
    
    # 제외된 저장소 필터링
    repos = [r for r in repos if r.get('name') not in EXCLUDED_REPOS]
    
    if not repos:
        print(f"✅ 제외 목록({', '.join(EXCLUDED_REPOS)})을 제외하면 통합할 저장소가 없습니다.")
        return
    
    print(f"\n총 {len(repos)}개의 Private 저장소를 찾았습니다:")
    for repo in repos:
        print(f"  - {repo.get('name')}: {repo.get('description', 'No description')}")
    
    # 통합 계획 생성
    plan = generate_consolidation_plan(repos)
    
    with open("PRIVATE_REPO_CONSOLIDATION_PLAN.md", "w", encoding="utf-8") as f:
        f.write(plan)
    
    logger.info("통합 계획 생성 완료: PRIVATE_REPO_CONSOLIDATION_PLAN.md")
    
    print("\n" + "="*60)
    print("통합 작업을 시작하시겠습니까?")
    print("="*60)
    print()
    print("다음 작업이 수행됩니다:")
    print(f"1. {CONSOLIDATED_REPO_NAME} 저장소 생성")
    for repo in repos:
        print(f"2. {repo.get('name')} → {CONSOLIDATED_REPO_NAME}/{repo.get('name')}/ 통합")
    print("3. 통합 완료 후 원본 저장소 Archive 처리")
    print()
    print("⚠️  주의: 이 작업은 되돌릴 수 없습니다!")
    print()
    print("자동 실행을 원하시면 다음 명령어를 실행하세요:")
    print("  python consolidate_private_repos.py --auto")


def auto_consolidate():
    """자동 통합 실행"""
    owner = "Twodragon0"
    
    print("="*60)
    print("Private 저장소 자동 통합 시작")
    print("="*60)
    print()
    
    # Private 저장소 목록 가져오기
    repos = get_private_repositories(owner)
    repos = [r for r in repos if r.get('name') not in EXCLUDED_REPOS]
    
    if not repos:
        print("❌ 통합할 저장소가 없습니다.")
        return
    
    # 통합 저장소 생성
    print(f"📦 {CONSOLIDATED_REPO_NAME} 저장소 생성 중...")
    if not create_consolidated_repo(owner, CONSOLIDATED_REPO_NAME):
        print("❌ 통합 저장소 생성 실패")
        return
    
    # 각 저장소 통합
    success_count = 0
    failed_repos = []
    
    for repo in repos:
        repo_name = repo.get('name')
        print(f"\n🔄 {repo_name} 통합 중...")
        
        if merge_repository_into_consolidated(owner, repo_name, CONSOLIDATED_REPO_NAME, repo_name):
            success_count += 1
            # 통합 성공 후 Archive 처리
            print(f"📦 {repo_name} Archive 처리 중...")
            archive_after_consolidation(owner, repo_name)
        else:
            failed_repos.append(repo_name)
    
    # 결과 요약
    print("\n" + "="*60)
    print("통합 작업 완료")
    print("="*60)
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {len(failed_repos)}개")
    
    if failed_repos:
        print(f"\n실패한 저장소: {', '.join(failed_repos)}")
        print("수동으로 확인하세요.")


if __name__ == "__main__":
    import sys
    
    if "--auto" in sys.argv:
        auto_consolidate()
    else:
        main()

