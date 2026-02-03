# GitHub 블로그 생성 가이드

Tistory 블로그에서 IT, DevSecOps, 코딩 관련 포스트만 필터링하여 GitHub 블로그로 변환하는 가이드입니다.

## 📋 사전 요구사항

1. **Python 3.8+** 설치
2. **GitHub CLI (gh)** 설치 및 인증
   ```bash
   brew install gh  # macOS
   gh auth login
   ```
3. **필요한 Python 패키지** 설치
   ```bash
   pip install feedparser
   ```

## 🚀 사용 방법

### 1. 스크립트 실행

```bash
python tistory_to_github_blog.py
```

스크립트는 다음 작업을 수행합니다:
- Tistory RSS에서 포스트 수집
- IT/DevSecOps/코딩 관련 포스트만 필터링
- Jekyll 블로그 구조 생성
- 포스트를 마크다운 파일로 변환
- GitHub 저장소 생성
- GitHub Actions 워크플로우 설정

### 2. 생성된 파일 구조

```
tech-blog/
├── _config.yml          # Jekyll 설정
├── _posts/              # 블로그 포스트
│   ├── 2024-01-01-post-title.md
│   └── ...
├── _layouts/            # 레이아웃 파일
│   ├── default.html
│   └── post.html
├── _includes/           # 재사용 가능한 컴포넌트
├── assets/              # CSS, JS, 이미지
├── .github/
│   └── workflows/
│       └── jekyll.yml   # GitHub Actions
├── Gemfile              # Ruby 의존성
├── README.md
└── index.html
```

### 3. 로컬에서 테스트

```bash
cd tech-blog
bundle install
bundle exec jekyll serve
```

브라우저에서 `http://localhost:4000` 접속하여 확인합니다.

### 4. GitHub에 푸시

```bash
cd tech-blog
git init
git add .
git commit -m "Initial commit: Tistory to GitHub Blog"
git remote add origin https://github.com/Twodragon0/tech-blog.git
git branch -M main
git push -u origin main
```

### 5. GitHub Pages 활성화

1. GitHub 저장소로 이동
2. **Settings** → **Pages** 메뉴
3. **Source**에서 **GitHub Actions** 선택
4. 저장 후 자동 배포 시작

### 6. Giscus 설정 (Discussions 연결)

#### 6.1 Discussions 활성화

1. GitHub 저장소로 이동
2. **Settings** → **General** → **Features**
3. **Discussions** 체크박스 활성화

#### 6.2 Giscus 앱 설치

1. [Giscus](https://giscus.app) 접속
2. **Repository** 선택: `Twodragon0/tech-blog`
3. **Discussion category** 선택: `Announcements` (또는 새로 생성)
4. **Enable giscus** 클릭
5. 생성된 설정 정보 복사

#### 6.3 _config.yml 업데이트

`_config.yml` 파일의 `giscus` 섹션을 업데이트합니다:

```yaml
giscus:
  repo: "Twodragon0/tech-blog"
  repo_id: "R_xxxxxxxxxxxxx"  # Giscus에서 제공
  category: "Announcements"
  category_id: "DIC_kw_xxxxxxxxxxxxx"  # Giscus에서 제공
  mapping: "pathname"
  reactions_enabled: "1"
  emit_metadata: "0"
  input_position: "bottom"
  theme: "preferred_color_scheme"
  lang: "ko"
  crossorigin: "anonymous"
```

#### 6.4 변경사항 커밋 및 푸시

```bash
git add _config.yml
git commit -m "Configure Giscus for Discussions"
git push
```

## 🔍 필터링 키워드

스크립트는 다음 키워드를 포함하는 포스트만 포함합니다:

### 포함 키워드 (IT/DevSecOps/코딩)
- **IT 일반**: 개발, 프로그래밍, 코딩, 소프트웨어, 알고리즘
- **DevSecOps**: 보안, security, 취약점, penetration testing, audit
- **클라우드**: AWS, Azure, GCP, Kubernetes, Docker, Terraform
- **프로그래밍 언어**: Python, Java, JavaScript, Go, Rust 등
- **프레임워크/도구**: React, Vue, Git, CI/CD, Jenkins
- **보안 도구**: Burp, ZAP, OWASP, SAST, DAST
- **네트워크/시스템**: Linux, Shell, Database, API, Microservice

### 제외 키워드
- 맛집, 여행, 웨딩, 결혼, 신혼여행
- 에어드랍, 코인, NFT, 블록체인
- 성장스토리, 면접, 자소서, 구직

필터링 로직은 `tistory_to_github_blog.py`의 `TECH_KEYWORDS`와 `EXCLUDE_KEYWORDS`에서 수정할 수 있습니다.

## 🛡️ 보안 고려사항

스크립트는 다음 보안 모범 사례를 따릅니다:

1. **URL 검증**: 화이트리스트 기반 도메인 검증
2. **XSS 방지**: HTML 이스케이프 처리
3. **경로 탐색 방지**: 파일명 생성 시 위험 문자 제거
4. **SQL 인젝션 방지**: 파라미터화된 파일명 생성
5. **에러 처리**: 안전한 예외 처리 및 로깅

## 📝 커스터마이징

### 저장소 이름 변경

`tistory_to_github_blog.py`의 `main()` 함수에서:

```python
repo_name = "my-tech-blog"  # 원하는 이름으로 변경
```

### 필터링 키워드 수정

`tistory_to_github_blog.py`에서:

```python
TECH_KEYWORDS = {
    # 키워드 추가/수정
    'your-keyword',
    ...
}

EXCLUDE_KEYWORDS = {
    # 제외 키워드 추가/수정
    'your-exclude-keyword',
    ...
}
```

### Jekyll 테마 변경

`_config.yml`에서:

```yaml
theme: minima  # 원하는 테마로 변경
```

또는 `Gemfile`에 테마 gem 추가:

```ruby
gem "jekyll-theme-architect"
```

## 🔄 자동 업데이트

새로운 포스트를 자동으로 추가하려면 GitHub Actions 워크플로우를 설정할 수 있습니다:

```yaml
# .github/workflows/update-blog.yml
name: Update Blog Posts

on:
  schedule:
    - cron: '0 0 * * *'  # 매일 자정
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install feedparser
      - run: python tistory_to_github_blog.py
      - run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add .
          git commit -m "Update blog posts" || exit 0
          git push
```

## 📚 참고 자료

- [Jekyll 공식 문서](https://jekyllrb.com/)
- [Giscus 문서](https://github.com/giscus/giscus)
- [GitHub Pages 가이드](https://docs.github.com/en/pages)
- [GitHub Actions 문서](https://docs.github.com/en/actions)

## ⚠️ 문제 해결

### GitHub CLI 인증 오류

```bash
gh auth login
gh auth refresh
```

### Jekyll 빌드 오류

```bash
bundle update
bundle exec jekyll build
```

### Giscus 댓글이 표시되지 않음

1. Discussions가 활성화되어 있는지 확인
2. `_config.yml`의 `repo_id`와 `category_id`가 올바른지 확인
3. 브라우저 콘솔에서 JavaScript 오류 확인

## 📞 지원

문제가 발생하면 GitHub Issues에 등록해주세요.
