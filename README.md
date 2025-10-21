# AI Startup Investment Evaluation Agent (RWA Tokenization Focus)
## Background

- **Objective** :  
  부동산, 미술품, 채권, 지식재산권 등 실물자산을 블록체인 상에서 **토큰화(RWA Tokenization)** 하는 스타트업의 **기술력·시장성·규제 적합성·수익성**을 종합적으로 분석하여 **투자 적합성**을 자동 평가

- **Method** :  
  LangGraph 기반 **Multi-Agent + Agentic RAG** 구조로 설계  

- **Tools** :  
  LangGraph, LangChain, Tavily Search API, OpenAI GPT-4o-mini

---
## 🎯 개요
# 🏦 RWA 멀티 에이전트 투자 분석 시스템

> **실물자산(RWA) 토큰화 스타트업을 위한 AI 기반 VC 실사 프레임워크**
LangGraph와 LLM을 활용하여 벤처캐피탈 회사가 실물자산(RWA) 토큰화에 집중하는 초기 단계 블록체인 스타트업을 자동으로 평가할 수 있도록 설계된 멀티 에이전트 시스템

## AI Agent 서비스 차별화 고민 포인트
- 1. 투자 시장 규모자체가 해외가 더 크고, 리서치에 필요한 해외 원천 글 자료가 더 풍부하다고 생각했기에 해외 글을 가져오는 이점을 챙기기 위해 Docstrings도 모두 영어로 코드를 짜서 진행
- 2. RAG를 진행할때 임베딩 모델도 한국어 모델은 선택지 폭과 성능의 옵션이 적어서 영어를 더 적합하게 사용할 수 있도록 "모델명: multilingual-e5-large"을 채택했습니다.


### 📋 목차

- [개요]
- [주요 기능]
- [기술 스택]
- [에이전트 상세]
- [시스템 아키텍처]

---

## ⚙️ 주요 기능(Feature)
### 1️⃣ 투자자 성향 평가 Agent

**투자자 리스크 프로필 기반 적응형 평가**

시스템은 5개 질문 CLI 설문조사(1-5 척도)를 통해 투자자 성향을 평가합니다:

1. 위험 선호도 (고수익 vs. 안정성)
2. 초기 단계 투자 경험
3. 수익 모델 안정성의 중요도
4. ESG 고려 우선순위
5. 성장 선호도 (급성장 vs. 안정적 성장)

**두 가지 성향 유형:**

| 투자자 유형 | Seed/Early | Regional/ESG | Growth + Partnership | Regulation/Monetization |
|-------------|------------|--------------|---------------------|------------------------|
|  **공격형** (Aggressive) | **40%** (최우선) | 15% | **35%** (중요) | 10% |
|  **보수형** (Conservative) | 10% | **30%** (ESG 중점) | 20% | **40%** (규제 중점) |


### 2️⃣ 스타트업 탐색 및 랭킹 Agent

**자동화된 데이터 수집 및 다기준 평가**

#### 프로세스

1. **웹 검색**: DuckDuckGo API로 스타트업당 5개 결과 수집
   - 공식 웹사이트
   - 뉴스 기사
   - 파트너십 공지
   - 펀딩 정보

2. **정보 추출**: LLM이 구조화된 데이터 추출
   - 웹사이트 URL
   - 지역 (미국, 유럽, 아시아)
   - 펀딩 단계 (Seed, Series A, Series B)

3. **다기준 평가** (4개 차원)

#### 평가 기준 및 가중치

| 기준 | 설명 | 가중치(공격형) | 가중치(보수형) |
|------|------|----------------|----------------|
| **Seed/Early Stage** | 혁신성, 성장 잠재력, 펀딩 수준 | 40% | 10% |
| **Regional/ESG** | 지역 확장성, ESG 연관성 | 15% | 30% |
| **Growth + Partnership** | 성장률, 전략적 제휴 | 35% | 20% |
| **Regulation/Monetization** | 규제 준수, 수익 명확성 | 10% | 40% |

#### 출력 점수

각 스타트업이 받는 점수:

| 점수 유형 | 범위 | 설명 |
|-----------|------|------|
| `total_score` | 0-100 | 4개 기준의 가중 합계 |
| `domain_fit` | 0-1 | RWA 섹터 적합도 |
| `credibility_score` | 0-1 | 시장 신뢰도 |
| `final_score` | 0-1 | 정규화된 총점 |

#### 최종 출력

- `evaluation_results`: 순위별 전체 리스트
- `current_startup_index`: 0 (1순위 선택)
- `current_startup_data`: 심층 분석 대상 스타트업 상세 데이터

---

### 3️⃣ 기술 실사 Agent

**포괄적인 기술 평가를 위한 서브그래프 아키텍처**

Agent 2는 내부 루프와 품질 게이트를 갖춘 **독립적인 LangGraph 서브그래프**입니다.

#### 아키텍처 흐름
```
0: 입력 처리 → 1: 신호 수집 → 2: 정규화 및 보강 → 3: 가드 체크
                    ↑                                      ↓
                    └──────────── 신호 없음 ───────────────┘
                                                           ↓
4: 규칙 기반 점수 → 5: 최종 점수 계산 → 6: 증거 구축 → 7: 결정 노트
                                           ↑              ↓
                                           └─ 증거 부족 ──┘
                                                          ↓
7b: 내러티브 생성 → 8: JSON 출력 → 9: 품질 게이트 → 출력
```

#### 평가 기준

| 차원 | 설명 | 가중치 |
|------|------|--------|
| **Domain Fit** (도메인 적합성) | RWA 토큰화 분야에서의 제품 포지셔닝 | 30% |
| **Tech Maturity** (기술 성숙도) | 보안성, 확장성, TRL | 25% |
| **Credibility** (신뢰도) | 기관 파트너십 (BlackRock BUIDL 등) | 25% |
| **Compliance Risk** (규제 리스크) | KYC/AML, SEC 등록, ATS 라이선스 | -20% (페널티) |
| **Ecosystem** (생태계) | TradFi/DeFi 통합 (FalconX, Fireblocks) | 10% |

#### 신호 수집

**쿼리:**
- 쿼리 1: `[회사명] [섹터]`
- 쿼리 2: `[회사명] tokenization KYC AML licensing`

**출처 분류:**

| 출처 | 설명 | 신뢰도 |
|------|------|--------|
| `site` | 공식 웹사이트 | 0.85 |
| `report` | 산업 보고서 | 0.85 |
| `press` | 뉴스 기사 | 0.70 |
| `repo` | GitHub/GitLab | 0.60 |
| `other` | 기타 출처 | 0.60 |

---

### 4️⃣ 시장 평가 Agent 3

**산업 보고서를 활용한 RAG 기반 시장 분석**

#### RAG 문서 출처

| # | 문서명 | 활용 목적 | 주요 인사이트 |
|---|--------|-----------|--------------|
| ① | **CoinGecko 2025 RWA 보고서** | 시장 규모 및 성장 데이터 | TAM: $24B → $30T 전망, 주요 플레이어: Ondo Finance, BlackRock BUIDL |
| ② | **WEF 자산 토큰화 보고서** | 기관 채택 트렌드 | 규제 명확화, TradFi 통합 |
| ③ | **Cornerstone: 금융의 신뢰** | 신뢰 레이어 분석 | 보안 표준, 기관 신뢰 |
| ④ | **자산 토큰화 심층 분석 (한국어)** | 지역 규제 | 디지털자산기본법, STO 가이드라인, 국내 컨소시엄 활동 |

#### RAG 파이프라인

1. **웹 검색**: `[스타트업명] [섹터] 시장 규모 TAM SAM SOM CAGR`
2. **문서 처리**:
   - 텍스트 분할 (chunk_size=1000, overlap=200)
   - 임베딩: `all-mpnet-base-v2` (sentence-transformers)
   - 벡터 저장소: Chroma DB (일시적, 사용 후 삭제)
3. **검색**: 상위 3개 관련 청크 (k=3)
4. **LLM 분석**: GPT-4o-mini를 통한 구조화된 출력

#### 평가 프레임워크 (Bessemer Checklist + Scorecard Method)

| 기준 | 가중치 | 분석 초점 |
|------|--------|-----------|
| **시장 성장성** (Growth Momentum) | 40% | TAM/SAM/SOM 규모, CAGR, 기관 관심도 |
| **수요 동력** (Demand Drivers) | 30% | 제품-시장 적합성, 고객 기반, 정책 지원 |
| **경쟁 강도** (Competitive Pressure) | 20% | 플레이어 수, 진입 장벽, 차별화 |
| **규제 명확성** (Regulatory Clarity) | 10% | 법적 불확실성, 운영 리스크 |

---

### 5️⃣ 경쟁사 분석 (Agent 4)

**주요 경쟁사 2-3개에 대한 SWOT 분석**

#### 프로세스

1. **웹 검색**: `[스타트업명]의 [섹터] 주요 경쟁사`
2. **LLM 식별**: 2-3개 핵심 경쟁사 추출
3. **SWOT 분석**: 각 경쟁사별 강점/약점 분석

---

### 6️⃣ 투자 결정 및 보고서 생성 (Agent 5 & 6)

#### Agent 5: 20개 항목 VC 체크리스트 평가

**업계 표준 VC 기준 기반 종합 평가**

| # | 카테고리 | 질문 | 참조 데이터 |
|---|----------|------|-------------|
| 1-2 | **시장** | TAM > $1B? CAGR > 20%? | Agent 3 데이터 |
| 3-4 | **문제/제품** | 명확한 문제? 10배 개선? | Agent 1 |
| 5-6 | **기술** | 방어 가능한 해자? 검증된 성숙도? | Agent 2 tech_maturity |
| 7-8 | **팀** | 도메인 전문성? 실행 실적? | Agent 2 증거 |
| 9-10 | **경쟁** | 명확한 차별화? 높은 장벽? | Agent 4 |
| 11-12 | **비즈니스 모델** | 명확한 수익? LTV/CAC > 3x? | Agent 1, 2 |
| 13-14 | **견인력** | 기관 파트너십? 활성 사용자? | Agent 2 ecosystem |
| 15-16 | **신뢰도** | VC 펀딩? 미디어 검증? | Agent 2 credibility |
| 17-18 | **규제** | 명확한 전략? 낮은 리스크 점수? | Agent 2 compliance_risk |
| 19-20 | **확장성/적합성** | 글로벌 확장 가능? 독특한 포지셔닝? | Agent 1, 3 |

**결정 로직:**

| 점수 범위 | 결정 | 의미 |
|-----------|------|------|
| 점수 ≥ 15/20 |  "투자 적절" | 투자 승인 |
| 점수 12-14/20 |  "보류" | 추가 검토 필요 |
| 점수 < 12/20 |  "부정적" | 투자 거절 |

---

#### Agent 6: VC급 보고서 생성

**결과에 따른 두 가지 보고서 유형**
**발생 조건:**
- 5회 평가 후 투자 기준을 충족하는 스타트업이 없는 경우
- 또는 전체 스타트업 리스트 소진

**주요 섹션:**

1. 경영진 요약 (평가 통계)
2. 평가된 스타트업 목록 (표 형식)
3. 스타트업별 상세 평가
4. 투자자 성향 분석
5. 주요 발견사항 및 권고사항
   - 포트폴리오 확장 고려
   - 평가 기준 재검토
   - 직접 소싱 전략
6. 부록: 전체 랭킹 데이터

---

##  기술 스택

| 카테고리 | 기술 | 용도 |
|----------|------|------|
| **프레임워크** | LangGraph, LangChain | 에이전트 조율, 상태 관리 |
| **LLM** | GPT-4o, GPT-4o-mini | 핵심 추론 엔진 |
| **검색** | DuckDuckGo Search API | 웹 데이터 수집 (Tavily 대체) |
| **RAG** | Chroma DB | 임시 벡터 저장소 |
| **임베딩** | all-mpnet-base-v2 | 의미론적 검색 (sentence-transformers) |
| **데이터 형식** | JSON | 구조화된 데이터 교환 |
| **출력** | Markdown | 사람이 읽을 수 있는 보고서 |
| **로깅** | LangSmith | 추적 및 디버깅 |
| **환경** | Python 3.11+ | 런타임 |

---

## 🤖 에이전트 상세

| 에이전트 | 역할 | RAG | 주요 책임 |
|----------|------|-----|-----------|
| **Agent 0** 🏦 | 성향 평가 | ❌ | 5개 질문 설문, 투자자 유형 분류 |
| **Agent 1** 🔍 | 스타트업 탐색 및 랭킹 | ❌ | 웹 검색, 다기준 점수, 랭킹 |
| **Agent 2** 🗜️ | 기술 실사 | ❌ | 10개 노드 서브그래프, 기술 성숙도 점수, 증거 수집 |
| **Agent 3** 📊 | 시장 평가 | ✅ | RAG 기반 시장 분석 (4개 PDF 출처) |
| **Agent 4** 🧮 | 경쟁사 분석 | ❌ | 경쟁사 식별, SWOT 분석 |
| **Agent 5** ⚖️ | 투자 결정 | ❌ | 20개 항목 체크리스트 평가, 승인/보류/거절 |
| **Agent 6** 📝 | 보고서 생성 | ❌ | VC급 마크다운 보고서 (15-20페이지) |

---

## Architecture

<img width="433" height="1581" alt="image" src="https://github.com/user-attachments/assets/75d42131-8eed-4230-bd3b-0e1fcc0cdf9f" />

---
## 프로젝트 구조
```
RWA_Investment_Agent/
│
├
├── startups.json                     # 입력: 10개 스타트업 리스트
│
├── agent0_persona.py                 # Agent 0: 투자자 성향 평가 (공격형/보수형)
├── agent1_search.py                  # Agent 1: 웹 검색 + 4개 기준 평가 + 랭킹
├── agent2_tech_summary.py            # Agent 2: 기술 실사 (10개 노드 서브그래프)
├── agent3_marketeval.py              # Agent 3: 시장 분석 (RAG + 4개 PDF 문서)
├── agent4_CompetitorAnalysis.py      # Agent 4: 경쟁사 SWOT 분석
├── agent5_Decision.py                # Agent 5: 20-Point 체크리스트 투자 결정
├── agent6_ReportGen.py               # Agent 6: VC급 보고서 생성 (15-20페이지)
│
├── config.py                         # 공유 설정 (LLM, DuckDuckGo 검색, 체크리스트)
├── graph_state.py                    # 전역 상태 정의 (모든 에이전트 데이터)
├── control_flow.py                   # 루프 제어 (최대 5회 재시도)
│
├── main.py                           # 메인 실행 스크립트
│
├── Final_Investment_Report.md        # 출력: 최종 투자 보고서
└── README.md                         # 프로젝트 문서
```

### 실행 흐름

```
START → Agent 0 (성향) → Agent 1 (랭킹) 
  ↓
Agent 2 (기술) → Agent 3 (시장) → Agent 4 (경쟁) → Agent 5 (결정)
  ↓
조건 분기:
  ├─ "투자 적절" → Agent 6 (성공 보고서) → END
  └─ "보류/부정" → 다음 스타트업 선택 → Agent 2로 재진입 (최대 5회)
      └─ 5회 초과 또는 리스트 소진 → Agent 6 (실패 보고서) → END
```

Contributor Role 
백광운 Company Profiling Agent, Startup Selection Agent Design 

백선재 Investment Decision Agent and Report Generation Design 

문해준 Technology Evaluation Agent Design 

조혜림 Market Evaluation Agent Design, RAG Embedding

