# AI Startup Investment Evaluation Agent (RWA Tokenization Focus)
본 프로젝트는 **RWA(Real-World Asset, 실물자산) 토큰화 분야의 AI 스타트업**에 대한 **투자 가능성을 자동 평가**하는 다중 에이전트(Multi-Agent) 시스템을 설계하고 구현한 실습 프로젝트입니다.

---

## 🧭 Overview

- **Objective** :  
  부동산, 미술품, 채권, 지식재산권 등 실물자산을 블록체인 상에서 **토큰화(RWA Tokenization)** 하는 스타트업의 **기술력·시장성·규제 적합성·수익성**을 종합적으로 분석하여 **투자 적합성**을 자동 평가

- **Method** :  
  LangGraph 기반 **Multi-Agent + Agentic RAG** 구조로 설계  

- **Tools** :  
  LangGraph, LangChain, Tavily Search API, OpenAI GPT-4o-mini

---

## AI Agent 서비스 차별화 고민 포인트
- 1. 투자 시장 규모자체가 해외가 더 크고, 리서치에 필요한 해외 원천 글 자료가 더 풍부하다고 생각했기에 해외 글을 가져오는 이점을 챙기기 위해 Docstrings도 모두 영어로 코드를 짜서 진행
- 2. RAG를 진행할때 임베딩 모델도 한국어 모델은 선택지 폭과 성능의 옵션이 적어서 영어를 더 적합하게 사용할 수 있도록 "모델명: multilingual-e5-large"을 채택했습니다.

## ⚙️ Features

### 1️⃣ 스타트업 데이터 입력 (list.json)
- 약 10개의 RWA 관련 스타트업을 JSON 형태로 입력  
  (`name`, `sector`, `strength` 필드 포함)
- Agent 1이 Tavily Search API를 이용하여 공식 웹사이트, 기사, 파트너십 정보를 자동 수집  

### 2️⃣ 투자자 성향 분석 (Agent 0)
- 투자 성향을 **Aggressive(공격형)** / **Conservative(보수형)** 두 가지로 분류  
- 각 성향에 따라 평가 가중치(weight)를 차등 적용  

| 투자자 유형 | Seed/Early | Regional/ESG | Growth + Partnership | Regulation/Monetization |
|--------------|-------------|---------------|-----------------------|--------------------------|
| 🧨 Aggressive | **0.40 (최우선)** | 0.15 | **0.35 (중요)** | 0.10 |
| 🧩 Conservative | 0.10 | **0.30 (ESG 중점)** | 0.20 | **0.40 (규제·수익화 중점)** |

→ Agent 1은 Agent 0의 `investor_persona` 결과를 받아 스타트업 평가 시 가중치를 반영

### 3️⃣ 스타트업 탐색 및 평가 (Agent 1)
- 각 기업을 아래 4가지 기준으로 평가  
  1. **Seed / Early Stage:** 혁신성, 성장 잠재력, 초기 자금 조달 수준  
  2. **Regional / ESG:** 지역 확장성, ESG 연관성  
  3. **Growth + Partnership:** 성장 속도, 전략적 제휴 여부  
  4. **Regulation / Monetization:** 규제 적응력, 수익화 구조 명확성  
- 점수 기반으로 `total_score`, `domain_fit`, `credibility_score`, `final_score` 산출

### 3️⃣ 기술 평가 (Agent 2 – Tech Summary Agent)

핵심 목적: 
- 스타트업의 기술력·보안성·규제 준수도를 평가하여 tech_score, credibility, domain_fit, compliance_risk 등을 산출
- Agent 2는 RAG 검색 결과와 실시간 신호(raw_signals, normalized_signals)를 종합해 기업의 기술 성숙도(TRL), 아키텍처 안정성, 규제 인증 상태를 자동 분석

분석 기준:
* 기술 아키텍처 (Tech Architecture) :
  웹 기반 토큰화 플랫폼의 보안성·확장성·데이터 무결성 등을 평가
* 규제 준수 (Compliance & Governance) :
  SEC 등록 대체거래시스템(ATS)·브로커딜러·이전대리인 면허 보유 여부, KYC/AML 이행 정도 평가
* 도메인 적합성 (Domain Fit) :
  RWA 토큰화 분야에서의 제품 포지셔닝과 시장 활용성 평가
* 신뢰도 (Credibility) :
  기관 투자자 참여(BlackRock BUIDL 연계 등), 파트너 생태계 다변성 기준 평가
* 생태계 (Ecosystem Integration) :
  FalconX, Fireblocks 등 TradFi · DeFi 네트워크 협업 여부 측정

### 4️⃣ 시장성 평가 (Agent 3 – Market Evaluation Agent)

기술 요약 결과를 입력으로 받아, 시장 규모·성장률·수요 동향 분석
- RAG 문서: CoinGecko 2025 Report / WEF Report / Cornerstone / 자산 토큰화 심층 분석
- 평가 항목
  1. 시장 성장성 (Growth Momentum)
  2. 수요 동력 (Demand Drivers)
  3. 경쟁 강도 (Competitive Pressure)
  4. 규제 환경 (Regulatory Clarity)
→ market_score 및 demand_score 산출, 이후 투자 판단 에이전트로 전달

시장성 평가는 VC 및 PE 투자 기준(Bessemer Checklist, Scorecard Method)을 참조
- 시장 성장성 (40%): 산업의 TAM·SAM·SOM 규모와 성장률을 분석해 시장의 확장 가능성과 제도권 주목도를 평가
- 수요 동력 (30%): 제품의 시장 적합성(Product-Market Fit), 고객 기반, 정책 지원 수준을 측정
- 경쟁 강도 (20%): 시장 내 플레이어 수, 진입장벽, 기술 차별성을 분석해 경쟁 우위 여부를 평가
- 규제/리스크 (10%): 법적 불확실성, 유동성·운영 리스크 등 부정 요인을 검토하여 안정성을 판단

| No | 문서명                                                       | 활용 목적                 | 주요 활용 내용                                                                                                                                                |
| -- | --------------------------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ①  | **CoinGecko 2025 RWA Report**                             | 시장 성장 데이터 및 산업 트렌드 수집 | - 글로벌 RWA(Real World Asset) 시장 규모 및 성장률 (240억 → 30조 달러 예측)<br>- 주요 토큰화 프로젝트 및 기업 사례 (Ondo Finance, BlackRock BUIDL 등)<br>- 시장 성장성(Growth) 스코어 산정에 직접 반영 |
| ②  | **WEF_Asset_Tokenization_in_Financial_Markets_2025**      | 거시적 시장 동향 및 제도권 진입 분석 | - 금융 시장 내 자산 토큰화의 제도권 편입 사례<br>- 글로벌 기관 참여, 규제 명확화 추세<br>- “Institutional adoption”, “Regulatory clarity” 키워드 가중치 근거                                    |
| ③  | **(Eng) The Cornerstone of Trust in a New Financial Era** | 신뢰 및 제도 기반 관점 보완      | - 금융 생태계의 신뢰(Trust layer) 구축 및 보안 강화<br>- 블록체인 기반 금융 인프라의 신뢰도 향상 요인<br>- 시장 진입 장벽 완화 및 제도적 수요 요인 분석                                                     |
| ④  | **자산 토큰화 심층 분석 보고서 (한국어)**                                | 국내 시장 환경 및 규제 분석      | - 한국·미국 규제 프레임워크 비교<br>- 디지털자산기본법, STO 가이드라인 등 제도 분석<br>- 국내 금융사 컨소시엄(미래에셋, 신한, KB 등) 동향<br>- “국내 시장 수요”, “정책 수용성” 점수 반영                                |


### 5️⃣ 통합 투자 판단 및 보고서 생성
- **Case 1: 투자 적절**
  - 투자 유망 스타트업 1개를 선정  
  - `Final_Investment_Report.md` 파일 생성  
  - 주요 항목: 스타트업 이름 / 종합 점수 / 투자자 성향 / 판단 근거  
- **Case 2: 투자 부적합**
  - 10개 스타트업 모두 평가 후 ‘투자 적절’ 대상이 없는 경우  
  - “총 n개 스타트업 검토, 모두 보류” 보고서를 자동 생성


---

## 🧰 Tech Stack

| Category   | Details |
|-------------|----------|
| **Framework** | LangGraph, LangChain |
| **LLM** | GPT-4o-mini via OpenAI API |
| **Retrieval** | Tavily Search API, Chorma |
| **Embedding** | multilingual-e5-large |
| **Storage** | JSON 기반 파이프라인 저장 구조 |
| **Visualization** | docx 기반 Summary Report |

---

## 🤖 Agents

| 에이전트 | 역할 | RAG 여부 | 내용 |
|-----------|------|-----------|------|
| 🔍 **스타트업 탐색 에이전트** | 유명한 AI 스타트업 정보 수집 | ❌ X | 웹서치, 스타트업 평가 리포트 등에서 정보 수집 |
| 🗜️ **기술 요약 에이전트** | 스타트업의 기술력 핵심 요약 | ❌ X | 홈페이지, 논문 등에서 핵심 기술·장단점 정리 |
| 📊 **시장성 평가 에이전트** | 시장 성장성·수요 분석 | ✅ O | 산업 리포트, 시장 뉴스 기반 성장성 평가 |
| 🧮 **투자 판단 에이전트** | 종합 판단,  최종 요약 보고서 생성 | ❌ X | “투자” vs “보류” 결정,단계별 결과를 통합하여 투자 보고서 작성  |


---

## 🧩 Architecture
<img width="246" height="590" alt="image" src="https://github.com/user-attachments/assets/858afde7-019e-463b-864b-b1804f9cf56b" />

---

## 📂 Directory Structure
```
├── data/                  # 스타트업 리스트 및 PDF 문서
├── agents/                # 각 평가 기준별 Agent 모듈
├── prompts/               # 프롬프트 템플릿
├── outputs/               # 평가 결과 및 최종 보고서
├── main_agent01.py        # Agent 0 + Agent 1 실행 스크립트
├── tech_summary_agent_vol2.py  # Agent 2 기술 요약/리스크 평가
└── README.md              # 프로젝트 개요 문서
```

---

Contributor Role 

백광운 Company Profiling Agent, Startup Selection Agent Design 

백선재 Investment Decision Agent and Report Generation Design 

문해준 Technology Evaluation Agent Design 

조혜림 Market Evaluation Agent Design, RAG Embedding

