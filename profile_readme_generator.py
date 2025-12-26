#!/usr/bin/env python3
"""
GitHub Profile README 생성 스크립트
Twodragon0 프로필 페이지용 README.md를 생성합니다.
"""

import feedparser
import datetime
import logging
import html
from typing import List, Dict

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 허용된 블로그 도메인
ALLOWED_DOMAINS = ['twodragon.tistory.com', '2twodragon.com']
MAX_POSTS = 5  # 프로필 페이지에는 최근 5개만 표시


def fetch_recent_posts() -> List[Dict[str, str]]:
    """최근 블로그 포스트를 가져옵니다."""
    posts = []
    blog_urls = [
        "https://twodragon.tistory.com",
        "https://2twodragon.com"
    ]
    
    for blog_url in blog_urls:
        try:
            rss_url = f"{blog_url}/rss"
            feed = feedparser.parse(rss_url)
            
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"RSS 피드 파싱 오류: {feed.bozo_exception}")
                continue
            
            for entry in feed.get('entries', [])[:MAX_POSTS]:
                if 'link' in entry and 'title' in entry:
                    posts.append({
                        'title': html.escape(entry['title']),
                        'link': entry['link'],
                        'published': entry.get('published', '')
                    })
        except Exception as e:
            logger.error(f"블로그 포스트 수집 중 오류: {e}")
    
    # 날짜순 정렬 (최신순)
    def get_sort_key(post):
        try:
            if post.get('published'):
                return datetime.datetime.strptime(
                    post['published'], 
                    "%a, %d %b %Y %H:%M:%S %z"
                )
        except (ValueError, KeyError):
            pass
        return datetime.datetime.min
    
    posts.sort(key=get_sort_key, reverse=True)
    return posts[:MAX_POSTS]


def generate_profile_readme() -> str:
    """GitHub 프로필 README 내용을 생성합니다."""
    posts = fetch_recent_posts()
    
    readme = """# Hi there, I'm Twodragon 👋

> A curious researcher on future development through IT | DevSecOps Engineer | Cloud Security Specialist

<div align="center">
  <a href="https://github.com/Twodragon0">
    <img src="https://readme-typing-svg.herokuapp.com?font=Roboto&size=30&duration=4000&color=FF5722&center=true&vCenter=true&width=600&lines=DevSecOps+Engineer;Cloud+Security+Specialist;AWS+Architect;Kubernetes+Enthusiast" alt="Typing SVG" />
  </a>
</div>

### 🐱 GitHub Stats

<div align="center">
  <img height="180em" src="https://github-profile-summary-cards.vercel.app/api/cards/profile-details?username=Twodragon0&theme=radical" alt="GitHub Profile Details" />
  <img height="180em" src="https://github-profile-summary-cards.vercel.app/api/cards/repos-per-language?username=Twodragon0&theme=radical" alt="Top Languages" />
  <img height="180em" src="https://github-profile-summary-cards.vercel.app/api/cards/most-commit-language?username=Twodragon0&theme=radical" alt="Most Commit Language" />
</div>

<div align="center">
  <img src="https://streak-stats.demolab.com/?user=Twodragon0&theme=radical" alt="GitHub Streak" />
</div>

### 💁 About Me

<p align="center">
  <a href="https://twodragon.tistory.com/"><img src="https://img.shields.io/badge/Blog-FF5722?style=flat-square&logo=Blogger&logoColor=white"/></a>
  <a href="https://2twodragon.com/"><img src="https://img.shields.io/badge/Blog-FF5722?style=flat-square&logo=Blogger&logoColor=white"/></a>
  <a href="mailto:twodragon114@gmail.com"><img src="https://img.shields.io/badge/Gmail-d14836?style=flat-square&logo=Gmail&logoColor=white"/></a>
  <a href="https://github.com/Twodragon0"><img src="https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=GitHub&logoColor=white"/></a>
</p>

### 🛠️ Tech Stack

<p align="center">
  <img src="https://img.shields.io/badge/AWS-232F3E?style=flat-square&logo=Amazon-AWS&logoColor=white"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=Python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Kubernetes-326CE5?style=flat-square&logo=Kubernetes&logoColor=white"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=Docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/Terraform-623CE4?style=flat-square&logo=Terraform&logoColor=white"/>
  <img src="https://img.shields.io/badge/DevSecOps-000000?style=flat-square&logo=GitLab&logoColor=white"/>
  <img src="https://img.shields.io/badge/OpenSearch-005571?style=flat-square&logo=OpenSearch&logoColor=white"/>
  <img src="https://img.shields.io/badge/Bedrock-FF9900?style=flat-square&logo=Amazon-AWS&logoColor=white"/>
</p>

### 📊 GitHub Activity

<div align="center">
  <img src="https://github-readme-activity-graph.vercel.app/graph?username=Twodragon0&theme=radical&hide_border=true" alt="GitHub Activity Graph" />
</div>

### 📦 Featured Repositories

<div align="center">
  
[![AWS IAM Policies](https://github-readme-stats.vercel.app/api/pin/?username=Twodragon0&repo=AWS&theme=radical)](https://github.com/Twodragon0/AWS)
[![Blog RSS Collector](https://github-readme-stats.vercel.app/api/pin/?username=Twodragon0&repo=Blog&theme=radical)](https://github.com/Twodragon0/Blog)
[![ESP32 OpenWrt](https://github-readme-stats.vercel.app/api/pin/?username=Twodragon0&repo=esp32-openwrt&theme=radical)](https://github.com/Twodragon0/esp32-openwrt)

</div>

### 📝 Recent Blog Posts

"""
    
    for idx, post in enumerate(posts, 1):
        readme += f"{idx}. [{post['title']}]({post['link']})\n"
    
    readme += "\n---\n\n"
    readme += "<p align=\"center\">\n"
    readme += f"  <i>Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S KST')}</i>\n"
    readme += "</p>\n"
    
    return readme


if __name__ == "__main__":
    content = generate_profile_readme()
    with open("PROFILE_README.md", "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("GitHub Profile README 생성 완료: PROFILE_README.md")

