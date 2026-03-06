<div align="center">
  <h1>💧 온유(On_You) :<br />AI 피부 분석 · 성분 OCR · 올리브영 제품 추천 챗봇</h1>
  <div align="center" style="margin: 16px 0 20px 0">
    <img src="front/src/assets/logo.png" width="400">
  </div>
  <b>AI Skin Analysis & OliveYoung Product Recommendation Chatbot</b>
  <p>딥러닝 피부 정량 분석 · VLM 기반 전성분 OCR · LangGraph 오케스트레이션 · 올리브영 실상품 검증 추천</p>
</div>

<br />

<h2><img src="assets/팀로고.png" width="70" style="margin-right: 8px"> Team. <b>King Ghidorah</b> v1.0 </h2>

### 팀원 소개

<div align="center">
  <table>
    <colgroup>
      <col style="width: 20%;">
      <col style="width: 20%;">
      <col style="width: 20%;">
      <col style="width: 20%;">
      <col style="width: 20%;">
    </colgroup>
    <tbody>
      <tr>
        <td align="center"><img src="assets/왼쪽.png" alt="왼쪽날개-송민채"></td>
        <td align="center"><img src="assets/왼쪽 얼굴.png" alt="왼쪽얼굴-정석원"></td>
        <td align="center"><img src="assets/중앙.png" alt="중앙얼굴-강승원"></td>
        <td align="center"><img src="assets/오른쪽 얼굴.png" alt="오른쪽얼굴-정유선"></td>
        <td align="center"><img src="assets/오른쪽 날개.png" alt="오른쪽날개-이승연"></td>
      </tr>
      <tr style="font-weight: bold;">
        <td align="center">송민채</td>
        <td align="center">정석원</td>
        <td align="center">강승원 (팀장)</td>
        <td align="center">정유선</td>
        <td align="center">이승연</td>
      </tr>
      <tr>
        <td align="center">
          <a href="https://github.com/minchaesong"><img src="https://img.shields.io/badge/minchaesong-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub - 송민채"></a>
        </td>
        <td align="center">
          <a href="https://github.com/jsrop07"><img src="https://img.shields.io/badge/jsrop07-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub - 정석원"></a>
        </td>
        <td align="center">
          <a href="https://github.com/chopa4452"><img src="https://img.shields.io/badge/chopa4452-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub - 강승원"></a>
        </td>
        <td align="center">
          <a href="https://github.com/jys96"><img src="https://img.shields.io/badge/jys96-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub - 정유선"></a>
        </td>
        <td align="center">
          <a href="https://github.com/oooonbbo-wq"><img src="https://img.shields.io/badge/oooonbbo wq-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub - 이승연"></a>
        </td>
      </tr>
    </tbody>
  </table>
</div>

| 이름 | 담당 업무 |
| :-: | :-- |
| 강승원<br />(PM/LLM/BACK) | ResNet50 기반 피부 정량 분석 모델 학습(Fast/Deep), 전성분 추출 모델 학습, LangGraph 파이프라인 설계 및 프롬프트 엔지니어링 |
| 정석원<br />(LLM/BACK) | LLM 응답 생성기 구현 및 LLM 라우터, 올리브영 제품 검증 파이프라인, RAG 기반 답변 보강, FastAPI 백엔드 개발 |
| 정유선<br />(FRONT/BACK) | React 프론트엔드 개발, ChromaDB 벡터 DB 구축 및 관리, RAG 파이프라인 구현, 임베딩 모델(ko-sroberta) 연동, FastAPI 구축 및 백엔드 API 개발 |
| 송민채<br />(BACK/DB) | MySQL 데이터베이스 설계(ERD), 사용자/분석/위시리스트 테이블 구조, FastAPI 백엔드 API 설계 및 개발, 분석 이력 저장 로직 |
| 이승연<br />(AWS/UI) | AWS 인프라(EC2 배포·S3·MariaDB) 구축 및 운영, 로고·UI·인포그래픽 제작, 브랜드 아이덴티티 기획 |

---

## 1. 프로젝트 기간

**2025.02.27 ~ 2025.03.03** (5일)

---

## 2. 프로젝트 개요

<div align="center" style="margin: 10px 0 20px 0">
  <img src="assets/logo.gif" width="600" />
</div>

**On You, 오직 당신만을 위한 스킨케어**

On-you(온유)는 화장품에 관심이 많은 20~30대를 대상으로 한 AI 기반 스킨케어 추천 챗봇입니다.

사용자는 대화를 통해 피부 타입·고민·성분·취향을 입력하여 자신에게 적합한 제품을 추천받을 수 있으며 제품의 전성분(성분표) 사진을 촬영/업로드 시, 성분을 추출·분석해 나에게 적합한 성분/주의가 필요한 성분을 안내합니다. 또한 피부 정밀 분석 결과를 통해 현재 피부 상태, 피부 타입, 민감 요인에 맞는 개인 피부관리법을 제공하는 맞춤 스킨케어 서비스입니다.

### 2.1. 프로젝트 배경 및 목적

<div align="center">
  <img src="assets/뉴스.png" width="500" alt="news1">
  <br />
  <img src="assets/뉴스2.png" width="500" alt="news2">
  <br />
  <img src="assets/뉴스3.png" width="500" alt="news3">
</div>

올리브영은 국내 온라인 뷰티 플랫폼 3사(올리브영·화해·글로우픽) 중에서도 사용자 관심도와 영향력이 가장 높은 플랫폼으로, 화장품 구매와 제품 정보 탐색이 활발하게 이루어지는 대표적인 뷰티 커머스 채널입니다. 이러한 시장 영향력과 사용자 접근성을 고려했을 때, **올리브영 기반의 제품 데이터는 실제 상품 상세 페이지와 연결된 구매 가능 정보를 포함하고 있어, 추천 결과를 실제 구매로 이어지게 할 수 있는 실사용 가치가 높은 데이터**라고 판단했습니다.

현재 올리브영은 매장에서 기기를 통해 피부 상태를 측정하는 체험형 AI 서비스 [스킨스캔(Skin Scan)]을 운영하고 있으며, 진단 결과를 앱에서 조회·관리할 수 있도록 서비스를 고도화하고 있습니다. 그러나 해당 서비스는 매장 방문을 전제로 한 오프라인 중심 서비스로, **시간과 장소의 제약이 있어 사용자가 집에서 즉시 피부 상태를 확인하거나 성분 정보를 분석하고 제품을 추천받기에는 한계**가 있습니다.

이러한 서비스 환경을 바탕으로, **사용자가 스마트폰 앱만으로 언제 어디서나 피부 상태 분석, 성분 분석, 맞춤 제품 추천을 받을 수 있는 홈 기반 스킨케어 챗봇 서비스의 필요성**을 확인하였으며, 이를 기반으로 본 프로젝트를 기획·개발하게 되었습니다.

### 2.2. 프로젝트 목표

본 프로젝트는 **벡터DB 기반 챗봇 상담, 피부 이미지 분석(빠른 분석/정밀 분석), 전성분 OCR 분석을 결합한 멀티모달 스킨케어 AI 챗봇**으로, 사용자의 피부 상태를 분석하고 성분 기반 추천 포인트를 도출하여 올리브영 실상품 검증 기반 제품 추천 및 위시리스트 저장 기능, 피부 이미지 분석 결과를 기반의 피부 관리법 추천까지 제공하는 서비스 개발을 목표로 합니다.

```mermaid
graph LR
    A["📸 피부 사진 : 1장/3장"] --> B["🔬 Vision : 피부 분석"]
    C["🏷️ 전성분 : 라벨 이미지"] --> D["📝 OCR : 성분 추출"]
    E["💬 피부 고민 : 텍스트/프로필"] --> F["👤 개인화 : 컨텍스트"]
    B --> G["📦 Evidence : Bundle"]
    D --> G["📦 Evidence : Bundle"]
    F --> G["📦 Evidence : Bundle"]
    G --> H["🔍 RAG : 후보 검색"]
    H --> I["✅ 올리브영 : 웹 검증"]
    I --> J["📋 추천/리포트 : 출력"]
    J --> K["💾 위시리스트 : 저장"]
```

> ⚠️ 본 서비스는 의료 진단/치료가 아닌 **스킨케어 정보 제공** 목적입니다.

---

## 3. 수집된 데이터 및 데이터 전처리

---

### 3.1. 데이터 출처 및 수집 방식

| 데이터 유형 | 출처 및 수집 방식 | 활용 목적 |
| --- | --- | --- |
| 기능성 화장품 보고품목 | 공공 API (기능성화장품 보고품목 정보, 식약처) | 기능성화장품의 제품 목록 및 상세 정보 수집, 성분 안전성 판단 및 피부 교차 필터링 |
| 화장품 원료 성분 정보 | 공공 API (식약처 화장품 원료성분 정보) | 주의 및 제한 성분 조회 |
| 피부 질병 정보 | 대한피부과학회 웹크롤링 (비회원 공개 페이지) | 피부 질환별 상세 정보 수집 및 상담 근거 확보 |
| 피부 관련 리뷰 논문 | PubMed E-utilities API (논문 요약본) | 피부 장벽, 보습, 항노화 관련 최신 학술 근거 제공 |
| 피부 관리 가이드 | AAD(미국피부과학회) 웹 크롤링 | 피부 상태별 관리 단계 및 루틴 구성 |

※ 수집 제외 항목: 학회 회원 전용 콘텐츠, 라이선스 문제 있는 외부 사이트, 과도한 수집 부담 항목

---

### 3.2. 데이터 전처리 파이프라인

#### 3.2.1. 데이터 전처리 과정

- 각 데이터 출처별 문서를 다음과 같이 분류·정리
  - 피부 가이드 (guide) : 피부 고민별 관리, 단계별 관리, 관리 루틴 구성 등
  - 성분 정보 (ingredient) : 성분명, 기능 설명, 피부 타입별 적합성, 성분 간 상호작용, 주의/제한 정보 등
  - 피부 질병 정보 (disease) : 정의, 증상, 원인, 치료, 진단, 합병증 등 상세 항목
  - 기능성화장품 보고품목 (cosmetic_product): 제품명, 효능·효과, 용법·용량, 주의사항, SPF·PA 지수, 방수 여부 등

- 문서 내 청킹 처리: 대용량 문서는 최대 1,000자 단위로 분할하여 RAG(검색 기반 질의응답) 최적화
- 태깅 자동화: 키워드 매칭 방식으로 피부 고민, 성분명, 피부 타입 등 자동 태깅 적용
- 영문 원문은 태깅 후 GPT-4.1-mini 모델을 통해 한국어 요약·번역 적용
- 저장 및 검색 최적화:
  - 통일 JSONL 스키마로 정형화 후 ChromaDB에 저장
  - 한국어 특화 임베딩(jhgan/ko-sroberta-multitask) 사용
  - 중복 제거 및 메타데이터 기반 다중 필터링 적용
  - 기능성화장품 보고품목: 염모, 제모, 탈모, 샴푸 등 피부 분석 목적에 맞지 않는 헤어·두피 제품을 키워드 필터링으로 제거
  - 기능성화장품 보고품목: CANCEL_APPROVAL_YN 값이 'Y'인 제품을 제외하여 최신 유효 데이터만

#### 3.2.2. 주요 전처리 시스템 및 스키마

- 통일된 JSONL 스키마

```json
{
  "id": "고유 문서 ID",
  "doc_type": "guide | ingredient | disease | cosmetic_product",
  "category": "대분류 주제",
  "skin_type": ["피부 타입 리스트"],
  "concern_tag": ["피부 고민 키워드"],
  "ingredient_tag": ["주요 성분명"],
  "source": "데이터 출처",
  "chunk_index": "분할 순서",
  "content": "전처리된 텍스트 본문"
}
```

---

### 3.3. 수집 데이터 현황

<div align="center">
  <div style="display: flex; flex-wrap: wrap; gap: 12px;">
    <div>
      <h4 align="center">피부 가이드 (guide)</h4>
      <table>
        <thead>
          <tr>
            <th>카테고리</th>
            <th>상태</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>피부 타입별 관리</td><td>완료</td></tr>
          <tr><td>피부 장벽 관리</td><td>완료</td></tr>
          <tr><td>여드름/트러블 관리</td><td>완료</td></tr>
          <tr><td>미백·색소 관리</td><td>완료</td></tr>
          <tr><td>안티에이징 관리</td><td>완료</td></tr>
          <tr><td>민감 피부 진정 관리</td><td>완료</td></tr>
          <tr><td>모공 관리</td><td>완료</td></tr>
          <tr><td>단계별 관리 (mild→severe)</td><td>완료</td></tr>
          <tr><td>아침/저녁 데일리 루틴</td><td>완료</td></tr>
          <tr><td>주기적 관리 루틴</td><td>완료</td></tr>
          <tr><td>피해야 할 습관</td><td>완료</td></tr>
        </tbody>
      </table>
    </div>
    <div>
      <h4 align="center">성분 정보 (ingredient)</h4>
      <table>
        <thead>
          <tr>
            <th>항목</th>
            <th>상태</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>성분명·기능 설명</td><td>완료</td></tr>
          <tr><td>피부 타입별 적합성 설명</td><td>완료</td></tr>
          <tr><td>성분 간 시너지/충돌 관계</td><td>완료</td></tr>
          <tr><td>농도별 효과 차이 설명</td><td>완료</td></tr>
          <tr><td>주의/제한 성분 여부 및 이유</td><td>완료</td></tr>
          <tr><td>부작용 가능성</td><td>완료</td></tr>
        </tbody>
      </table>
    </div>
    <div>
      <h4 align="center">피부 질병 정보 (disease)</h4>
      <table>
        <thead>
          <tr>
            <th>항목</th>
            <th>상태</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>피부 질병별 상세 설명</td><td>완료</td></tr>
        </tbody>
      </table>
    </div>
    <div>
      <h4 align="center">화장품(제품) 목록 (cosmetic_product)</h4>
      <table>
        <thead>
          <tr>
            <th>항목</th>
            <th>상태</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>기능성 화장품 보고 품목</td><td>완료</td></tr>
        </tbody>
      </table>
    </div>
  </div>

  <h3>태그별 수집 개수</h3>
  <img src="assets/vector_data.png"  />
</div>

---

## 4. 기능 및 모델/파이프라인 설계

### 4.1. 핵심 기능 요약

| 기능 | 설명 | 사용 모델/기술 |
| :-: | :-- | :-- |
| 🔬 빠른 분석 | 정면 사진 1장 → 수분/탄력/주름/모공/색소 5개 항목 정량 분석 | ResNet50 (Fast Model) |
| 🔬 정밀 분석 | 정면+좌+우 3장 → 부위별(이마/볼/턱/눈가) 13개 지표 정밀 분석 | ResNet50 + AttentionFusion (Deep Model) |
| 🏷️ 성분 분석 | 화장품 전성분 라벨 사진 → OCR 추출 → 피부타입 맞춤 성분 해석 | Qwen2.5-VL 7B |
| 💬 피부 상담 | 자연어 질문 → RAG 기반 근거 답변 (루틴/성분/고민) | GPT-4.1-mini + ChromaDB |
| 🛒 제품 추천 | RAG 후보 → 올리브영 실상품 URL 검증 → 검증된 제품만 추천 | GPT-4.1-mini + Tavily |
| 📸 얼굴 검증 | 업로드 이미지가 사람 얼굴인지 + 3장 순서 검증 | GPT-4.1-mini (Vision) |
| 🤖 intent 라우팅 | 사용자 입력을 11개 intent로 분류 (비로그인/회원 분기) | GPT-4.1-mini |
| 💾 위시리스트 | 추천 제품 저장/조회/삭제 | MySQL/MariaDB |

## 4.2. 피부 분석 딥러닝 모델

### 데이터셋

| 항목 | 내용 |
|:---:|:---|
| 출처 | [AI Hub — 한국인 피부상태 측정 데이터](https://www.aihub.or.kr/aihubdata/data/view.do?dataSetSn=71645) |
| 라벨 구조 | 얼굴 9개 Area(0~8)별 JSON — 전문 장비 측정값(수분/탄력/주름Ra/모공/색소) + 전문가 등급(0~6) |
| 정규화 | 고정 분모 방식 (moisture /100, R2 그대로, Ra /50, pore /2500~2600, count /350) |

### 학습 환경

| 항목 | Fast Model | Deep Model |
|:---:|:---:|:---:|
| GPU | RunPod RTX 5090 × 5 | RunPod RTX 5090 × 5 |
| 병렬화 | DataParallel + GPU별 Area 분산 | GPU별 Area 분산 (spawn) |
| 이미지 크기 | 128 × 128 | 256 × 256 |
| Batch Size | 32 × GPU수 (자동 스케일) | 32 |
| Epochs | 100 (Early Stop 30) | 100 (Early Stop 30) |
| Precision | FP16 (Mixed Precision) | FP16 (Mixed Precision) |

---

### 4.2.1. Fast Model (빠른 분석)

#### 개요

정면 이미지 **1장**으로 수분·탄력·주름·모공·색소 5가지 피부 지표를 0.5초 내에 측정합니다. 각 얼굴 영역(Area)별로 독립된 ResNet50 모델이 회귀(수치)와 분류(등급)를 동시에 예측하고, 영역별 결과를 평균하여 최종 5개 항목 수치와 1~5등급을 산출합니다.

#### 모델 아키텍처

```
정면 이미지 1장
    ↓
Area별 Bbox Crop (JSON 메타데이터 기반)
    ↓
┌─────────────────────────────────────────────┐
│  Area별 SkinAreaModel (총 8개 독립 모델)     │
│                                             │
│  ResNet50 Backbone (ImageNet Pretrained)    │
│      ↓ Feature (2048-d)                    │
│      ├→ Regression Head                    │
│      │   Linear(2048,256) → ReLU           │
│      │   → Dropout(0.3)                    │
│      │   → Linear(256, reg_out) → Sigmoid  │
│      │   출력: 0~1 정규화 수치              │
│      │                                     │
│      └→ Classification Head                │
│          Linear(2048,256) → ReLU           │
│          → Dropout(0.3)                    │
│          → Linear(256, cls_out)            │
│          출력: 0~6 등급 logits             │
└─────────────────────────────────────────────┘
    ↓
Area별 수치 → 항목별 평균 집계
    ↓
5개 항목 수치(0~1) + 등급(1~5) 반환
```

#### Area별 출력 매핑

| Area | 부위 | Regression 출력 | Classification 출력 |
|:---:|:---|:---|:---|
| 0 | 색소침착 | pigmentation_count (1개) | — |
| 1 | 이마 | moisture, elasticity_R2 (2개) | forehead_wrinkle(7), forehead_pigmentation(6) |
| 2 | 미간 | — | glabellus_wrinkle (7) |
| 3 | 왼눈가 | l_perocular_wrinkle_Ra (1개) | l_perocular_wrinkle (7) |
| 4 | 오른눈가 | r_perocular_wrinkle_Ra (1개) | r_perocular_wrinkle (7) |
| 5 | 왼볼 | moisture, elasticity_R2, pore (3개) | l_cheek_pore(6), l_cheek_pigmentation(6) |
| 6 | 오른볼 | moisture, elasticity_R2, pore (3개) | r_cheek_pore(6), r_cheek_pigmentation(6) |
| 8 | 턱 | moisture, elasticity_R2 (2개) | chin_wrinkle (7) |

#### 최종 5개 항목 집계 방식

| 항목 | 사용 Area | 집계 |
|:---:|:---|:---:|
| moisture (수분) | Area 1(이마) + 5(왼볼) + 6(오른볼) + 8(턱) | 평균 |
| elasticity (탄력) | Area 1(이마) + 5(왼볼) + 6(오른볼) + 8(턱) | 평균 |
| wrinkle (주름) | Area 3(왼눈가) + 4(오른눈가) | 평균 |
| pore (모공) | Area 5(왼볼) + 6(오른볼) | 평균 |
| pigmentation (색소) | Area 0 | 단일값 |

#### 학습 설정

| 항목 | 설정 |
|:---:|:---|
| Optimizer | Adam (lr=1e-4 × GPU수, Linear Scaling Rule) |
| Weight Decay | 1e-4 |
| Loss (Regression) | L1Loss (NaN 마스킹) |
| Loss (Classification) | CrossEntropyLoss × 0.5 가중치 |
| Augmentation | RandomHorizontalFlip(0.3), ColorJitter(brightness=0.3, contrast=0.3), RandomRotation(10°) |
| Early Stopping | 30 epochs patience |

#### 평가 지표

**Regression — Validation MAE** (0~1 정규화 기준, 낮을수록 정확)

> MAE 0.07 = 예측값이 실제값에서 평균 ±7% 오차 (예: 수분 60 → 53~67 예측)

| Area | 부위 | Best val_MAE |
|:---:|:---|:---:|
| 0 | 색소침착 | **0.0615** |
| 1 | 이마 | **0.0744** |
| 3 | 왼눈가 | **0.0361** |
| 4 | 오른눈가 | **0.0343** |
| 5 | 왼볼 | **0.0734** |
| 6 | 오른볼 | **0.0730** |
| 8 | 턱 | **0.0857** |
| | **전체 평균** | **0.0626** |

#### 등급 매핑 (Sigmoid → Grade)

```python
def value_to_grade(value, n_grades=5):
    return min(int(value * n_grades) + 1, n_grades)
 0.0~0.2 → 1등급 | 0.2~0.4 → 2등급 | 0.4~0.6 → 3등급 | 0.6~0.8 → 4등급 | 0.8~1.0 → 5등급
```

#### 반환값 예시

```json
{
  "mode": "fast",
  "skin_metrics": {
    "moisture":      { "value": 0.652, "grade": 4 },
    "elasticity":    { "value": 0.621, "grade": 4 },
    "wrinkle":       { "value": 0.382, "grade": 2 },
    "pore":          { "value": 0.210, "grade": 2 },
    "pigmentation":  { "value": 0.272, "grade": 2 }
  }
}
```

- `value`: 0~1 Sigmoid 정규화 수치 (각 부위 Area 평균)
- `grade`: 1~5등급 (5가 최고)

---

### 4.2.2. Deep Model (정밀 분석)

#### 개요

정면(F) + 좌측(L) + 우측(R) **3장**의 이미지를 입력받아 부위별 13개 정밀 측정값, 10개 등급, 항목별 신뢰도를 산출합니다. 핵심 설계 결정은 **Regression과 Classification의 인코더를 분리**한 것입니다. 수치 측정값은 전문 장비가 정면(F) bbox 기반으로 측정하므로 F 이미지만 사용하고, 등급 판정은 다각도 정보가 유리하므로 F+L+R을 Attention Fusion으로 융합합니다.

#### 모델 아키텍처 (v4: Triple-Encoder Attention Fusion)

```
정면(F) + 좌측(L) + 우측(R) 이미지 3장
    ↓
Area별 Bbox Crop
    ↓
┌──────────────────────────────────────────────────────────────┐
│  Area별 DeepAreaModel                                        │
│                                                              │
│  ┌─ Regression Branch (F만) ──────────────────────────────┐  │
│  │  ResNet50 Encoder (F)                                  │  │
│  │      ↓ Feature (2048-d)                               │  │
│  │  Linear(2048,512) → BN → ReLU → Dropout(0.4)         │  │
│  │  → Linear(512,256) → ReLU → Dropout(0.4)             │  │
│  │  → Linear(256, reg_out)                               │  │
│  │  출력: 0~1 정규화 수치                                 │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ Classification Branch (F+L+R Attention Fusion) ───────┐  │
│  │  ResNet50 Shared Encoder                               │  │
│  │      F → feat_F (2048-d)                              │  │
│  │      L → feat_L (2048-d)                              │  │
│  │      R → feat_R (2048-d)                              │  │
│  │          ↓                                            │  │
│  │  ┌─ AttentionFusion ─────────────────────────────┐    │  │
│  │  │  concat(F,L,R) → Linear(6144,3) → Softmax    │    │  │
│  │  │  = 가중치 w_F, w_L, w_R                       │    │  │
│  │  │  fused = w_F·F + w_L·L + w_R·R               │    │  │
│  │  │  → Linear(2048,512) → BN → ReLU → Drop(0.4)  │    │  │
│  │  └───────────────────────────────────────────────┘    │  │
│  │          ↓ (512-d)                                    │  │
│  │  Linear(512,256) → ReLU → Dropout(0.4)               │  │
│  │  → Linear(256, cls_out)                               │  │
│  │  출력: 0~6 등급 logits                                │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

**v4 핵심 설계 의도:**

| 설계 결정 | 이유 |
|:---|:---|
| Regression은 F(정면)만 사용 | 전문 장비 측정값(수분, 탄력 등)이 정면 bbox 기반이므로 동일 앵글이 최적 |
| Classification은 F+L+R Fusion | 등급 판정은 여러 각도에서 본 종합 정보가 더 정확 |
| Attention 방식 가중 합산 | 단순 concat/평균 대비 각 각도의 기여도를 학습, 품질 낮은 사진 자동 감쇠 |
| 인코더 가중치 공유 (Classification) | F/L/R에 동일 ResNet50을 적용하여 파라미터 효율 + 일관된 피처 공간 |

#### 학습 설정

| 항목 | 설정 |
|:---:|:---|
| Optimizer | Adam (lr=1e-4, betas=(0.9, 0.999), weight_decay=0) |
| LR Schedule | Warmup 5 epochs → Cosine Annealing (min_factor=0.01) |
| Loss (Regression) | **CharbonnierLoss** (ε=1e-6) — L1보다 이상치에 강건하고 L2보다 스파이크에 둔감 |
| Loss (Classification) | **FocalLoss** (α=1, γ=3) × 0.5 가중치 — 클래스 불균형(등급 0~6) 대응 |
| Gradient Clipping | max_norm=1.0 |
| Sampler | **WeightedRandomSampler** — 소수 등급 과소대표 방지 |
| Augmentation | RandomHorizontalFlip(0.3), ColorJitter(0.15/0.15/0.1/0.05), RandomAffine(5°, translate=2%) |
| Early Stopping | 30 epochs patience |

#### Loss 함수 상세

**CharbonnierLoss (Regression)**
```
L(pred, target) = mean( sqrt( (pred - target)² + ε² ) )
```
L1Loss의 smooth 버전으로, 원점 근처에서 미분 가능하여 학습이 안정적이고, L2Loss 대비 이상치에 덜 민감합니다.

**FocalLoss (Classification)**
```
FL(p_t) = -α × (1 - p_t)^γ × log(p_t)
```
γ=3으로 설정하여 쉬운 샘플(높은 확신)의 loss를 크게 줄이고, 어려운 샘플(소수 등급)에 집중합니다. 피부 등급 데이터는 중앙값 등급에 편중되는 경향이 있어 이를 보완합니다.

#### 평가 지표

Deep Model은 수치(수분, 탄력, 주름Ra 등)와 등급(주름, 모공, 색소 등)을 동시에 예측하므로, **수치 항목은 MAE**, **등급 항목은 ±1 정확도**로 각각 평가합니다.

**Regression — Validation MAE** (0~1 정규화 기준)

> MAE 0.05 = 예측값이 실제값에서 평균 ±5% 오차 (예: 수분 65 → 60~70 예측)

| Area | 부위 | Best val_MAE |
|:---:|:---|:---:|
| 0 | 색소침착 | **0.0904** |
| 1 | 이마 | **0.0799** |
| 3 | 왼눈가 | **0.1055** |
| 4 | 오른눈가 | **0.0826** |

**Classification — ±1 정확도** (예측 등급이 실제 등급과 1단계 이내일 확률)

> ±1 정확도 90% = 100명 중 90명은 실제 등급 ±1 이내로 예측

| Area | 부위 | ±1 정확도 |
|:---:|:---|:---:|
| 1 | 이마 | **93.5%** |
| 2 | 미간 | **79.4%** |
| 3 | 왼눈가 | **90.0%** |
| 4 | 오른눈가 | **69.2%** |

#### 출력 구조

Deep Model은 3가지 정보를 반환합니다:

| 필드 | 설명 | 예시 |
|:---|:---|:---|
| `measurements` | 실제 단위로 역정규화된 수치 13개 | 수분 0~100, 탄력 0~1, 주름Ra 0~50, 모공 0~2600, 색소 0~350 |
| `grades` | 전문가 등급 기준 분류 10개 | 0~6등급 (0=최저) |
| `reliability` | 항목별 예측 신뢰도 | high / medium / low / very_low |

#### 반환값 예시

```json
{
  "mode": "deep",
  "measurements": {
    "forehead_moisture": 65.2,
    "l_cheek_moisture": 70.1,
    "r_cheek_moisture": 68.5,
    "chin_moisture": 55.3,
    "forehead_elasticity_R2": 0.621,
    "l_cheek_elasticity_R2": 0.587,
    "r_cheek_elasticity_R2": 0.563,
    "chin_elasticity_R2": 0.41,
    "l_perocular_wrinkle_Ra": 18.5,
    "r_perocular_wrinkle_Ra": 20.1,
    "pigmentation_count": 95.0,
    "l_cheek_pore": 2.0,
    "r_cheek_pore": 2.0
  },
  "grades": {
    "forehead_wrinkle": 1,
    "glabellus_wrinkle": 2,
    "l_perocular_wrinkle": 3,
    "r_perocular_wrinkle": 3,
    "l_cheek_pore": 2,
    "r_cheek_pore": 2,
    "l_cheek_pigmentation": 2,
    "r_cheek_pigmentation": 3,
    "chin_wrinkle": 1,
    "forehead_pigmentation": 1
  },
  "reliability": {
    "forehead_moisture": "medium",
    "forehead_elasticity_R2": "high",
    "l_perocular_wrinkle_Ra": "low"
  }
}
```

---

### 4.2.3. Fast vs Deep 비교 요약

| | Fast Model | Deep Model |
|:---:|:---:|:---:|
| **입력** | 정면 1장 | 정면 + 좌측 + 우측 3장 |
| **이미지 크기** | 128 × 128 | 256 × 256 |
| **아키텍처** | Area별 ResNet50 (Single Encoder) | Area별 ResNet50 + AttentionFusion (Triple Encoder) |
| **Regression** | L1Loss + Sigmoid 출력 | CharbonnierLoss + Linear 출력 |
| **Classification** | CrossEntropyLoss | FocalLoss + WeightedSampler |
| **출력 수치** | 5개 항목 (영역 평균) | 13개 부위별 측정값 |
| **출력 등급** | 1~5등급 (5개 항목) | 0~6등급 (10개 부위) |
| **신뢰도** | 없음 | 항목별 high/medium/low/very_low |
| **추론 속도** | ~0.5초 | ~2초 |
| **평균 MAE** | 0.0626 | 0.0896 |
| **용도** | 빠른 피부 상태 스크리닝 | 부위별 정밀 분석 + 좌우 비교 |

### 4.2.4. 피부타입 판정

두 모델 모두 수치 예측 후, **규칙 기반 알고리즘**으로 5가지 피부타입(건성/지성/복합성/중성/민감성)을 확정합니다. LLM이 아닌 수치 기반으로 판정하여 일관성을 보장합니다.

**Fast Model 판정 기준 (0~1 Sigmoid 수치 기반):**

| 피부타입 | 판정 조건 |
|:---:|:---|
| 민감성 | elasticity ≤ 0.46 AND pigmentation ≥ 0.50 AND wrinkle ≥ 0.50 |
| 건성 | moisture ≤ 0.46 AND pore ≤ 0.48 |
| 지성 | pore ≥ 0.48 AND pigmentation ≥ 0.50 AND moisture > 0.46 |
| 복합성 | moisture ≤ 0.48 AND pore ≥ 0.46 (건조+지성 공존) |
| 중성 | 전반적 양호, 극단 항목 없음 |

**Deep Model 판정 기준 (실제 측정값 기반):**

| 피부타입 | 판정 조건 |
|:---:|:---|
| 민감성 | 평균 탄력 ≤ 0.48 AND (평균 주름Ra ≥ 22 OR 색소 ≥ 120) |
| 건성 | 건조 부위 3곳 이상 AND 평균 탄력 ≤ 0.50, 또는 평균 수분 ≤ 53 |
| 지성 | 평균 모공 ≥ 900 AND 평균 수분 ≥ 62 |
| 복합성 | 좌우 볼 수분 차이 ≥ 12, 또는 최대 모공 ≥ 900 AND 최소 수분 ≤ 52 |
| 중성 | 평균 수분 ≥ 60 AND 평균 탄력 ≥ 0.50 AND 평균 모공 ≤ 800 |

### 4.3. 성분 OCR & 성분 분석

#### 4.3.1. 모델 정보

|    항목     | 내용                                                  |
| :---------: | :---------------------------------------------------- |
| 베이스 모델 | Qwen/Qwen2.5-VL-7B-Instruct                           |
|  모델 유형  | Vision-Language Model (VLM)                           |
|  파라미터   | 7B                                                    |
|   정밀도    | float16 + Flash Attention 2                           |
|    VRAM     | ~15GB _(입력 해상도/visual token budget에 따라 변동)_ |
|  추론 환경  | NVIDIA RTX 5090 (RunPod)                              |
|  라이선스   | Apache-2.0 _(상업적 사용 가능)_                       |

#### 4.3.2. 핵심: OCR이 아닌 VLM 방식

기존 OCR(Tesseract, PaddleOCR)은 "글자를 읽는" 도구에 가깝고, 본 시스템은 이미지의 **맥락과 의미를 이해**하여 전성분만 골라냅니다.  
`[전성분]` 라벨을 시각적으로 인식하고, 마케팅 문구/설명 문장과 성분 목록을 **의미 차원에서 구분**하며, 곡면·그림자·작은 글씨에도 상대적으로 강건합니다.

#### 4.3.3. 왜 VLM이 전성분에 유리한가?

- **레이아웃/문서형 이미지에 강함**: 전성분은 “문서/라벨” 형태로 배치되는 경우가 많아, 문서형 시각 질의응답(DocVQA) 성격에 가까움
- **규칙 기반 후처리 의존도 감소**: “전성분 구간만 추출”을 정규식/좌표 규칙에만 맡기지 않고, 모델이 의미적으로 판별
- **속도-정확도 튜닝 가능**: 입력 해상도(visual token budget)를 제한해 처리시간/VRAM을 조절 가능 _(품질 ↔ 속도 트레이드오프)_

#### 4.3.4. Flash Attention 2 사용 이유 & 주의사항

- **이유**: 긴 컨텍스트·멀티모달 입력에서 메모리/속도 효율 개선
- **주의**: FA2는 일반적으로 `float16/bfloat16` 설정이 필요합니다. dtype 미설정/FP32로 동작하면 경고 또는 성능 저하/오류가 발생할 수 있어, 추론 초기화 시 dtype을 명시합니다.

#### 4.3.5. 성능 비교 (vs 기존 OCR)

|     평가 항목      | Tesseract OCR | PaddleOCR + 후처리 | **본 모델 (VLM)** |
| :----------------: | :-----------: | :----------------: | :---------------: |
|  곡면 텍스트 처리  |       ✗       |         △          |       **✓**       |
| 마케팅 문구 필터링 |       ✗       |   △ (규칙 기반)    | **✓ (의미 이해)** |
|  성분 분리 정확도  |       ✗       |  △ (오분리 발생)   |       **✓**       |
|   평균 처리 속도   |     0.5초     |      0.5~1초       |     **2~5초**     |

#### 4.3.6. 정확도 (3종 테스트 이미지 기반)

|         지표         |   결과   |
| :------------------: | :------: |
| 성분 검출률 (Recall) | **~95%** |
|  정밀도 (Precision)  | **~98%** |
|  마케팅 문구 필터율  | **~99%** |
|   성분 분리 정확도   | **~93%** |

> ⚠️ 3종 테스트 이미지 기반 추정치이며, 이미지 품질(해상도, 조명, 초점)에 따라 달라질 수 있습니다.

#### 4.3.7. 파이프라인 흐름

1. **성분 OCR(VLM)**: 이미지 → 전성분 텍스트/리스트 추출
2. **정규화(Normalization)**: 쉼표/중복/특수문자 제거, INCI 유사 표기 통일(가능한 범위)
3. **성분 매칭/분류**: 사용자 피부타입/고민과 매칭하여
   - 적합 성분 / 주의 성분 / 비추천 성분으로 태깅
4. **LLM 설명 생성**: 성분별 기능/주의사항을 자연어로 요약하여 사용자에게 제공

---

### 4.4. 제품 추천 (올리브영 검증)

#### 4.4.1 개요: “추천”이 아니라 “검증된 추천”

- 단순 웹검색 결과를 그대로 추천하지 않고, **올리브영 상품 상세 URL**로 실재성이 검증된 제품만 추천합니다.
- URL이 확인되지 않은 제품은 **절대 추천하지 않음** _(안전장치/신뢰성 핵심 정책)_

#### 4.4.2. 추천 파이프라인 (3-Stage)

1. **1차 후보 생성: RAG(ChromaDB)**
   - 제품/가이드 문서에서 후보를 검색해 “추천 후보 리스트” 구성
2. **2차 검증: Tavily 웹 검색**
   - 후보 제품명이 실제 올리브영에 존재하는지 웹에서 확인
3. **3차 생성: 검증 통과 제품만 LLM 입력**
   - 검증된 제품(상품 상세 URL 포함)만 근거로 추천 답변 생성

#### 4.4.3. URL 검증 정책(권장 명시)

- **Allowlist**: “올리브영 상품 상세” 패턴만 통과
  - 예: `.../store/goods/getGoodsDetail.do?goodsNo=...`
- **Reject**: 기획전/브랜드관/콘텐츠(매거진/셔터 등) URL은 상품 상세가 아니므로 제외
- **(선택) 2차 실재성 체크**: 후보 URL의 페이지에서 상품명/가격/옵션 등 핵심 요소 존재 여부 확인

#### 4.4.4. Tavily 검색 전략(2단계 운영)

- **정밀 단계(상품 상세 우선)**: `브랜드 + 제품명 + getGoodsDetail` 등으로 상품 상세 URL 우선 확보
- **완화 단계(폴백)**: 상품 상세가 안 잡히면 카테고리/라인 단위로 넓혀 후보를 확보한 뒤, 위 URL 정책으로 재필터링

> 이 2단계 전략을 통해 “기획전 링크만 잔뜩 걸리는 문제”를 구조적으로 완화합니다.

## 4.5. LangGraph 파이프라인

### 4.5.1. 개요

사용자 메시지가 입력되면 LangGraph 기반의 **6-노드 DAG(방향 비순환 그래프)** 가 순차·병렬로 실행되어 최종 응답을 생성합니다. 기존 단일 `pipeline.py`의 절차적 흐름을 **선언적 그래프**로 전환하여, 각 노드의 역할을 분리하고 조건부 엣지로 불필요한 처리를 건너뛸 수 있도록 설계했습니다.

### 4.5.2. 그래프 흐름

```
                        START
                          │
                   ┌──────┴──────┐
                   │  route_node │  GPT-4.1-mini로 intent 분류
                   └──────┬──────┘
                          │
                  route_condition 분기
                   ╱                ╲
          "instant"                  "continue"
              │                          │
             END                 ┌───────┴───────┐
     (greeting,                  │ context_node  │  프로필 로드 + 맥락 판단
      out_of_domain,             └───────┬───────┘
      login_required,                    │
      ask_for_context)          context_condition 분기
                                 ╱                ╲
                        "instant"                  "continue"
                            │                          │
                           END                 ┌───────┴───────┐
                    (맥락 부족 역질문)           │  vision_node  │  Fast/Deep 모델 추론
                                               └───────┬───────┘
                                                       │
                                               ┌───────┴───────┐
                                               │  search_node  │  RAG + Tavily 병렬
                                               └───────┬───────┘
                                                       │
                                               ┌───────┴───────┐
                                               │   llm_node    │  GPT-4.1-mini 답변 생성
                                               └───────┬───────┘
                                                       │
                                               ┌───────┴───────┐
                                               │ validate_node │  스키마 검증 + DB 저장
                                               └───────┬───────┘
                                                       │
                                                      END
```

### 4.5.3. 노드 상세

#### route_node — Intent 분류 (1~3초)

| 항목 | 내용 |
|:---|:---|
| **역할** | 사용자 메시지를 14개 intent 중 하나로 분류 |
| **모델** | GPT-4.1-mini (temperature=0.0, JSON mode) |
| **분기** | 비로그인(`_llm_decide_guest`) / 회원(`_llm_decide_member`) 별도 프롬프트 |
| **폴백** | LLM 실패 시 키워드 기반 규칙 라우터로 자동 전환 |
| **출력** | `RouteDecision(intent, needs_vision, needs_rag, needs_product, needs_context_check)` |

**Intent 분류 체계 (14개)**

| 분류 | Intent | 설명 | 실행 노드 |
|:---|:---|:---|:---|
| 즉시 응답 | `greeting` | 인사/잡담 | route_node에서 END |
| | `out_of_domain` | 피부 무관 질문 | route_node에서 END |
| | `login_required` | 비회원 분석 요청 | route_node에서 END |
| | `ask_for_context` | 피부 정보 부족 → 역질문 | route_node에서 END |
| | `ask_for_category` | 제품 종류 미특정 → 역질문 | route_node에서 END |
| | `ask_for_skin_info` | 피부타입 미수집 → 역질문 | route_node에서 END |
| 일반 상담 | `general_advice` | 피부 관리법/일반 지식 | context → search(RAG) → llm |
| | `routine_advice` | 스킨케어 루틴 추천 | context → search(RAG) → llm |
| | `medical_advice` | 피부과 상담 권고 | context → search(RAG) → llm |
| | `ingredient_question` | 화장품 성분 질문 | context → search(RAG) → llm |
| 제품 추천 | `product_recommend` | 올리브영 제품 추천 | context → search(Tavily) → llm |
| | `routine_and_product` | 루틴 + 제품 동시 | context → search(RAG+Tavily 병렬) → llm |
| 피부 분석 | `skin_analysis_fast` | 빠른 분석 (1장) | context → vision → search(RAG) → llm |
| | `skin_analysis_deep` | 정밀 분석 (3장) | context → vision → search(RAG) → llm |

**LLM 라우터 후처리 (오분류 보정)**

LLM이 intent를 반환한 후, 규칙 기반 후처리로 일관성을 보장합니다:

- **피부타입 선언 감지**: "지성이야", "복합성 피부" 같은 짧은 메시지는 이전 대화 맥락의 intent를 이어받기 (루틴 → `routine_advice`, 제품 → `product_recommend`)
- **루틴 우선 판단**: "루틴", "관리법" 키워드가 포함되면 `ask_for_category`가 아닌 `routine_advice`로 강제
- **맥락 부족 보정**: `product_recommend`인데 피부 정보 없으면 `ask_for_context`로, 카테고리 없으면 `ask_for_category`로 전환
- **회원 프로필 반영**: DB에 피부타입/고민이 저장되어 있으면 LLM 판단과 별개로 맥락 있음으로 처리

---

#### context_node — 프로필 로드 + 맥락 판단 (~0초)

| 항목 | 내용 |
|:---|:---|
| **역할** | DB에서 사용자 프로필 로드, 맥락 부족 시 역질문 반환 |
| **회원** | DB에서 skin_type, concern, age, gender, 최근 분석 이력 조회 |
| **비회원** | chat_history에서 임시 프로필 구성 (피부타입/고민 추출) |
| **출력** | `user_profile`, `instant_response`(역질문 시), `guest_upsell`(회원가입 유도 플래그) |

**비회원 2단계 역질문 로직**

```
1단계: needs_context_check=True이고 피부 맥락 없음
  → "어떤 피부 타입이나 고민에 맞는 제품을 찾고 계신가요?" (즉시 END)

2단계: 개인화가 필요한 질문(관리법, 루틴, 제품)인데 피부타입 미수집
  → "답변드리기 전에 먼저 피부 타입을 알려주시면 더 정확한 정보를 드릴 수 있어요" (즉시 END)

통과: 일반 지식 질문(성분 효능, 원인 설명 등)은 피부타입 없이 바로 답변 진행
```

비로그인 사용자가 개인화가 필요한 질문을 하면 역질문 후 END로 분기하고, 답변이 제공된 경우에는 `guest_upsell=True` 플래그를 설정하여 validate_node에서 회원가입 유도 문구를 자동 추가합니다.

---

#### vision_node — 피부 분석 모델 추론

| 항목 | 내용 |
|:---|:---|
| **역할** | Fast/Deep 모델 추론 또는 성분 OCR(VLM) 실행 |
| **실행 조건** | `needs_vision=True`인 intent만 (skin_analysis_fast, skin_analysis_deep, ingredient_analysis) |
| **Fast** | 정면 1장 → Area별 ResNet50 → 5개 항목 수치 + 등급 (~0.5초) |
| **Deep** | 정면+좌+우 3장 → Area별 ResNet50 + AttentionFusion → 13개 수치 + 10개 등급 + 신뢰도 (~2초) |
| **성분 OCR** | Qwen2.5-VL-7B로 전성분 이미지에서 성분명 추출 |
| **출력** | `vision_result` (skin_metrics / measurements+grades+reliability / ingredients) |

`needs_vision=False`인 일반 상담/제품 추천 intent에서는 이 노드를 통과(pass-through)합니다.

---

#### search_node — RAG + Tavily 검색 (0.3~5초)

| 항목 | 내용 |
|:---|:---|
| **역할** | intent별 필요한 검색을 실행하여 LLM에 전달할 근거 자료 수집 |
| **RAG** | ChromaDB 벡터 검색 — 피부 가이드, 성분 DB, 질환 정보, 화장품 데이터 |
| **Tavily** | 올리브영 실시간 제품 검색 (이름, 가격, URL, 성분) |
| **병렬** | `needs_rag + needs_product` 동시 True → ThreadPoolExecutor로 병렬 실행 |
| **출력** | `rag_passages`, `oliveyoung_products` |

**intent별 검색 조합**

| Intent | RAG | Tavily | 비고 |
|:---|:---:|:---:|:---|
| general_advice, routine_advice | ✔️ | — | 가이드/질환 문서 검색 |
| medical_advice | ✔️ | — | 질환 문서 중심 |
| ingredient_question | ✔️ | — | 성분/화장품 문서 검색 |
| product_recommend | — | ✔️ | 올리브영 실시간 검색 |
| routine_and_product | ✔️ | ✔️ | **병렬 실행** |
| skin_analysis_fast/deep | ✔️ | — | 수치 기반 피부타입 → RAG 쿼리 자동 생성 |

**분석 intent 특별 처리**

피부 분석 시 search_node는 vision_result의 수치로 **규칙 기반 피부타입을 확정**한 뒤, 이를 RAG 쿼리에 반영합니다. DB 프로필의 피부타입은 의도적으로 무시하여, 현재 분석 수치에 기반한 객관적인 정보를 검색합니다.

```python
# 예: Fast Model 수치 → 피부타입 확정 → RAG 쿼리
vision_result["determined_skin_type"] = "복합성"
→ RAG 쿼리: "복합성 피부 관리 루틴 스킨케어"
```

---

#### llm_node — LLM 답변 생성 (5~15초)

| 항목 | 내용 |
|:---|:---|
| **역할** | 확정된 피부타입 + 수치 + RAG/Tavily 결과를 종합하여 최종 답변 생성 |
| **모델** | GPT-4.1-mini |
| **입력** | intent, user_text, user_profile, vision_result, rag_passages, oliveyoung_products, chat_history |
| **프롬프트** | intent별 전문 프롬프트 (general_chat.py, product_recommend.py, skin_analysis.py 등) |
| **출력** | `llm_output` (chat_answer, summary, observations, recommendations, products, skin_type 등) |

intent에 따라 다른 시스템 프롬프트가 적용되며, 피부 분석 시에는 vision_result의 수치와 등급이 프롬프트에 직접 주입되어 LLM이 수치를 해석하고 조언을 생성합니다.

---

#### validate_node — 검증 + 후처리 + DB 저장 (~0초)

| 항목 | 내용 |
|:---|:---|
| **역할** | LLM 출력 검증, 올리브영 링크 반영, 분석 결과 DB 저장 |
| **스키마 검증** | Pydantic `validate_report()`로 JSON 구조 검증 + 자동 복구 |
| **올리브영 링크** | Tavily 검색 결과와 LLM 추천 제품을 fuzzy 매칭하여 구매 URL 반영 |
| **수치 정규화** | Fast/Deep 원시 수치 → 0~100 통합 스코어 + 5단계 라벨(매우 양호~개선 필요) |
| **DB 저장** | 분석 intent이고 vision_result 있을 때 → analysis 테이블에 정규화된 결과 저장 |
| **회원가입 유도** | `guest_upsell=True`이면 답변 끝에 회원가입 유도 문구 자동 추가 |
| **출력** | `report` (최종 응답 JSON) |

**올리브영 링크 반영 로직**

```
1. Tavily 검색 결과에서 URL이 있는 제품만 유효 제품(valid_oy)으로 선별
2. LLM이 추천한 제품명과 valid_oy를 fuzzy 매칭 (정확 → 부분 포함 순)
3. 매칭 성공 → LLM 제품에 oliveyoung_url 보완
4. 매칭 실패와 무관하게 valid_oy 기준으로 구매 링크 섹션 추가
```

---

### 4.5.4. 상태 관리 (GraphState)

LangGraph의 `TypedDict` 기반 상태 객체가 노드 간 데이터를 전달합니다:

```python
class GraphState(TypedDict):
    # 입력 (불변)
    user_text: str                    # 사용자 메시지
    images: list                      # 업로드 이미지
    analysis_type: str | None         # "quick" | "detailed" | "ingredient" | None
    user_id: int | None               # 회원 ID (비로그인 시 None)
    chat_history: list                # 이전 대화 이력
    is_first_message: bool            # 채팅방 첫 메시지 여부
    image_urls: list[str]             # S3 업로드 URL

    # 중간 상태 (노드가 채움)
    route: RouteDecision | None       # route_node 출력
    instant_response: dict | None     # 즉시 응답 (있으면 END로 분기)
    user_profile: dict | None         # context_node 출력
    guest_upsell: bool                # 회원가입 유도 플래그
    vision_result: dict | None        # vision_node 출력
    rag_passages: list                # search_node RAG 결과
    oliveyoung_products: list         # search_node Tavily 결과
    llm_output: dict                  # llm_node 출력
    report: dict                      # validate_node 최종 출력
```

### 4.5.5. 조건부 엣지 (Conditional Edges)

그래프에는 2개의 조건부 분기점이 있어, 불필요한 노드 실행을 최소화합니다:

| 분기점 | 조건 | "instant" (→ END) | "continue" (→ 다음 노드) |
|:---|:---|:---|:---|
| **route_condition** | `intent ∈ {greeting, out_of_domain, login_required, ask_for_context}` | 즉시 응답 반환 | context_node로 이동 |
| **context_condition** | `instant_response ≠ None` | 역질문 반환 | vision_node로 이동 |

이를 통해 인사/도메인 외 질문은 **1개 노드만 실행**(route_node)하고, 맥락 부족 시 **2개 노드**(route + context)만 실행하여 응답 속도를 최적화합니다.

### 4.5.6. 전체 응답 시간 (예시)

| 시나리오 | 실행 노드 | 총 소요 시간 |
|:---|:---|:---:|
| "안녕" (인사) | route_node | ~1.5초 |
| "추천해줘" (맥락 부족) | route → context | ~1.5초 |
| "건성 피부 관리법" (일반 상담) | route → context → search(RAG) → llm → validate | ~12초 |
| "지성 세럼 추천" (제품 추천) | route → context → search(Tavily) → llm → validate | ~15초 |
| "루틴이랑 세럼 추천" (복합) | route → context → search(RAG+Tavily 병렬) → llm → validate | ~15초 |
| 빠른 분석 (사진 1장) | route → context → vision(0.5s) → search(RAG) → llm → validate | ~13초 |
| 정밀 분석 (사진 3장) | route → context → vision(2s) → search(RAG) → llm → validate | ~15초 |                         |

---

## 5. 시스템 아키텍처

### 5.1. 전체 아키텍처

<div align="center">
  <img src="assets\EC2_RunPodGPU_.jpg" width="1000">
</div>

### 5.2. 주요 흐름 (User Flow)

1. 사용자가 로그인 후 채팅창에서 대화 또는 분석 모드 선택
2. **빠른 분석**: 정면 사진 1장 업로드 → GPT Vision 얼굴 검증 → ResNet50 Fast Model 추론 → 피부타입 확정 → LLM 해설
3. **정밀 분석**: 정면/좌/우 3장 업로드 → GPT Vision 얼굴+순서 검증 → Deep Model 추론 → 부위별 13개 지표 + 피부타입 확정 → LLM 해설
4. **성분 분석**: 전성분 라벨 사진 업로드 → OCR 성분 추출 → 사용자 피부타입 맞춤 성분 해석
5. **제품 추천**: RAG 후보 검색 → Tavily 올리브영 검증 → 검증된 제품만 추천
6. **위시리스트**: 추천 제품 저장/조회/삭제

---

## 6. 데이터베이스 설계

ERD 링크: https://www.erdcloud.com/d/2cjZbEpqqK92Mw6AZ

<div align="center">
  <img src="assets/erd.png">
</div>

</div>

### 6.1. 주요 테이블

|    테이블     | 설명                                         |
| :-----------: | :------------------------------------------- |
|     users     | 사용자 정보 (피부타입, 피부고민, 나이, 성별) |
|  chat_rooms   | 채팅방 관리                                  |
| chat_messages | 대화 이력 저장                               |
| skin_analyses | 피부 분석 결과 (피부타입, 점수, 측정값)      |
|   wishlists   | 추천 제품 위시리스트 저장                    |

---

## 7. 디렉토리 구조

```
📦 **SKN23-3rd-3TEAM/**
├── **front/** *(React + Vite 프론트엔드)*
│   ├── index.html                          # 앱 진입점 HTML
│   ├── package.json                        # 의존성 및 스크립트
│   ├── vite.config.ts                      # Vite 빌드 설정 (alias 등)
│   ├── tsconfig.json                       # TypeScript 설정
│   ├── public/
│   │   └── favicon.icons                   # 파비콘 파일
│   └── src/
│       ├── main.tsx                        # React 앱 마운트 진입점
│       ├── vite-env.d.ts                   # Vite 환경변수 타입 정의
│       ├── app/
│       │   ├── App.tsx                     # RouterProvider 루트 컴포넌트
│       │   ├── routes.tsx                  # 전체 라우트 정의
│       │   ├── api/                        # 백엔드 API 호출 함수 모음
│       │   │   ├── authApi.ts              # 로그인·회원가입·이메일 인증·소셜 로그인
│       │   │   ├── chatApi.ts              # 채팅방 CRUD·메시지 전송·게스트 채팅
│       │   │   ├── userApi.ts              # 사용자 프로필 조회·수정·소셜 연동
│       │   │   ├── analysisApi.ts          # 피부 분석 결과 조회
│       │   │   ├── wishlistApi.ts          # 위시리스트 조회·추가·삭제
│       │   │   └── uploadApi.ts            # S3 이미지 업로드
│       │   ├── pages/                      # 라우트에 대응하는 페이지 컴포넌트
│       │   │   ├── ChatPage.tsx            # 메인 채팅 페이지 (비로그인 접근 가능)
│       │   │   ├── AnalysisPage.tsx        # 피부 분석 결과 상세 (로그인 필수)
│       │   │   ├── WishlistPage.tsx        # 위시리스트 목록 (로그인 필수)
│       │   │   ├── WishlistDetailPage.tsx  # 위시리스트 상세 (로그인 필수)
│       │   │   ├── SettingsPage.tsx        # 프로필·계정 설정 (로그인 필수)
│       │   │   ├── LoginPage.tsx           # 로그인
│       │   │   ├── SignupPage.tsx          # 회원가입
│       │   │   ├── ForgotPasswordPage.tsx  # 비밀번호 재설정
│       │   │   ├── OnboardingPage.tsx      # 신규 회원 온보딩(피부정보 입력)
│       │   │   └── OAuthCallbackPage.tsx   # 소셜 로그인 콜백 처리
│       │   └── components/                 # 재사용 가능한 UI 컴포넌트
│       │       ├── Layout.tsx              # 전체 레이아웃(사이드바 + 콘텐츠)
│       │       ├── Sidebar.tsx             # 사이드바(네비·채팅 목록·사용자 정보)
│       │       └── ui/                     # 범용 UI 원자 컴포넌트(shadcn/ui 기반)
│       │           ├── bot.tsx             # 봇 아바타 컴포넌트
│       │           ├── icon.tsx            # SVG 아이콘 래퍼
│       │           ├── loading.tsx         # 로딩 스피너
│       │           ├── use-mobile.ts       # 모바일 감지 훅
│       │           └── utils.ts            # cn() 등 유틸 함수
│       │
│       ├── assets/                         # 정적 리소스(이미지/아이콘/애니메이션)
│       │   ├── logo.png
│       │   ├── profile.png
│       │   ├── info_1.png                  # 빠른/정밀 분석 안내사항 이미지
│       │   ├── info_2.png                  # 성분 분석 안내사항 이미지
│       │   ├── bot.svg
│       │   ├── animations/                 # 애니메이션 WebM 파일
│       │   │   ├── logo_idle_1.webm
│       │   │   ├── logo_loop_1.webm
│       │   │   ├── logo_pop_1.webm
│       │   │   └── logo_text.webm
│       │   ├── icons/                      # 커스텀 아이콘 SVG 파일
│       │   │   ├── beauty.svg
│       │   │   ├── chat.svg
│       │   │   ├── wish.svg
│       │   │   ├── moisture.svg
│       │   │   └── ...
│       │   └── factorial/                  # 피부분석-추천관리법 팩토리얼 SVG 파일 (17종)
│       │       ├── antiaging.svg
│       │       ├── brightening_care.svg
│       │       ├── moisturizing_boost.svg
│       │       └── ...
│       └── styles/                         # 전역 스타일
│           ├── index.css
│           ├── tailwind.css
│           ├── theme.css
│           └── fonts.css
│
├── **back/** *(FastAPI 백엔드)*
│   ├── main.py                             # FastAPI 앱 진입점(CORS, Router 등록)
│   │
│   ├── db/                                 # 데이터베이스 계층
│   │   ├── migrations/                     # 테이블 생성/변경 SQL
│   │   │   └── 001_init_tables.sql
│   │   ├── __init__.py
│   │   ├── db_manager.py                   # DB 연결 및 공통 쿼리 실행(Base layer)
│   │   ├── models.py                       # DB 모델(User, ChatSession 등)
│   │   └── schemas.py                      # Pydantic 스키마
│   │
│   ├── routers/                            # API 엔드포인트(Controller layer)
│   │   ├── __init__.py
│   │   ├── analysis_router.py              # 피부 분석 API
│   │   ├── auth_router.py                  # 인증/토큰 API
│   │   ├── chat_router.py                  # 채팅 API
│   │   ├── deps.py                         # Depends(인증/현재 유저 등)
│   │   ├── keyword_router.py               # 키워드 API
│   │   ├── upload_router.py                # S3 업로드 API
│   │   ├── user_router.py                  # 사용자 API
│   │   └── wishlist_router.py              # 위시리스트 API
│   │
│   ├── services/                           # 비즈니스 로직(Service layer)
│   │   ├── __init__.py
│   │   ├── analysis_service.py
│   │   ├── auth_service.py
│   │   ├── chat_service.py
│   │   ├── email_service.py
│   │   ├── keyword_service.py
│   │   └── user_service.py
│   │
│   ├── vector/                             # RAG 벡터 파이프라인(수집 → 전처리 → 임베딩)
│   │   ├── assets/
│   │   │   ├── links/                      # 외부 수집 링크/검색 결과 JSON
│   │   │   │   ├── aad_skin_care_*.json
│   │   │   │   ├── derma_skin_dis_*.json
│   │   │   │   ├── pubmed_search_*.json
│   │   │   │   └── single_search.json
│   │   │   └── vector_data/                # chunk 완료 JSONL(임베딩 입력)
│   │   │       ├── aad_guides.jsonl
│   │   │       ├── derma_disease.jsonl
│   │   │       ├── mfds_ingredient.jsonl
│   │   │       ├── pubmed_skin_guides.jsonl
│   │   │       └── single_item_collection.jsonl
│   │   ├── collectors/                     # 데이터 수집 모듈(RAG 1단계)
│   │   │   ├── aad_data_to_*.py
│   │   │   ├── cosmetic_*.py
│   │   │   ├── derma_data_*.py
│   │   │   ├── mfds_ingredient_*.py
│   │   │   └── pubmed_data_*.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   └── tagging.py                  # 메타 태깅/카테고리 로직
│   │   ├── check_collection.py             # Chroma 컬렉션 확인/생성
│   │   └── vectordb_insert.py              # 임베딩 생성 후 Chroma 업로드
│   │
│   ├── ai/                                 # AI 오케스트레이션 (LangGraph 파이프라인)
│   │   ├── orchestrator/                   # 그래프 실행 엔진
│   │   │   ├── graph.py                    # LangGraph DAG 정의 및 컴파일 (6-노드 그래프)
│   │   │   ├── state.py                    # GraphState TypedDict (노드 간 공유 상태)
│   │   │   ├── router.py                   # Intent 분류기 (LLM 라우팅 + 키워드 폴백)
│   │   │   ├── context_builder.py          # 사용자 프로필 빌드 (DB 조회 + chat_history 파싱)
│   │   │   └── nodes/                      # 그래프 노드 구현체
│   │   │       ├── route.py                # [route_node] GPT-4.1-mini intent 분류 + 즉시 응답
│   │   │       ├── context.py              # [context_node] 프로필 로드 + 맥락 부족 역질문
│   │   │       ├── vision.py               # [vision_node] Fast/Deep 모델 추론 · 성분 OCR
│   │   │       ├── search.py               # [search_node] RAG + Tavily 병렬 검색 · 피부타입 확정
│   │   │       ├── llm.py                  # [llm_node] GPT 답변 생성 (intent별 프롬프트)
│   │   │       └── validate.py             # [validate_node] 스키마 검증 · 올리브영 링크 · DB 저장
│   │   │
│   │   ├── llm/                            # LLM 호출 및 프롬프트 관리
│   │   │   ├── generator.py                # generate_report() — intent별 프롬프트 조합 → GPT 호출
│   │   │   ├── validators.py               # Pydantic 기반 LLM 출력 JSON 스키마 검증
│   │   │   └── prompts/                    # intent별 시스템 프롬프트
│   │   │       ├── system_base.py          # 공통 시스템 프롬프트 (역할 정의, 응답 형식)
│   │   │       ├── skin_analysis.py        # 빠른/정밀 분석 프롬프트 (수치 해석 + 피부타입 판정)
│   │   │       ├── ingredient_chat.py      # 성분 분석 프롬프트 (전성분 OCR 결과 해석)
│   │   │       ├── product_recommend.py    # 제품 추천 프롬프트 (올리브영 제품 기반 답변)
│   │   │       └── general_chat.py         # 일반 상담 프롬프트 (관리법, 루틴, 성분 질문)
│   │   │
│   │   ├── tools/                          # 외부 도구 연동
│   │   │   ├── rag_retriever.py            # ChromaDB 벡터 검색 (가이드/성분/질환/화장품)
│   │   │   └── oliveyoung.py               # Tavily API로 올리브영 실시간 제품 검색
│   │   │
│   │   └── config/
│   │       └── settings.py                 # API 키, 모델명, 경로 등 환경 설정
│   │
│   ├── skin_ai/                            # 딥러닝 모델 추론 (Fast/Deep)
│   │   ├── fast_inference.py               # Fast Model — 정면 1장 → 5개 항목 수치+등급 (~0.5초)
│   │   ├── deep_inference.py               # Deep Model — F+L+R 3장 → 13개 수치+10개 등급+신뢰도 (~2초)
│   │   ├── checkpoint/                     # 학습 완료 모델 가중치
│   │   │   ├── fast/                       # Area별 Fast Model state_dict.bin (7개)
│   │   │   └── deep/                       # Area별 Deep Model state_dict.bin (8개)
│   │   └── ingredient_demo/
│   │       └── demo_products.json          # 성분 분석 데모용 샘플 데이터
│   │
│   ├── assets/                             # 백엔드 리소스(팀 사진, 데모)
│   │   ├── images/
│   │   └── demo/
│   │
│   └── vector_store/                       # 로컬 Chroma 영속 저장소
│       └── chroma.sqlite3
│
├── README.md
└── requirements.txt
```

---

## 8. Tech Stack

<div align="center">

| Category | Stack |
| :-: | :-- |
| **Front-End** | ![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black) ![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=black) ![vite](https://img.shields.io/badge/vite-9135FF?style=flat&logo=vite&logoColor=white) ![TailwindCSS](https://img.shields.io/badge/TailwindCSS-1572B6?style=flat&logo=tailwindcss&logoColor=white) ![RadixUI](https://img.shields.io/badge/RadixUI-161618?style=flat&logo=radixui&logoColor=white) ![shadcn/ui](https://img.shields.io/badge/shadcnui-000000?style=flat&logo=shadcnui&logoColor=white) |
| **Back-End** | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white) ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) ![Uvicorn](https://img.shields.io/badge/Uvicorn-499848?style=flat&logoColor=white) |
| **인증 / 보안** | ![JWT](https://img.shields.io/badge/JWT-000000?style=flat&logo=jsonwebtokens&logoColor=white) ![bcrypt](https://img.shields.io/badge/bcrypt-338AF0?style=flat&logoColor=white) ![Google OAuth](https://img.shields.io/badge/Google_OAuth-4285F4?style=flat&logo=google&logoColor=white) ![Naver OAuth](https://img.shields.io/badge/Naver_OAuth-03C75A?style=flat&logo=naver&logoColor=white) ![SendGrid](https://img.shields.io/badge/SendGrid-1A82E2?style=flat&logo=sendgrid&logoColor=white) |
| **Database** | ![MariaDB](https://img.shields.io/badge/MariaDB-003545?style=flat&logo=mariadb&logoColor=white) |
| **Vector DB** | ![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6B00?style=flat&logoColor=white) |
| **AI / LLM** | ![OpenAI](https://img.shields.io/badge/GPT--4o-412991?style=flat&logo=openai&logoColor=white) ![OpenAI](https://img.shields.io/badge/GPT--4o--mini-412991?style=flat&logo=openai&logoColor=white) |
| **ML / DL** | ![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat&logo=pytorch&logoColor=white) ![ResNet50](https://img.shields.io/badge/ResNet50-FF6F00?style=flat&logoColor=white) ![Qwen2.5-VL](https://img.shields.io/badge/Qwen2.5--VL-7B-blueviolet?style=flat&logoColor=white) ![HuggingFace](https://img.shields.io/badge/HuggingFace-FFD21E?style=flat&logo=huggingface&logoColor=black) |
| **RAG / Orchestration** | ![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?style=flat&logo=langgraph&logoColor=white) ![Tavily](https://img.shields.io/badge/Tavily-0066FF?style=flat&logoColor=white) ![Sentence-Transformers](https://img.shields.io/badge/Sentence--Transformers-FF6B00?style=flat&logoColor=white) ![ko-sroberta](https://img.shields.io/badge/ko--sroberta--multitask-yellow?style=flat&logoColor=white) |
| **이미지 처리** | ![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat&logo=opencv&logoColor=white) ![Pillow](https://img.shields.io/badge/Pillow-3776AB?style=flat&logo=python&logoColor=white) |
| **Infra** | ![AWS](https://img.shields.io/badge/AWS_EC2-FF9900?style=flat&logo=amazonec2&logoColor=white) ![S3](https://img.shields.io/badge/S3-FF9900?style=flat&logo=amazonec2&logoColor=white) |
| **Tools** | ![Figma](https://img.shields.io/badge/Figma-F05032?style=flat&logo=Figma&logoColor=white) ![Git](https://img.shields.io/badge/Git-F05032?style=flat&logo=git&logoColor=white) ![VS Code](https://img.shields.io/badge/VS_Code-007ACC?style=flat&logo=visual-studio-code&logoColor=white) ![RunPod](https://img.shields.io/badge/RunPod-673AB7?style=flat&logoColor=white) |

## </div>

## 9. 실행 방법

### 9.1. Backend (FastAPI)

```bash
  # back 폴더로 이동
  cd ./back
  # venv 생성
  python -m venv skin_venv
  # venv 실행 (Windows)
  skin_venv\Scripts\activate
  # venv 실행 (Mac/Linux)
  source skin_venv/bin/activate
  # 의존성 설치
  pip install -r requirements.txt
  # uvicorn 서버 실행
  uvicorn main:app --reload --port 8000
```

### 9.2. Frontend (React)

```bash
  # nodeJS 18버전 이상 필요
  node --version
  # pnpm 설치
  npm install -g pnpm
  # front 폴더로 이동
  cd ./front
  # 패키지 설치
  pnpm install
  # react 서버 실행
  pnpm dev
```

### 9.3. Environment (.env)

```
# vector DB
DATA_GO_CSMT_KEY
DATA_GO_COSMETIC_KEY
VECTOR_DATA_DIR
CHROMA_DB_PATH
CHROMA_COLLECTION

# mariadb 정보
DB_HOST
DB_PORT
DB_USER
DB_PASSWORD
DB_NAME

# JWT
JWT_SECRET_KEY

# EC2 접속 정보
SSH_HOST
SSH_PORT
SSH_USER
SSH_PKEY

# S3 정보
AWS_REGION=ap-northeast-2
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
S3_BUCKET_NAME

# API 연결 URL
VITE_API_BASE_URL=http://localhost:8000

# 임베딩 모델
EMBED_MODEL_NAME

# PubMed API
NCBI_API_KEY
PUBMED_EMAIL

# OPEN AI API KEY
OPENAI_API_KEY

# TAVILY_API_KEY
TAVILY_KEY

# VISION MODEL
VISION_MODEL_PATH

# 이메일 인증
SENDGRID_API_KEY
SENDGRID_FROM_EMAIL
EMAIL_OTP_SECRET

# Google OAuth
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI

# Naver OAuth
NAVER_CLIENT_ID
NAVER_CLIENT_SECRET
NAVER_REDIRECT_URI

# 소셜 로그인 콜백 URL
FRONTEND_BASE_URL

```

---

## 10. 화면 설계

### 10.1. 사이트 구조

```bash

On-you(온유)
   ├── chat (회원, 비회원)
   │      ├── 채팅 질문
   │      ├── 빠른 분석
   │      ├── 정밀 분석
   │      └── 성분 분석
   ├── 피부 분석
   │      ├── 현재 분석
   │      └── 비교 분석
   ├── 위시리스트
   ├── 설정
   │      ├── 프로필 (회원정보, 피부정보)
   │      └── 소셜 연동 (구글, 네이버)
   └── 로그인 (일반, 구글, 네이버)
        ├── 비밀번호 찾기 (이메일 인증)
        └── 회원가입 (이메일 인증)

```

### 10.2. 화면흐름도

<div align="center">
  <img src="assets/화면흐름도.jpg" width="80%" />
</div>

### 10.3. 와이어 프레임 (Figma):

https://www.figma.com/make/GidYts0kuhsYalIeB8HraC/Multimodal-Skin-Analysis-Chatbot?t=YhjLgI2srgQIFRuA-1

### 10.4. 인포그래픽

<div align="center">
  <img src="assets/인포그래픽_분석.png">
  <p>
    <b>🔍 분석 가이드라인</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 
  </p>
  <img src="assets/인포그래픽_전성분.png">
  <p>
    <b>🧪 전성분 추출 가이드라인</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 
  </p>

  <br><br>

  
</div>

## 11. 시연화면

<div align="center">
  <img src="assets/0_진입화면_비회원.png" />

  <details>
    <summary><b>전체 시연화면 보기</b></summary>
    <br/>
    <img src="assets/1-1_채팅_비회원.png" />
    <img src="assets/1-2_채팅_회원.png" />
    <img src="assets/1-2_채팅_회원_빠른분석.png" />
    <img src="assets/1-2_채팅_회원_정밀분석.png" />
    <img src="assets/1-2_채팅_회원_성분분석.png" />
    <img src="assets/2_피부분석_현재분석.png" />
    <img src="assets/2_피부분석_비교분석.png" />
    <img src="assets/3_위시리스트.png" />
    <img src="assets/4-1_로그인.png" />
    <img src="assets/4-2_비밀번호찾기.png" />
    <img src="assets/4-3_회원가입.png" />
    <img src="assets/5-1_설정_프로필.png" />
    <img src="assets/5-2_설정_소셜연동.png" />
  </details>
</div>

## 11.1 시연영상

<div align="center">
  <img src="assets/gif/Adobe Express - 비로그인 편집.gif">
  <img src="assets/gif/Adobe Express - 회원관리법.gif">
  <img src="assets/gif/Adobe Express - 레이저시술.gif">
  <img src="assets/gif/Adobe Express - 빠른분석.gif">
  <img src="assets/gif/Adobe Express - 정밀분석.gif">
  <img src="assets/gif/Adobe Express - 전성분추출.gif">
</div>
---

## 12. 트러블 슈팅

### 12.1. 피부타입 분류 편향 (복합성/지성 집중)

- **증상**: 다양한 얼굴 사진을 넣어도 복합성 또는 지성만 출력
- **원인**: ResNet50 Sigmoid 출력이 0.4~0.6 범위에 집중되는데, 판단 임계값이 이를 고려하지 않음
- **해결**:
  1. 모델 출력 분포에 맞춘 상대적 임계값으로 규칙 기반 판정 재설계
  2. 민감성 타입 판정 기준 추가
  3. 규칙 기반으로 확정된 피부타입을 `determined_skin_type`으로 LLM에 전달하여 LLM의 임의 변경 방지
  4. 기본값 "복합성" 제거 → 점수 기반 폴백으로 변경

### 12.2. RAG 검색 0건 문제

- **원인**: 실행 위치(cwd)에 따라 `CHROMA_DB_PATH` 상대경로가 달라져 새 vector_store가 생성
- **해결**: 프로젝트 루트 기준 절대경로 정규화 + `.env`는 루트 기준 상대경로 사용

### 12.3. OCR 모델 CPU 환경 실행 불가

- **원인**: Qwen2.5-VL 7B 모델을 RunPod GPU에서 학습했으나, 실제 서비스 환경은 CPU
- **해결**: 데모용 미리 추출된 전성분 JSON 매칭 테이블 방식으로 대체 (순서 기반 카운터)

### 12.4. LLM 응답에 JSON 구조 노출

- **증상**: 챗봇 답변에 `{"title": "수분 상태", "detail": "..."}` 형태 그대로 노출
- **해결**: 프롬프트에 `chat_answer에는 JSON 형식을 절대 포함하지 않는다` 규칙 및 구체적 예시 추가

---

## 13. 비즈니스 전략

1. **프리미엄 구독 서비스**  
   서비스를 빠른 검사(무료) / 정밀 검사(유료)로 구분합니다.  
   구독 결제를 통해 유료 회원에게는 정밀 검사 기능, 개인 정보·피부 기록 저장 확대, 개인화 추천 고도화 등 더 높은 수준의 서비스를 제공합니다.

2. **모바일 애플리케이션 확장**  
   향후 웹 서비스에서 나아가 모바일 애플리케이션으로 확장하여, 스마트폰을 통한 피부 촬영 기반 분석과 전성분 촬영(OCR) 분석을 더 편리하게 제공할 계획입니다.

3. **커뮤니티 기능 추가 및 구독 회원 혜택 확대**  
   사용자 사용 빈도와 접속률(리텐션)을 높이기 위해 커뮤니티 기능을 향후 추가합니다.  
   구독 회원에게는 전용 네임 배지, 유용한 게시글 저장, 피부 성향 테스트(피부 MBTI) 등 심화 기능을 제공하여 구독 가치를 높이고자 합니다.

4. **광고 및 제휴 기반 수익**  
   웹/앱 내 배너 광고를 도입해 광고 수익을 확보합니다.  
   또한 화장품 업체와의 제휴를 통해 쿠폰·체험단·이벤트를 제공하고, 이를 기반으로 마케팅 효과, 사용자 확장, 수익화를 함께 강화합니다.

---

## 14. 한줄 회고

- **강승원** :이번 프로젝트에서 ResNet50 기반 Fast/Deep 피부 정량분석 모델의 학습·추론·평가와 LangGraph 기반 6-노드 챗봇 파이프라인(라우팅, RAG 검색, 비로그인/회원 분기 등) 설계·구현을 담당했습니다. 멀티뷰 AttentionFusion 구조와 까다로운 부위 재학습으로 분석 성능을 안정화하는 데 집중했고, 각자의 영역을 끝까지 책임져 준 팀원들 덕분에 프로젝트를 잘 마무리할 수 있었습니다.

- **정석원** :이번 프로젝트에서 LLM 단계와 벡터DB(RAG)를 맡으면서, LLM이 의도 분류 → 근거 검색 → 답변 생성 → 검증 흐름으로 동작한다는 걸 확실히 이해하게 됐습니다. 짧은 기간인데도 각자 역할을 끝까지 책임져준 팀원들 덕분에 완성할 수 있었고, 모두 정말 고맙습니다.

- **정유선** :이번 프로젝트에서 ReactJS와 Typescript 기반 프론트엔드와 FastAPI 구축을 처음 경험하며 많은 것을 배웠습니다. 귀여운 이미지 디자인과 디자이너의 도움 덕분에 프론트 개발이 더욱 즐거웠습니다. 또한 한국어 특화 임베딩 모델(jhgan/ko-sroberta-multitask)을 활용한 데이터 수집과 벡터 임베딩 작업도 값진 경험이었습니다. 팀원들 모두가 맡은 바 최선을 다해 주셨고, 팀장님의 훌륭한 리더십 덕분에 프로젝트를 성공적으로 마무리할 수 있었습니다. 모두에게 감사드립니다.

- **송민채** :이번 프로젝트에서 저는 DB 설계, 백엔드 구조 설계, 인증 보안 구현을 맡았습니다. ERD 작성과 외래키 설정을 통해 데이터 관계를 직접 설계하고, 계층 구조로 시스템을 구성하며 이전보다 더 깊이 있게 DB 구조를 고민해볼 수 있었습니다. 또한 프론트엔드, 백엔드, LLM이 동시에 진행되는 개발 과정을 경험하며 여러 영역이 함께 맞물려 돌아간다는 점을 알게 되었습니다. 로그인 비밀번호 암호화와 해싱을 구현하기 위해 보안 내용을 찾아보면서, 이전에는 잘 알지 못했던 개념들을 새롭게 배우는 계기가 되었습니다. 이번 프로젝트를 통해 단순한 기능 구현을 넘어, 전체 흐름과 구조를 고려하며 개발하는 관점을 배우게 되었습니다.

- **이승연** :이번 프로젝트를 통해 로컬 개발 환경에서 EC2 배포와 S3 버킷 생성 및 저장까지 전체 서비스 흐름을 직접 경험할 수 있었습니다. FastAPI 기반 백엔드 개발과 MariaDB 연동을 구현하며 API 구조와 데이터 흐름에 대한 이해를 높일 수 있었습니다. 배포 과정에서 발생한 환경 변수, DB 연결, 서버 설정 오류를 해결하면서 운영 환경에 대한 감각도 한층 성장할 수 있었습니다. 또한 UI 및 인포그래픽 제작과 챗봇 브랜드 디자인에 참여하며 서비스 완성도를 높였고, 웹 서비스 디자인에 대한 이해도 함께 넓힐 수 있었습니다. 부족한 점이 많았음에도 멋진 리더십으로 이끌어주신 팀장님과 따뜻하게 응원해주신 팀원분들께 감사드립니다.
