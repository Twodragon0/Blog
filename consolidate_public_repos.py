#!/usr/bin/env python3
"""
Public 저장소 통폐합 스크립트
카테고리별로 Public 저장소들을 통합합니다.
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

# 카테고리별 저장소 분류
REPO_CATEGORIES = {
    "aws-tools": {
        "repos": ["Lambda", "security_standards"],
        "description": "AWS-related tools and security standards",
        "name": "aws-tools"
    },
    "docker-ipfs-projects": {
        "repos": [
            "docker-tools",
            "ipfs-kubernetes",
            "picam-ipfs",
            "ipfs-cluster",
            "OpenWRT-IPFS",
            "raspi-docker-stacks",
            "docker-jetson"
        ],
        "description": "Docker and IPFS infrastructure projects",
        "name": "docker-ipfs-projects"
    },
    "iot-projects": {
        "repos": ["esp32-openwrt"],
        "description": "IoT and embedded systems projects",
        "name": "iot-projects"
    },
    "infrastructure": {
        "repos": ["Okta", "server-storage"],
        "description": "Infrastructure and system administration tools",
        "name": "infrastructure-tools"
    }
}


def check_gh_cli() -> bool:
    """GitHub CLI가 설치되어 있는지 확인합니다."""
    try:
        result = subprocess.run(['gh', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def create_consolidated_repo(owner: str, repo_name: str, description: str) -> bool:
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
        
        # 새 저장소 생성 (Public)
        create_cmd = f"gh repo create {owner}/{repo_name} --public --description '{description}'"
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
        temp_dir = Path(f"/tmp/github-consolidate-public-{source_repo}")
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
        
        # 소스 저장소 클론
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
        
        # Git 상태 확인 및 정리
        status_result = subprocess.run(['git', 'status', '--porcelain'], cwd=consolidated_path, capture_output=True, text=True)
        if status_result.stdout.strip():
            subprocess.run(['git', 'add', '.'], cwd=consolidated_path, capture_output=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit or cleanup'], cwd=consolidated_path, capture_output=True)
        
        # 빈 저장소인 경우 초기 커밋 생성
        try:
            subprocess.run(['git', 'rev-parse', '--verify', 'HEAD'], cwd=consolidated_path, check=True, capture_output=True)
        except:
            # 빈 저장소
            readme_content = f"# {target_repo}\n\nConsolidated repository for related projects.\n"
            with open(consolidated_path / "README.md", "w") as f:
                f.write(readme_content)
            subprocess.run(['git', 'add', 'README.md'], cwd=consolidated_path, capture_output=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=consolidated_path, capture_output=True)
        
        # 브랜치 확인 (main 또는 master)
        branch_check = subprocess.run(['git', 'ls-remote', '--heads', source_path, 'main'], capture_output=True, text=True)
        branch = 'main' if branch_check.returncode == 0 else 'master'
        
        # 소스 저장소를 subtree로 추가
        subtree_cmd = f"git subtree add --prefix={subdirectory} {source_path} {branch} --squash"
        result = subprocess.run(subtree_cmd, shell=True, capture_output=True, text=True, cwd=consolidated_path)
        
        if result.returncode == 0:
            # 푸시
            push_cmd = "git push origin main || git push origin master"
            result = subprocess.run(push_cmd, shell=True, capture_output=True, text=True, cwd=consolidated_path)
            
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
            if '/tmp/github-consolidate-public' in os.getcwd():
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
        cmd = f"gh repo archive {owner}/{repo_name} --yes"
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


def consolidate_category(owner: str, category_name: str, category_info: Dict) -> bool:
    """카테고리별로 저장소를 통합합니다."""
    target_repo = category_info["name"]
    repos = category_info["repos"]
    description = category_info["description"]
    
    print(f"\n{'='*60}")
    print(f"카테고리: {category_name}")
    print(f"통합 저장소: {target_repo}")
    print(f"대상 저장소: {', '.join(repos)}")
    print(f"{'='*60}\n")
    
    # 통합 저장소 생성
    if not create_consolidated_repo(owner, target_repo, description):
        return False
    
    # 각 저장소 통합
    success_count = 0
    for repo in repos:
        print(f"🔄 {repo} 통합 중...")
        
        if merge_repository_into_consolidated(owner, repo, target_repo, repo):
            success_count += 1
            # 통합 성공 후 Archive 처리
            print(f"📦 {repo} Archive 처리 중...")
            archive_after_consolidation(owner, repo)
        else:
            print(f"❌ {repo} 통합 실패")
    
    print(f"\n✅ {category_name} 통합 완료: {success_count}/{len(repos)} 성공\n")
    return success_count == len(repos)


def main():
    """메인 실행 함수"""
    owner = "Twodragon0"
    
    print("="*60)
    print("Public 저장소 통합 도구")
    print("="*60)
    print()
    
    # GitHub CLI 확인
    if not check_gh_cli():
        print("⚠️  GitHub CLI (gh)가 설치되어 있지 않습니다.")
        return
    
    print("✅ GitHub CLI가 설치되어 있습니다.")
    print()
    
    # 각 카테고리별로 통합
    for category_name, category_info in REPO_CATEGORIES.items():
        consolidate_category(owner, category_name, category_info)
    
    print("="*60)
    print("모든 Public 저장소 통합 작업 완료")
    print("="*60)


if __name__ == "__main__":
    main()

