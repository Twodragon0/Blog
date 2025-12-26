#!/usr/bin/env python3
"""
GitHub 저장소 정리 및 통폐합 스크립트
Twodragon0의 GitHub 저장소들을 분석하고 정리 계획을 생성합니다.
"""

import json
import logging
from typing import List, Dict, Optional
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 현재 저장소 정보 (웹 검색 결과 기반)
REPOSITORIES = [
    {
        "name": "AWS",
        "description": "IAM policies for various use cases",
        "language": "Python",
        "type": "original",
        "category": "aws-security",
        "status": "active"
    },
    {
        "name": "esp32-openwrt",
        "description": "ESP32-MDF (ESP-Mesh) and OpenWrt Socket",
        "language": "Python",
        "type": "original",
        "category": "iot",
        "status": "active",
        "stars": 14,
        "forks": 2
    },
    {
        "name": "OpenWRT-IPFS",
        "description": "IPFS in Raspberry Pi based on OpenWrt/Untangle/pfsense",
        "language": "Shell",
        "type": "original",
        "category": "iot",
        "status": "active",
        "stars": 4,
        "forks": 1
    },
    {
        "name": "audit-points",
        "description": "Audit Points 공유를 위한 Repository",
        "language": "Python",
        "type": "forked",
        "original": "querypie/audit-points",
        "category": "security",
        "status": "archive"
    },
    {
        "name": "prowler",
        "description": "Prowler is an Open Source Security tool for AWS, Azure, GCP and Kubernetes",
        "language": "Python",
        "type": "forked",
        "original": "prowler-cloud/prowler",
        "category": "security",
        "status": "archive"
    },
    {
        "name": "DevSecOps",
        "description": "Collection and Roadmap for everyone who wants DevSecOps",
        "language": "Go",
        "type": "forked",
        "original": "hahwul/DevSecOps",
        "category": "security",
        "status": "archive"
    },
    {
        "name": "Blog",
        "description": "Blog RSS Feed Collector and README updater",
        "language": "Python",
        "type": "original",
        "category": "automation",
        "status": "active"
    }
]


def analyze_repositories() -> Dict:
    """저장소들을 분석하고 정리 계획을 생성합니다."""
    analysis = {
        "total": len(REPOSITORIES),
        "original": len([r for r in REPOSITORIES if r["type"] == "original"]),
        "forked": len([r for r in REPOSITORIES if r["type"] == "forked"]),
        "by_category": {},
        "by_language": {},
        "recommendations": []
    }
    
    # 카테고리별 분류
    for repo in REPOSITORIES:
        category = repo.get("category", "other")
        if category not in analysis["by_category"]:
            analysis["by_category"][category] = []
        analysis["by_category"][category].append(repo["name"])
    
    # 언어별 분류
    for repo in REPOSITORIES:
        language = repo.get("language", "other")
        if language not in analysis["by_language"]:
            analysis["by_language"][language] = []
        analysis["by_language"][language].append(repo["name"])
    
    # 정리 권장사항 생성
    recommendations = []
    
    # 1. 포크된 저장소는 Archive 처리 권장
    forked_repos = [r for r in REPOSITORIES if r["type"] == "forked"]
    if forked_repos:
        recommendations.append({
            "action": "archive",
            "repos": [r["name"] for r in forked_repos],
            "reason": "포크된 저장소는 원본 저장소를 참조하므로 Archive 처리 권장"
        })
    
    # 2. IoT 관련 저장소 통합 고려
    iot_repos = analysis["by_category"].get("iot", [])
    if len(iot_repos) >= 2:
        recommendations.append({
            "action": "consolidate",
            "repos": iot_repos,
            "reason": "IoT 관련 저장소들을 하나의 monorepo로 통합 고려",
            "suggested_name": "iot-projects"
        })
    
    # 3. AWS 관련 저장소 정리
    aws_repos = [r for r in REPOSITORIES if "aws" in r["category"].lower() or "aws" in r["name"].lower()]
    if aws_repos:
        recommendations.append({
            "action": "organize",
            "repos": [r["name"] for r in aws_repos],
            "reason": "AWS 관련 저장소들을 별도 조직 또는 태그로 정리"
        })
    
    analysis["recommendations"] = recommendations
    
    return analysis


def generate_organization_plan() -> str:
    """저장소 정리 계획을 마크다운 형식으로 생성합니다."""
    analysis = analyze_repositories()
    
    plan = f"""# GitHub 저장소 정리 계획

> 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S KST')}

## 📊 현재 상태

- **총 저장소 수**: {analysis['total']}개
- **원본 저장소**: {analysis['original']}개
- **포크된 저장소**: {analysis['forked']}개

## 📁 카테고리별 분류

"""
    
    for category, repos in analysis["by_category"].items():
        plan += f"### {category.upper()}\n"
        for repo_name in repos:
            repo = next((r for r in REPOSITORIES if r["name"] == repo_name), None)
            if repo:
                plan += f"- **{repo_name}** ({repo.get('language', 'N/A')}) - {repo.get('description', 'No description')}\n"
        plan += "\n"
    
    plan += """## 🎯 정리 권장사항

"""
    
    for idx, rec in enumerate(analysis["recommendations"], 1):
        plan += f"### {idx}. {rec['action'].upper()}: {', '.join(rec['repos'])}\n"
        plan += f"**이유**: {rec['reason']}\n"
        if 'suggested_name' in rec:
            plan += f"**제안 이름**: `{rec['suggested_name']}`\n"
        plan += "\n"
    
    plan += """## 📝 실행 계획

### 1단계: 포크된 저장소 Archive 처리
- `audit-points` - Archive 처리
- `prowler` - Archive 처리  
- `DevSecOps` - Archive 처리

### 2단계: IoT 프로젝트 통합 검토
- `esp32-openwrt`와 `OpenWRT-IPFS`를 하나의 저장소로 통합 고려
- 또는 별도 조직(Organization) 생성

### 3단계: AWS 관련 저장소 정리
- `AWS` 저장소를 더 명확한 이름으로 변경 고려 (예: `aws-iam-policies`)
- AWS 관련 프로젝트들을 태그로 분류

### 4단계: 프로필 README 업데이트
- 정리된 저장소 목록 반영
- Pinned repositories 업데이트

## ⚠️ 주의사항

- Archive 처리 전에 중요한 변경사항이 있는지 확인
- 통합 전에 각 저장소의 이슈와 PR 확인
- 통합 시 Git 히스토리 보존 방법 검토

"""
    
    return plan


def generate_archive_script() -> str:
    """저장소 Archive 처리를 위한 스크립트를 생성합니다."""
    script = """#!/bin/bash
# GitHub 저장소 Archive 처리 스크립트
# 사용법: gh repo archive <owner>/<repo-name>

# 포크된 저장소 Archive 처리
echo "Archiving forked repositories..."

# gh CLI가 설치되어 있어야 합니다
# gh repo archive Twodragon0/audit-points
# gh repo archive Twodragon0/prowler
# gh repo archive Twodragon0/DevSecOps

echo "Archive complete!"
"""
    return script


if __name__ == "__main__":
    # 분석 실행
    analysis = analyze_repositories()
    
    # 정리 계획 생성
    plan = generate_organization_plan()
    
    # 파일로 저장
    with open("REPO_ORGANIZATION_PLAN.md", "w", encoding="utf-8") as f:
        f.write(plan)
    
    logger.info("저장소 정리 계획 생성 완료: REPO_ORGANIZATION_PLAN.md")
    
    # Archive 스크립트 생성
    archive_script = generate_archive_script()
    with open("archive_repos.sh", "w", encoding="utf-8") as f:
        f.write(archive_script)
    
    logger.info("Archive 스크립트 생성 완료: archive_repos.sh")
    
    # JSON 형식으로도 저장
    with open("repo_analysis.json", "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    logger.info("저장소 분석 결과 저장 완료: repo_analysis.json")
    
    # 콘솔 출력
    print("\n" + "="*60)
    print("저장소 정리 계획")
    print("="*60)
    print(plan)

