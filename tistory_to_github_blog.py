#!/usr/bin/env python3
"""
Tistory 블로그를 GitHub 블로그로 변환하는 스크립트
IT, DevSecOps, 코딩 관련 포스트만 필터링하여 Jekyll 블로그 형태로 생성합니다.

보안 고려사항:
- URL 입력 검증
- 파일 쓰기 안전 처리
- XSS 방지를 위한 HTML 이스케이프
- SQL 인젝션 방지 (파일명 생성 시)
"""

import feedparser
import datetime
import sys
import logging
import html
import time
import socket
import re
import subprocess
import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Set, Any
from urllib.parse import urlparse, urljoin
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 허용된 블로그 도메인 (화이트리스트)
ALLOWED_DOMAINS = [
    "twodragon.tistory.com",
    "2twodragon.com",
    "tech.2twodragon.com",
    "edu.2twodragon.com",
]

# IT, DevSecOps, 코딩 관련 키워드 (소문자로 정규화)
TECH_KEYWORDS = {
    # IT 일반
    "it",
    "개발",
    "프로그래밍",
    "코딩",
    "소프트웨어",
    "알고리즘",
    "데이터구조",
    # DevSecOps
    "devsecops",
    "devops",
    "보안",
    "security",
    "시큐리티",
    "취약점",
    "vulnerability",
    "penetration",
    "pentest",
    "penetration testing",
    "보안 점검",
    "audit",
    # 클라우드
    "aws",
    "azure",
    "gcp",
    "cloud",
    "클라우드",
    "kubernetes",
    "k8s",
    "docker",
    "terraform",
    "ansible",
    "infrastructure",
    "인프라",
    # 프로그래밍 언어
    "python",
    "java",
    "javascript",
    "typescript",
    "go",
    "rust",
    "c++",
    "c#",
    "ruby",
    "php",
    "swift",
    "kotlin",
    "scala",
    # 프레임워크/도구
    "react",
    "vue",
    "angular",
    "node",
    "spring",
    "django",
    "flask",
    "fastapi",
    "git",
    "github",
    "gitlab",
    "ci/cd",
    "jenkins",
    "github actions",
    # 보안 도구
    "burp",
    "zap",
    "nmap",
    "metasploit",
    "wireshark",
    "owasp",
    "sast",
    "dast",
    # 네트워크/시스템
    "network",
    "네트워크",
    "linux",
    "unix",
    "shell",
    "bash",
    "powershell",
    "database",
    "데이터베이스",
    "sql",
    "nosql",
    "mongodb",
    "postgresql",
    "mysql",
    # 기타 기술
    "api",
    "rest",
    "graphql",
    "microservice",
    "마이크로서비스",
    "serverless",
    "lambda",
    "container",
    "컨테이너",
    "orchestration",
    "monitoring",
    "로깅",
    "logging",
    "observability",
    "prometheus",
    "grafana",
    "elk",
    "elasticsearch",
}

# 제외할 키워드 (맛집, 여행, 개인 일기 등)
EXCLUDE_KEYWORDS = {
    "맛집",
    "여행",
    "웨딩",
    "결혼",
    "신혼여행",
    "리조트",
    "호텔",
    "식당",
    "에어드랍",
    "코인",
    "nft",
    "블록체인",
    "암호화폐",
    "galxe",
    "코인",
    "nft",
    "블록체인",
    "암호화폐",
    "galxe",
    "성장스토리",
    "고시원",
    "원룸",
    "면접",
    "자소서",
    "삼성",
    "카카오뱅크",
    "서류",
    "인터뷰",
    "구직",
    "취업",
}

# 네트워크 타임아웃 설정 (초)
REQUEST_TIMEOUT = 30

# 재시도 설정
MAX_RETRIES = 3
RETRY_DELAY = 2  # 초

# User-Agent 설정
USER_AGENT = "Mozilla/5.0 (compatible; BlogRSSCollector/1.0; +https://github.com/Twodragon0/Blog)"


def validate_url(url: str) -> bool:
    """URL 유효성 검증"""
    try:
        result = urlparse(url)
        if result.netloc not in ALLOWED_DOMAINS:
            logger.warning(f"허용되지 않은 도메인: {result.netloc}")
            return False
        if result.scheme not in ["http", "https"]:
            logger.warning(f"허용되지 않은 프로토콜: {result.scheme}")
            return False
        return True
    except Exception as e:
        logger.error(f"URL 검증 중 오류 발생: {e}")
        return False


def sanitize_filename(text: str) -> str:
    """
    파일명으로 사용할 수 있도록 텍스트를 정리합니다.
    SQL 인젝션 및 경로 탐색 공격 방지
    """
    # 위험한 문자 제거
    text = re.sub(r'[<>:"/\\|?*]', "", text)
    # 연속된 공백을 언더스코어로 변경
    text = re.sub(r"\s+", "_", text)
    # 특수문자 제거 (한글, 영문, 숫자, 언더스코어, 하이픈만 허용)
    text = re.sub(r"[^\w\s\-가-힣]", "", text)
    # 길이 제한 (파일명이 너무 길면 잘라냄)
    if len(text) > 100:
        text = text[:100]
    return text.strip()


def sanitize_html(text: str) -> str:
    """HTML 특수문자 이스케이프 처리 (XSS 방지)"""
    return html.escape(text)


def fetch_wordpress_posts(blog_url: str) -> List[Dict[str, Any]]:
    """
    WordPress REST API를 사용하여 포스트 목록을 가져옵니다.
    IT, DevSecOps, 코딩 관련 포스트만 필터링합니다.
    """
    api_url = f"{blog_url}/wp-json/wp/v2/posts"
    logger.info(f"WordPress API 수집 중: {api_url}")

    posts = []
    page = 1
    per_page = 100

    while True:
        try:
            # 페이지네이션 지원
            url = f"{api_url}?per_page={per_page}&page={page}&_embed"

            socket.setdefaulttimeout(REQUEST_TIMEOUT)
            request = Request(url)
            request.add_header("User-Agent", USER_AGENT)
            request.add_header("Accept", "application/json")

            with urlopen(request) as response:
                data = json.loads(response.read().decode("utf-8"))

            if not data:
                break

            for item in data:
                try:
                    # 기본 정보 추출
                    title = sanitize_html(item["title"]["rendered"])
                    link = item["link"]

                    if not validate_url(link):
                        logger.warning(f"유효하지 않은 링크 URL: {link}")
                        continue

                    # 내용 추출
                    content = item.get("content", {}).get("rendered", "")
                    excerpt = item.get("excerpt", {}).get("rendered", "")

                    # 기술 관련 포스트만 필터링
                    if not is_tech_related(title, excerpt + " " + content):
                        logger.debug(f"기술 관련이 아닌 포스트 제외: {title}")
                        continue

                    # 날짜 파싱
                    published_date = None
                    try:
                        if item.get("date"):
                            published_date = datetime.datetime.fromisoformat(
                                item["date"].replace("Z", "+00:00")
                            )
                    except (ValueError, KeyError):
                        pass

                    post = {
                        "title": title,
                        "link": link,
                        "description": sanitize_html(excerpt),
                        "published": item.get("date", ""),
                        "published_date": published_date,
                        "content": content,
                    }
                    posts.append(post)

                except Exception as e:
                    logger.error(f"WordPress 포스트 처리 중 오류: {e}")
                    continue

            page += 1

            # 너무 많은 페이지 방지 (최대 10페이지, 1000개 포스트)
            if page > 10:
                break

        except HTTPError as e:
            if e.code == 400:  # 더 이상 페이지 없음
                break
            logger.warning(f"WordPress API 오류: {e}")
            break
        except Exception as e:
            logger.error(f"WordPress API 수집 중 오류: {e}")
            break

    logger.info(f"{len(posts)}개의 WordPress 포스트 수집 완료")
    return posts


def is_tech_related(title: str, description: str = "") -> bool:
    """
    포스트가 IT, DevSecOps, 코딩 관련인지 확인합니다.

    Args:
        title: 포스트 제목
        description: 포스트 설명 (선택)

    Returns:
        기술 관련이면 True, 그렇지 않으면 False
    """
    # 제외 키워드 확인
    combined_text = (title + " " + description).lower()
    for exclude_keyword in EXCLUDE_KEYWORDS:
        if exclude_keyword.lower() in combined_text:
            logger.debug(f"제외 키워드 발견: {exclude_keyword} in '{title}'")
            return False

    # 기술 키워드 확인
    for keyword in TECH_KEYWORDS:
        if keyword.lower() in combined_text:
            logger.debug(f"기술 키워드 발견: {keyword} in '{title}'")
            return True

    return False


def fetch_blog_posts(blog_url: str) -> List[Dict[str, Any]]:
    """
    블로그 RSS 피드에서 포스트 목록을 가져옵니다.
    IT, DevSecOps, 코딩 관련 포스트만 필터링합니다.
    """
    if not validate_url(blog_url):
        logger.error(f"유효하지 않은 URL: {blog_url}")
        return []

    # 다양한 RSS 피드 경로 시도
    rss_paths = ["/rss", "/feed", "/rss.xml", "/feed.xml", "/atom.xml"]
    rss_url = None
    feed = None

    for path in rss_paths:
        try_url = f"{blog_url}{path}"
        logger.debug(f"RSS 피드 시도 중: {try_url}")

        # 재시도 로직
        for attempt in range(MAX_RETRIES):
            try:
                socket.setdefaulttimeout(REQUEST_TIMEOUT)
                request = Request(try_url)
                request.add_header("User-Agent", USER_AGENT)
                request.add_header(
                    "Accept", "application/rss+xml, application/xml, text/xml"
                )

                temp_feed = feedparser.parse(try_url)

                if temp_feed.bozo and temp_feed.bozo_exception:
                    logger.debug(f"RSS 피드 파싱 오류: {temp_feed.bozo_exception}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                        continue
                    break  # 다음 경로 시도

                if temp_feed.get("entries"):
                    rss_url = try_url
                    feed = temp_feed
                    logger.info(f"RSS 피드 발견: {rss_url}")
                    break

                break  # 다음 경로 시도

            except (URLError, HTTPError) as e:
                logger.debug(f"네트워크 오류: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                break
            except socket.timeout:
                logger.debug(f"타임아웃 오류")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                break
            except Exception as e:
                logger.debug(f"예상치 못한 오류: {e}")
                break

        if feed and feed.get("entries"):
            break

    if not feed or not feed.get("entries"):
        logger.info(f"RSS 피드를 찾을 수 없음. WordPress API 시도: {blog_url}")
        # WordPress REST API 시도
        return fetch_wordpress_posts(blog_url)

    # 포스트 추출 및 필터링
    posts = []
    for entry in feed.get("entries", []):
        try:
            if "link" not in entry or "title" not in entry:
                logger.warning("필수 필드(link, title)가 없는 항목 건너뜀")
                continue

            title = sanitize_html(entry["title"])
            link = entry["link"]
            description = entry.get("summary", entry.get("description", ""))

            if not validate_url(link):
                logger.warning(f"유효하지 않은 링크 URL: {link}")
                continue

            # 기술 관련 포스트만 필터링
            if not is_tech_related(title, description):
                logger.debug(f"기술 관련이 아닌 포스트 제외: {title}")
                continue

            # 날짜 파싱
            published_date = None
            try:
                if entry.get("published"):
                    published_date = datetime.datetime.strptime(
                        entry["published"], "%a, %d %b %Y %H:%M:%S %z"
                    )
            except (ValueError, KeyError):
                pass

            post = {
                "title": title,
                "link": link,
                "description": sanitize_html(description),
                "published": entry.get("published", ""),
                "published_date": published_date,
                "content": entry.get("content", [{}])[0].get("value", "")
                if entry.get("content")
                else "",
            }
            posts.append(post)

        except Exception as e:
            logger.error(f"포스트 처리 중 오류 발생: {e}")
            continue

    logger.info(f"{len(posts)}개의 기술 관련 포스트 수집 완료")
    return posts


def create_jekyll_post(post: Dict[str, Any], output_dir: Path) -> Optional[str]:
    """
    Jekyll 포스트 파일을 생성합니다.

    Args:
        post: 포스트 정보 딕셔너리
        output_dir: 출력 디렉토리

    Returns:
        생성된 파일 경로 또는 None
    """
    try:
        # 날짜 파싱
        if post.get("published_date"):
            date = post["published_date"]
        else:
            date = datetime.datetime.now()

        # 파일명 생성 (안전하게)
        safe_title = sanitize_filename(post["title"])
        filename = f"{date.strftime('%Y-%m-%d')}-{safe_title}.md"
        filepath = output_dir / filename

        # 중복 방지
        counter = 1
        original_filepath = filepath
        while filepath.exists():
            filename = f"{date.strftime('%Y-%m-%d')}-{safe_title}-{counter}.md"
            filepath = output_dir / filename
            counter += 1
            if counter > 100:  # 무한 루프 방지
                logger.error(f"파일명 생성 실패: {post['title']}")
                return None

        # Jekyll front matter 생성
        front_matter = f"""---
layout: post
title: "{post["title"]}"
date: {date.strftime("%Y-%m-%d %H:%M:%S %z")}
categories: [IT, DevSecOps, 코딩]
tags: []
comments: true
original_url: {post["link"]}
---
"""

        # 본문 생성
        content = post.get("content", "")
        if not content:
            content = post.get("description", "")

        # 원본 링크 추가
        content += f"\n\n원본 포스트: [{post['link']}]({post['link']})\n"

        # 파일 작성
        filepath.write_text(front_matter + content, encoding="utf-8")
        logger.info(f"포스트 생성 완료: {filename}")
        return str(filepath)

    except Exception as e:
        logger.error(f"포스트 생성 중 오류: {e}")
        return None


def create_jekyll_structure(
    output_dir: Path, repo_name: str, github_username: str
) -> None:
    """
    Jekyll 블로그 기본 구조를 생성합니다.
    """
    # 디렉토리 생성
    (output_dir / "_posts").mkdir(parents=True, exist_ok=True)
    (output_dir / "_layouts").mkdir(parents=True, exist_ok=True)
    (output_dir / "_includes").mkdir(parents=True, exist_ok=True)
    (output_dir / "assets").mkdir(parents=True, exist_ok=True)
    (output_dir / "assets" / "css").mkdir(parents=True, exist_ok=True)
    (output_dir / "assets" / "js").mkdir(parents=True, exist_ok=True)

    # _config.yml 생성
    config_content = f"""# Site Settings
title: "{github_username}'s Tech Blog"
description: "IT, DevSecOps, 코딩 관련 기술 블로그"
url: "https://{github_username}.github.io"
baseurl: "/{repo_name}" if repo_name != "{github_username}.github.io" else ""

# Author
author:
  name: "{github_username}"
  email: "twodragon114@gmail.com"

# Build Settings
markdown: kramdown
highlighter: rouge
theme: minima
plugins:
  - jekyll-feed
  - jekyll-sitemap

# Giscus Comments (Discussions 연결)
giscus:
  repo: "{github_username}/{repo_name}"
  repo_id: ""  # Giscus 설정 후 입력 필요
  category: "Announcements"
  category_id: ""  # Giscus 설정 후 입력 필요
  mapping: "pathname"
  reactions_enabled: "1"
  emit_metadata: "0"
  input_position: "bottom"
  theme: "preferred_color_scheme"
  lang: "ko"
  crossorigin: "anonymous"

# Exclude
exclude:
  - Gemfile
  - Gemfile.lock
  - node_modules
  - vendor
  - .git
  - .gitignore
"""
    (output_dir / "_config.yml").write_text(config_content, encoding="utf-8")

    # index.html 생성
    index_content = """---
layout: default
---

<div class="home">
  <h1 class="page-heading">Posts</h1>
  
  <ul class="post-list">
    {% for post in site.posts %}
      <li>
        <span class="post-meta">{{ post.date | date: "%b %-d, %Y" }}</span>
        <h2>
          <a class="post-link" href="{{ post.url | relative_url }}">{{ post.title | escape }}</a>
        </h2>
        {% if post.original_url %}
          <p class="post-meta">
            <a href="{{ post.original_url }}" target="_blank">원본 포스트 보기</a>
          </p>
        {% endif %}
      </li>
    {% endfor %}
  </ul>
  
  <p class="rss-subscribe">subscribe <a href="{{ "/feed.xml" | relative_url }}">via RSS</a></p>
</div>
"""
    (output_dir / "index.html").write_text(index_content, encoding="utf-8")

    # post.html 레이아웃 생성 (giscus 포함)
    post_layout = """---
layout: default
---
<article class="post h-entry" itemscope itemtype="http://schema.org/BlogPosting">
  <header class="post-header">
    <h1 class="post-title p-name" itemprop="name headline">{{ page.title | escape }}</h1>
    <p class="post-meta">
      <time class="dt-published" datetime="{{ page.date | date_to_xmlschema }}" itemprop="datePublished">
        {{ page.date | date: "%b %-d, %Y" }}
      </time>
      {% if page.original_url %}
        | <a href="{{ page.original_url }}" target="_blank">원본 포스트</a>
      {% endif %}
    </p>
  </header>

  <div class="post-content e-content" itemprop="articleBody">
    {{ content }}
  </div>

  {% if site.giscus %}
    <script src="https://giscus.app/client.js"
            data-repo="{{ site.giscus.repo }}"
            data-repo-id="{{ site.giscus.repo_id }}"
            data-category="{{ site.giscus.category }}"
            data-category-id="{{ site.giscus.category_id }}"
            data-mapping="{{ site.giscus.mapping }}"
            data-reactions-enabled="{{ site.giscus.reactions_enabled }}"
            data-emit-metadata="{{ site.giscus.emit_metadata }}"
            data-input-position="{{ site.giscus.input_position }}"
            data-theme="{{ site.giscus.theme }}"
            data-lang="{{ site.giscus.lang }}"
            crossorigin="{{ site.giscus.crossorigin }}"
            async>
    </script>
  {% endif %}

  <a class="u-url" href="{{ page.url | relative_url }}" hidden></a>
</article>
"""
    (output_dir / "_layouts" / "post.html").write_text(post_layout, encoding="utf-8")

    # default.html 레이아웃 생성
    default_layout = """<!DOCTYPE html>
<html lang="{{ site.lang | default: "ko" }}">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% if page.title %}{{ page.title | escape }}{% else %}{{ site.title | escape }}{% endif %}</title>
    <meta name="description" content="{% if page.excerpt %}{{ page.excerpt | strip_html | strip_newlines | truncate: 160 }}{% else %}{{ site.description }}{% endif %}">
    <link rel="stylesheet" href="{{ "/assets/css/main.css" | relative_url }}">
    <link rel="canonical" href="{{ page.url | replace:'index.html','' | absolute_url }}">
    <link rel="alternate" type="application/rss+xml" title="{{ site.title | escape }}" href="{{ "/feed.xml" | relative_url }}">
  </head>
  <body>
    <header class="site-header">
      <div class="wrapper">
        <a class="site-title" href="{{ "/" | relative_url }}">{{ site.title | escape }}</a>
        <nav class="site-nav">
          <div class="trigger">
            <a class="page-link" href="{{ "/" | relative_url }}">Home</a>
          </div>
        </nav>
      </div>
    </header>

    <main class="page-content">
      <div class="wrapper">
        {{ content }}
      </div>
    </main>

    <footer class="site-footer">
      <div class="wrapper">
        <p>&copy; {{ site.time | date: '%Y' }} {{ site.author.name }}. All rights reserved.</p>
      </div>
    </footer>
  </body>
</html>
"""
    (output_dir / "_layouts" / "default.html").write_text(
        default_layout, encoding="utf-8"
    )

    # README.md 생성
    readme_content = f"""# {github_username}'s Tech Blog

IT, DevSecOps, 코딩 관련 기술 블로그입니다.

## 구조

- `_posts/`: 블로그 포스트
- `_layouts/`: Jekyll 레이아웃 파일
- `_includes/`: 재사용 가능한 컴포넌트
- `assets/`: CSS, JS, 이미지 등 정적 파일

## 로컬 실행

```bash
bundle install
bundle exec jekyll serve
```

## Giscus 설정

1. [Giscus](https://giscus.app)에서 저장소 연결
2. `_config.yml`의 `giscus` 섹션에 `repo_id`와 `category_id` 입력
3. Discussions 활성화 확인

## 자동 배포

GitHub Actions를 통해 자동으로 배포됩니다.
"""
    (output_dir / "README.md").write_text(readme_content, encoding="utf-8")

    # .gitignore 생성
    gitignore_content = """_site/
.sass-cache/
.jekyll-cache/
.jekyll-metadata
vendor/
.bundle/
Gemfile.lock
"""
    (output_dir / ".gitignore").write_text(gitignore_content, encoding="utf-8")

    # Gemfile 생성
    gemfile_content = """source "https://rubygems.org"

gem "jekyll", "~> 4.3"
gem "jekyll-feed", "~> 0.15"
gem "jekyll-sitemap", "~> 1.4"
gem "minima", "~> 2.5"

group :jekyll_plugins do
  gem "jekyll-feed", "~> 0.15"
  gem "jekyll-sitemap", "~> 1.4"
end
"""
    (output_dir / "Gemfile").write_text(gemfile_content, encoding="utf-8")

    logger.info("Jekyll 블로그 구조 생성 완료")


def create_github_repo(owner: str, repo_name: str, description: str) -> bool:
    """
    GitHub 저장소를 생성합니다.
    """
    try:
        # GitHub CLI 확인
        result = subprocess.run(["gh", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("GitHub CLI (gh)가 설치되어 있지 않습니다.")
            return False

        # 저장소가 이미 존재하는지 확인
        check_cmd = f"gh repo view {owner}/{repo_name} --json name 2>/dev/null"
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info(f"✅ {repo_name} 저장소가 이미 존재합니다.")
            return True

        # 새 저장소 생성 (Public)
        create_cmd = (
            f"gh repo create {owner}/{repo_name} --public --description '{description}'"
        )
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


def create_github_actions_workflow(output_dir: Path) -> None:
    """
    GitHub Actions 워크플로우를 생성합니다.
    """
    workflow_dir = output_dir / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)

    workflow_content = """name: Deploy Jekyll site to Pages

on:
  push:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Setup Ruby
        uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.1'
          bundler-cache: true
          cache-version: 0
      
      - name: Setup Pages
        id: pages
        uses: actions/configure-pages@v4
      
      - name: Build with Jekyll
        run: bundle exec jekyll build --baseurl "${{ steps.pages.outputs.base_path }}"
        env:
          JEKYLL_ENV: production
      
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
"""
    (workflow_dir / "jekyll.yml").write_text(workflow_content, encoding="utf-8")
    logger.info("GitHub Actions 워크플로우 생성 완료")


def main():
    """메인 실행 함수"""
    # 명령줄 인자 파싱
    parser = argparse.ArgumentParser(description="멀티 블로그를 GitHub 블로그로 변환")
    parser.add_argument(
        "--overwrite", "-y", action="store_true", help="출력 디렉토리 덮어쓰기"
    )
    parser.add_argument("--repo-name", default="tech-blog", help="GitHub 저장소 이름")
    parser.add_argument("--username", default="Twodragon0", help="GitHub 사용자명")
    args = parser.parse_args()

    # 수집할 블로그 URL 목록
    blog_urls = [
        "https://twodragon.tistory.com",
        "https://2twodragon.com",
        "https://tech.2twodragon.com",
        "https://edu.2twodragon.com",
    ]
    github_username = args.username
    repo_name = args.repo_name

    logger.info("=" * 60)
    logger.info("멀티 블로그 → GitHub 블로그 변환 시작")
    logger.info("=" * 60)

    # 1. 포스트 수집 및 필터링
    logger.info("1단계: 여러 블로그에서 포스트 수집 및 필터링")
    all_posts = []
    for blog_url in blog_urls:
        logger.info(f"블로그 수집 중: {blog_url}")
        posts = fetch_blog_posts(blog_url)
        if posts:
            logger.info(f"  → {len(posts)}개의 기술 관련 포스트 수집")
            all_posts.extend(posts)
        else:
            logger.warning(f"  → 수집된 포스트 없음")

    if not all_posts:
        logger.error("수집된 포스트가 없습니다.")
        sys.exit(1)

    # 중복 제거 (같은 링크의 포스트)
    unique_posts = {}
    for post in all_posts:
        if post["link"] not in unique_posts:
            unique_posts[post["link"]] = post

    posts = list(unique_posts.values())
    logger.info(f"총 {len(posts)}개의 유니크한 기술 관련 포스트를 찾았습니다.")

    # 2. 출력 디렉토리 생성
    output_dir = Path(f"./{repo_name}")
    if output_dir.exists() and not args.overwrite:
        logger.error(f"출력 디렉토리가 이미 존재합니다: {output_dir}")
        logger.error("덮어쓰려면 --overwrite 또는 -y 옵션을 사용하세요.")
        sys.exit(1)

    # 3. Jekyll 구조 생성
    logger.info("2단계: Jekyll 블로그 구조 생성")
    create_jekyll_structure(output_dir, repo_name, github_username)

    # 4. 포스트 생성
    logger.info("3단계: 포스트 파일 생성")
    posts_dir = output_dir / "_posts"
    created_count = 0
    for post in posts:
        if create_jekyll_post(post, posts_dir):
            created_count += 1

    logger.info(f"{created_count}개의 포스트 파일 생성 완료")

    # 5. GitHub Actions 워크플로우 생성
    logger.info("4단계: GitHub Actions 워크플로우 생성")
    create_github_actions_workflow(output_dir)

    # 6. GitHub 저장소 생성
    logger.info("5단계: GitHub 저장소 생성")
    description = "IT, DevSecOps, 코딩 관련 기술 블로그"
    if create_github_repo(github_username, repo_name, description):
        logger.info("✅ 모든 작업이 완료되었습니다!")
        logger.info(f"다음 단계:")
        logger.info(f"1. cd {repo_name}")
        logger.info(f"2. git init")
        logger.info(f"3. git add .")
        logger.info(f"4. git commit -m 'Initial commit: Tistory to GitHub Blog'")
        logger.info(
            f"5. git remote add origin https://github.com/{github_username}/{repo_name}.git"
        )
        logger.info(f"6. git push -u origin main")
        logger.info(f"7. GitHub 저장소 설정에서 Pages 활성화")
        logger.info(f"8. Giscus 설정: https://giscus.app")
    else:
        logger.warning("저장소 생성에 실패했지만, 로컬 파일은 생성되었습니다.")


if __name__ == "__main__":
    main()
