#!/usr/bin/env python3
"""
GitHub README 업데이트 스크립트
두 개의 블로그(twodragon.tistory.com, 2twodragon.com)에서 RSS 피드를 수집하여 README.md를 업데이트합니다.

보안 고려사항:
- URL 입력 검증
- 파일 쓰기 안전 처리
- 에러 처리 및 로깅
- XSS 방지를 위한 HTML 이스케이프
"""

import feedparser
import datetime
import sys
import logging
import html
import time
import socket
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 허용된 블로그 도메인 (화이트리스트)
ALLOWED_DOMAINS = ['twodragon.tistory.com', '2twodragon.com', 'tech.2twodragon.com']

# 수집할 피드 URL. 블로그마다 피드 경로가 달라서 `<url>/rss` 로 조립하지 않고 명시한다.
#
# 2026-09-11 실측:
#   https://twodragon.tistory.com/rss      200 · 30건
#   https://tech.2twodragon.com/feed.xml   200 · 50건
#   https://2twodragon.com/rss             200 이지만 HTML 을 돌려준다 · 0건
#   https://2twodragon.com/feed(/)         200 · 0건
# 즉 2twodragon.com 은 피드가 꺼져 있다. `/rss` 를 붙이면 HTML 을 받아 feedparser 가
# bozo 로 처리하고 3회 재시도 후 빈 리스트를 내놓는다 — 조용히 실패하므로 아예 뺀다.
# 링크로는 계속 소개하되 수집 대상은 아니다.
# (표시 이름, 블로그 URL, 피드 URL)
BLOG_FEEDS = [
    ('Tech Blog', 'https://tech.2twodragon.com', 'https://tech.2twodragon.com/feed.xml'),
    ('Tistory', 'https://twodragon.tistory.com', 'https://twodragon.tistory.com/rss'),
]

# 블로그 한 곳당 README 에 실을 포스트 수
POSTS_PER_BLOG = 10

# 최대 수집할 포스트 수
MAX_POSTS = 30

# 네트워크 타임아웃 설정 (초)
REQUEST_TIMEOUT = 30

# 재시도 설정
MAX_RETRIES = 3
RETRY_DELAY = 2  # 초

# User-Agent 설정 (일부 서버에서 User-Agent가 없으면 차단할 수 있음)
USER_AGENT = 'Mozilla/5.0 (compatible; BlogRSSCollector/1.0; +https://github.com/Twodragon0/Blog)'


def validate_url(url: str) -> bool:
    """
    URL 유효성 검증
    
    Args:
        url: 검증할 URL 문자열
        
    Returns:
        유효한 URL이면 True, 그렇지 않으면 False
    """
    try:
        result = urlparse(url)
        # 허용된 도메인인지 확인
        if result.netloc not in ALLOWED_DOMAINS:
            logger.warning(f"허용되지 않은 도메인: {result.netloc}")
            return False
        # HTTP/HTTPS 프로토콜만 허용
        if result.scheme not in ['http', 'https']:
            logger.warning(f"허용되지 않은 프로토콜: {result.scheme}")
            return False
        return True
    except Exception as e:
        logger.error(f"URL 검증 중 오류 발생: {e}")
        return False


def sanitize_html(text: str) -> str:
    """
    HTML 특수문자 이스케이프 처리 (XSS 방지)

    **먼저 풀고 나서 한 번만 조인다.** 그냥 `html.escape` 만 하면 이미 인코딩된 피드
    제목이 두 번 조여진다 — Tistory 의 `Docker &amp; Kubernetes` 가 `&amp;amp;` 가 돼
    README 에 `Docker &amp; Kubernetes` 로 그대로 보였다 (2026-09-11 실측).
    피드마다 인코딩 횟수가 달라서, 더 안 풀릴 때까지 풀어 정규화한 뒤 한 번 조인다.

    Args:
        text: 이스케이프할 텍스트

    Returns:
        정확히 한 번 이스케이프된 텍스트
    """
    previous = None
    current = text
    # 중첩 인코딩을 모두 벗긴다. 고정점에 닿으면 멈춘다
    while current != previous:
        previous = current
        current = html.unescape(current)
    # 마크다운 링크 텍스트로 들어가므로 따옴표는 건드리지 않는다
    return html.escape(current, quote=False)


def fetch_blog_posts(rss_url: str) -> List[Dict[str, str]]:
    """
    블로그 RSS 피드에서 포스트 목록을 가져옵니다.
    재시도 로직과 타임아웃 처리가 포함되어 있습니다.

    Args:
        rss_url: 피드 URL 전체 (`BLOG_FEEDS` 참고). 경로를 여기서 조립하지 않는다

    Returns:
        포스트 정보 딕셔너리 리스트
    """
    if not validate_url(rss_url):
        logger.error(f"유효하지 않은 URL: {rss_url}")
        return []

    logger.info(f"RSS 피드 수집 중: {rss_url}")
    
    # 재시도 로직
    for attempt in range(MAX_RETRIES):
        try:
            # 타임아웃 설정을 위한 소켓 타임아웃
            socket.setdefaulttimeout(REQUEST_TIMEOUT)
            
            # User-Agent를 포함한 요청 생성
            request = Request(rss_url)
            request.add_header('User-Agent', USER_AGENT)
            request.add_header('Accept', 'application/rss+xml, application/xml, text/xml')
            
            # 피드 파싱 (feedparser가 내부적으로 요청 처리)
            feed = feedparser.parse(rss_url)
            
            # 피드 파싱 오류 확인
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"RSS 피드 파싱 오류 (시도 {attempt + 1}/{MAX_RETRIES}): {feed.bozo_exception}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))  # 지수 백오프
                    continue
                return []
            
            # 피드가 비어있는지 확인
            if not feed.get('entries'):
                logger.warning(f"RSS 피드에 항목이 없습니다: {rss_url}")
                return []
            
            break  # 성공 시 루프 종료
            
        except (URLError, HTTPError) as e:
            logger.warning(f"네트워크 오류 (시도 {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            logger.error(f"RSS 피드 수집 실패: {rss_url}")
            return []
        except socket.timeout:
            logger.warning(f"타임아웃 오류 (시도 {attempt + 1}/{MAX_RETRIES}): {rss_url}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            logger.error(f"RSS 피드 수집 타임아웃: {rss_url}")
            return []
        except Exception as e:
            logger.error(f"예상치 못한 오류 (시도 {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            return []
    
    # 피드 파싱이 성공했으므로 포스트 추출
    posts = []
    for entry in feed.get('entries', [])[:MAX_POSTS]:
        try:
            # 필수 필드 확인
            if 'link' not in entry or 'title' not in entry:
                logger.warning("필수 필드(link, title)가 없는 항목 건너뜀")
                continue
            
            # HTML 이스케이프 처리
            title = sanitize_html(entry['title'])
            link = entry['link']
            
            # 링크 URL 검증
            if not validate_url(link):
                logger.warning(f"유효하지 않은 링크 URL: {link}")
                continue
            
            post = {
                'title': title,
                'link': link,
                'published': entry.get('published', '')
            }
            posts.append(post)
            
        except Exception as e:
            logger.error(f"포스트 처리 중 오류 발생: {e}")
            continue
    
    logger.info(f"{len(posts)}개의 포스트 수집 완료")
    return posts


def merge_and_sort_posts(posts_list: List[List[Dict[str, str]]]) -> List[Dict[str, str]]:
    """
    여러 블로그의 포스트를 병합하고 날짜순으로 정렬합니다.
    
    Args:
        posts_list: 각 블로그의 포스트 리스트
        
    Returns:
        병합 및 정렬된 포스트 리스트
    """
    all_posts = []
    for posts in posts_list:
        all_posts.extend(posts)
    
    # 중복 제거 (링크 기준)
    seen_links = set()
    unique_posts = []
    for post in all_posts:
        if post['link'] not in seen_links:
            seen_links.add(post['link'])
            unique_posts.append(post)
    
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
    
    unique_posts.sort(key=get_sort_key, reverse=True)
    
    return unique_posts[:MAX_POSTS]


def generate_readme_content(
    posts_by_source: List[Tuple[str, str, List[Dict[str, str]]]]
) -> str:
    """
    README.md 내용을 생성합니다.

    Args:
        posts_by_source: `(블로그 이름, 블로그 URL, 포스트 리스트)` 튜플의 리스트.
            합쳐진 하나의 리스트가 아니라 **출처별로 나뉜** 형태를 받는다 — 이유는
            아래 렌더링 루프의 주석 참고

    Returns:
        생성된 마크다운 내용
    """
    markdown_text = """
# Blog — RSS collector

This repository is the **automation**, not the blog. It pulls posts from the feeds below
and regenerates this README on a schedule.

| Where | What | Feed |
|---|---|---|
| [tech.2twodragon.com](https://tech.2twodragon.com) | Tech blog — Jekyll, built from [`tech-blog`](https://github.com/Twodragon0/tech-blog) | `/feed.xml` ✅ |
| [twodragon.tistory.com](https://twodragon.tistory.com) | Main blog | `/rss` ✅ |
| [2twodragon.com](https://2twodragon.com) | Personal site | no feed — **not collected** |

👤 **Profile:** [github.com/Twodragon0](https://github.com/Twodragon0) — the profile README
lives in [`Twodragon0/Twodragon0`](https://github.com/Twodragon0/Twodragon0) and pulls the
same feeds itself. This repo does **not** write to it.

### 🐱 GitHub Stats

<div align="center">
  <img src="https://github-profile-summary-cards.vercel.app/api/cards/profile-details?username=Twodragon0&theme=radical" alt="GitHub Profile Details" />
  <img src="https://github-profile-summary-cards.vercel.app/api/cards/repos-per-language?username=Twodragon0&theme=radical" alt="Top Languages" />
  <img src="https://github-profile-summary-cards.vercel.app/api/cards/most-commit-language?username=Twodragon0&theme=radical" alt="Most Commit Language" />
</div>

<div align="center">
  <img src="https://streak-stats.demolab.com/?user=Twodragon0&theme=radical" alt="GitHub Streak" />
</div>

### 💁 About Me

<p align="center">
  <a href="https://tech.2twodragon.com/"><img src="https://img.shields.io/badge/Tech%20Blog-0A0A0A?style=flat-square&logo=Jekyll&logoColor=white"/></a>
  <a href="https://twodragon.tistory.com/"><img src="https://img.shields.io/badge/Tistory-FF5722?style=flat-square&logo=Blogger&logoColor=white"/></a>
  <a href="https://2twodragon.com/"><img src="https://img.shields.io/badge/Site-4A4A4A?style=flat-square&logo=WordPress&logoColor=white"/></a>
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
</p>

### 📝 Recent Blog Posts

"""

    # 블로그별로 나눠 싣는다.
    #
    # 두 피드를 한 리스트로 합쳐 최신순 상위 N건만 자르면 **한쪽 블로그가 통째로 사라진다.**
    # 2026-09-11 실측 — Tistory 최신글은 2026-02-06, tech.2twodragon.com 은 2026-09-13 이라
    # 합친 상위 30건이 전부 후자로 채워졌다. 정렬 버그가 아니라 갱신 주기가 다른 것이고,
    # 그래서 잘라내기가 아니라 나눠 싣기로 푼다.
    for label, url, source_posts in posts_by_source:
        if not source_posts:
            continue
        markdown_text += f"**[{label}]({url})**\n\n"
        for idx, post in enumerate(source_posts[:POSTS_PER_BLOG], 1):
            # HTML 이스케이프는 수집 시점에 처리되었으므로 안전하게 사용
            markdown_text += f"{idx}. [{post['title']}]({post['link']})\n"
        markdown_text += "\n"

    markdown_text += "\n---\n\n"
    markdown_text += "<p align=\"center\">\n"
    markdown_text += "  <i>Last updated: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S KST") + "</i>\n"
    markdown_text += "</p>\n"
    
    return markdown_text


def write_readme(content: str, output_path: str = "README.md") -> bool:
    """
    README.md 파일을 안전하게 작성합니다.
    
    Args:
        content: 작성할 내용
        output_path: 출력 파일 경로
        
    Returns:
        성공 여부
    """
    try:
        output_file = Path(output_path)
        
        # 경로 검증 (상위 디렉토리로 이동 방지)
        if '..' in str(output_file):
            logger.error("상위 디렉토리 접근 시도 감지")
            return False
        
        # 임시 파일에 먼저 작성
        temp_file = output_file.with_suffix('.tmp')
        temp_file.write_text(content, encoding='utf-8')
        
        # 원본 파일이 존재하면 백업
        if output_file.exists():
            backup_file = output_file.with_suffix('.bak')
            output_file.rename(backup_file)
        
        # 임시 파일을 원본 파일로 이동
        temp_file.rename(output_file)
        
        # 백업 파일 삭제
        backup_file = output_file.with_suffix('.bak')
        if backup_file.exists():
            backup_file.unlink()
        
        logger.info(f"README.md 업데이트 완료: {output_path}")
        return True
        
    except PermissionError:
        logger.error(f"파일 쓰기 권한 없음: {output_path}")
        return False
    except Exception as e:
        logger.error(f"파일 쓰기 중 오류 발생: {e}")
        return False


def main():
    """메인 실행 함수"""
    logger.info("블로그 포스트 수집 시작")

    # 각 블로그에서 포스트 수집 — 출처를 유지한 채로 담는다
    posts_by_source = []
    for label, blog_url, feed_url in BLOG_FEEDS:
        posts = fetch_blog_posts(feed_url)
        if posts:
            # 블로그 안에서만 최신순으로 정렬한다 (블로그 간 비교는 하지 않는다)
            posts = merge_and_sort_posts([posts])
            posts_by_source.append((label, blog_url, posts))
        else:
            # 한 피드가 죽어도 나머지로 계속 간다. 다만 조용히 넘기지는 않는다 —
            # 2twodragon.com 이 정확히 이렇게 몇 달을 0건으로 돌았다.
            logger.warning(f"피드에서 수집된 포스트가 0건이다: {feed_url}")

    if not posts_by_source:
        logger.error("수집된 포스트가 없습니다.")
        sys.exit(1)

    # README 내용 생성
    readme_content = generate_readme_content(posts_by_source)

    # README 파일 작성
    if not write_readme(readme_content):
        logger.error("README.md 작성 실패")
        sys.exit(1)

    total = sum(len(p) for _, _, p in posts_by_source)
    summary = ' · '.join(f"{label} {len(p)}건" for label, _, p in posts_by_source)
    logger.info(f"README.md 업데이트 완료 — 총 {total}건 ({summary})")


if __name__ == "__main__":
    main()
