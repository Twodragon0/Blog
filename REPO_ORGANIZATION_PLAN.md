# GitHub 저장소 정리 계획

> 생성일: 2025-12-26 18:56:11 KST

## 📊 현재 상태

- **총 저장소 수**: 7개
- **원본 저장소**: 4개
- **포크된 저장소**: 3개

## 📁 카테고리별 분류

### AWS-SECURITY
- **AWS** (Python) - IAM policies for various use cases

### IOT
- **esp32-openwrt** (Python) - ESP32-MDF (ESP-Mesh) and OpenWrt Socket
- **OpenWRT-IPFS** (Shell) - IPFS in Raspberry Pi based on OpenWrt/Untangle/pfsense

### SECURITY
- **audit-points** (Python) - Audit Points 공유를 위한 Repository
- **prowler** (Python) - Prowler is an Open Source Security tool for AWS, Azure, GCP and Kubernetes
- **DevSecOps** (Go) - Collection and Roadmap for everyone who wants DevSecOps

### AUTOMATION
- **Blog** (Python) - Blog RSS Feed Collector and README updater

## 🎯 정리 권장사항

### 1. ARCHIVE: audit-points, prowler, DevSecOps
**이유**: 포크된 저장소는 원본 저장소를 참조하므로 Archive 처리 권장

### 2. CONSOLIDATE: esp32-openwrt, OpenWRT-IPFS
**이유**: IoT 관련 저장소들을 하나의 monorepo로 통합 고려
**제안 이름**: `iot-projects`

### 3. ORGANIZE: AWS
**이유**: AWS 관련 저장소들을 별도 조직 또는 태그로 정리

## 📝 실행 계획

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

