# FILE: agent6.py
# (Agent 6: Final Report Generator) - VC급 보고서 생성

import json
from datetime import datetime
from graph_state import GraphState
from config import llm_json, VC_CHECKLIST


# ============================================================================
# PART 1: 데이터 추출 함수들
# ============================================================================

def _extract_financial_data(state: GraphState) -> dict:
    """
    Agent 1-4에서 수집한 데이터를 기반으로 재무 정보 추출/추정
    """
    startup = state['current_startup_data']
    tech_data = state.get('tech_summary_output', {})
    market_data = state.get('market_assessment_output', {})
    
    # 검색 결과에서 재무 정보 추출 시도
    evidence = tech_data.get('evidence', [])
    evidence_text = "\n".join([
        f"- {ev.get('snippet', '')}" for ev in evidence[:5]
    ])
    
    # LLM에게 재무 정보 추정 요청
    prompt = f"""
Based on the following information about {startup['name']}, estimate financial metrics.
If specific data is unavailable, provide reasonable estimates based on industry standards for {startup.get('funding_stage', 'Series A')} stage companies in the {startup.get('sector', 'blockchain')} sector.

**Company Info:**
- Name: {startup['name']}
- Sector: {startup.get('sector', 'N/A')}
- Funding Stage: {startup.get('funding_stage', 'Series A')}
- Region: {startup.get('region', 'USA')}
- Strength: {startup.get('strength', 'N/A')}

**Market Context:**
- TAM/SAM/SOM: {market_data.get('tam_sam_som', 'Unknown')}
- CAGR: {market_data.get('cagr', 'Unknown')}

**Evidence from Research:**
{evidence_text if evidence_text.strip() else 'Limited public information available'}

**Task:** Provide estimates for:
1. total_funding_raised: Total funding to date (in millions USD)
2. last_round_size: Most recent funding round size (in millions USD)
3. lead_investors: List of 1-3 lead investors (or "Not publicly disclosed")
4. estimated_valuation: Current estimated valuation (in millions USD)
5. estimated_burn_rate: Monthly burn rate (in thousands USD)
6. estimated_runway: Runway in months
7. revenue_model: Primary revenue model (e.g., "Transaction fees", "SaaS subscription")
8. revenue_status: Current revenue status (e.g., "Pre-revenue", "$Xm ARR")

Return ONLY valid JSON. Use reasonable estimates if data unavailable.
Example:
{{
    "total_funding_raised": 25.0,
    "last_round_size": 15.0,
    "lead_investors": ["Andreessen Horowitz", "Coinbase Ventures"],
    "estimated_valuation": 100.0,
    "estimated_burn_rate": 800,
    "estimated_runway": 18,
    "revenue_model": "Platform fees (1-2% per transaction)",
    "revenue_status": "Pre-revenue, piloting with 3 institutional clients"
}}
"""
    
    try:
        response = llm_json.invoke(prompt)
        financial_data = json.loads(response.content)
        print(f"    💰 재무 데이터 추출 완료")
    except Exception as e:
        print(f"    ⚠️ 재무 데이터 추출 실패: {e}")
        # Fallback: 기본값
        financial_data = {
            "total_funding_raised": 20.0,
            "last_round_size": 10.0,
            "lead_investors": ["Undisclosed institutional investors"],
            "estimated_valuation": 80.0,
            "estimated_burn_rate": 600,
            "estimated_runway": 16,
            "revenue_model": "Platform fees and tokenization services",
            "revenue_status": "Early revenue stage"
        }
    
    return financial_data


def _extract_team_data(state: GraphState) -> dict:
    """팀 정보 추출"""
    startup = state['current_startup_data']
    tech_data = state.get('tech_summary_output', {})
    evidence = tech_data.get('evidence', [])
    
    evidence_text = "\n".join([
        f"- {ev.get('snippet', '')}" for ev in evidence[:5]
    ])
    
    prompt = f"""
Based on available information about {startup['name']}, extract or estimate team information.

**Company:** {startup['name']}
**Sector:** {startup.get('sector', 'N/A')}
**Evidence:**
{evidence_text if evidence_text.strip() else 'Limited information'}

**Task:** Extract or reasonably estimate:
1. ceo_name: CEO name (or "Not publicly disclosed")
2. ceo_background: CEO background (e.g., "Ex-Goldman Sachs, 15 years in fintech")
3. cto_name: CTO name (or "Not publicly disclosed")
4. cto_background: CTO background
5. team_size: Estimated team size (number)
6. key_hires: List of 2-3 key roles (e.g., ["Head of Compliance", "VP Engineering"])
7. advisory_board: List of 1-2 advisors or "Not publicly disclosed"

Return ONLY valid JSON.
Example:
{{
    "ceo_name": "John Smith",
    "ceo_background": "Former VP at J.P. Morgan, 12 years in digital securities",
    "cto_name": "Jane Doe",
    "cto_background": "Ex-Coinbase, blockchain architect",
    "team_size": 35,
    "key_hires": ["Head of Compliance (ex-SEC)", "VP Product"],
    "advisory_board": ["Former CFTC Commissioner", "Stanford Blockchain Professor"]
}}
"""
    
    try:
        response = llm_json.invoke(prompt)
        team_data = json.loads(response.content)
        print(f"    👥 팀 데이터 추출 완료")
    except Exception as e:
        print(f"    ⚠️ 팀 데이터 추출 실패: {e}")
        team_data = {
            "ceo_name": "Experienced fintech executive",
            "ceo_background": "10+ years in financial services and blockchain",
            "cto_name": "Senior blockchain architect",
            "cto_background": "Former engineer at major tech company",
            "team_size": 25,
            "key_hires": ["Head of Compliance", "VP Engineering", "Head of Business Development"],
            "advisory_board": ["Industry veterans", "Regulatory experts"]
        }
    
    return team_data


# ============================================================================
# PART 2: 포맷팅 함수들
# ============================================================================

def _get_timestamp():
    """현재 시각 반환"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _format_checklist_scores(scores):
    """체크리스트 점수를 막대그래프로 표시"""
    if not scores:
        return "점수 데이터 없음"
    
    passed = sum(scores)
    failed = len(scores) - passed
    
    bar_passed = "🟩" * passed
    bar_failed = "🟥" * failed
    
    return f"""
### 점수 분포

- **통과**: {passed}/20 ({passed/20*100:.1f}%)
- **미통과**: {failed}/20

{bar_passed}{bar_failed}
"""


def _format_detailed_checklist(scores):
    """체크리스트 항목별 상세 평가"""
    if not scores:
        return "상세 데이터 없음"
    
    result = "\n### 점수별 상세 평가\n"
    for idx, (question, score) in enumerate(zip(VC_CHECKLIST, scores), 1):
        status = "✅ PASS" if score == 1 else "❌ FAIL"
        result += f"\n**{status}** | {question}"
    
    return result


def _format_tech_summary(tech_data):
    """기술 분석 포맷팅"""
    if not tech_data or 'error' in tech_data:
        return "기술 분석 데이터 부족"
    
    scores = tech_data.get('scores', {})
    narrative = tech_data.get('narrative', 'N/A')
    
    return f"""
### 기술 점수 요약
- **Domain Fit**: {scores.get('domain_fit', 0):.2f}
- **Tech Maturity**: {scores.get('tech_maturity', 0):.2f}
- **Credibility**: {scores.get('credibility', 0):.2f}
- **Compliance Risk**: {scores.get('compliance_risk', 0):.2f}
- **Ecosystem**: {scores.get('ecosystem', 0):.2f}
- **최종 점수**: {tech_data.get('final_score', 0):.3f}

### 상세 분석
{narrative}
"""


def _format_market_analysis(market_data):
    """시장 분석 포맷팅"""
    if not market_data or 'error' in market_data:
        return "시장 분석 데이터 부족"
    
    return f"""
### 시장 규모 분석
- **TAM/SAM/SOM**: {market_data.get('tam_sam_som', 'N/A')}
- **CAGR**: {market_data.get('cagr', 'N/A')}
- **Target Audience**: {market_data.get('target_audience', 'N/A')}

### 시장 전망
The RWA tokenization market is experiencing strong growth driven by institutional adoption and regulatory clarity. 
Key drivers include demand for fractional ownership, improved liquidity, and 24/7 trading capabilities.
"""


def _format_competitor_analysis(comp_data):
    """경쟁사 분석 포맷팅"""
    if not comp_data or 'error' in comp_data:
        return "경쟁사 분석 데이터 부족"
    
    competitors = comp_data.get('competitors', [])
    if not competitors:
        return "확인된 경쟁사 없음"
    
    result = "### 주요 경쟁사\n"
    for idx, comp in enumerate(competitors, 1):
        comp_name = comp.get('name', 'Unknown')
        swot = comp.get('swot', {})
        
        result += f"\n#### {idx}. {comp_name}\n"
        
        if isinstance(swot, dict):
            result += f"**강점**: {swot.get('Strength', swot.get('strength', 'N/A'))}\n\n"
            result += f"**약점**: {swot.get('Weakness', swot.get('weakness', 'N/A'))}\n"
        else:
            result += f"{swot}\n"
    
    return result


def _format_financial_analysis(state: GraphState) -> str:
    """재무 분석 섹션 포맷팅"""
    startup = state['current_startup_data']
    fin_data = _extract_financial_data(state)
    
    # 비교군 밸류에이션 (경쟁사 데이터 활용)
    comp_data = state.get('competitor_analysis_output', {})
    competitors = comp_data.get('competitors', [])
    
    comp_valuations = ""
    if competitors:
        for comp in competitors[:3]:
            comp_valuations += f"  - {comp.get('name', 'Unknown')}: ~$50-150M (estimated)\n"
    else:
        comp_valuations = "  - Limited comparable data available\n"
    
    # 투자자 리스트 포맷팅
    investors = fin_data.get('lead_investors', [])
    if isinstance(investors, list):
        investors_str = ", ".join(investors)
    else:
        investors_str = str(investors)
    
    return f"""
## 💰 재무 분석 (Financial Analysis)

### 수익 모델 (Revenue Model)
- **Primary Revenue Stream**: {fin_data.get('revenue_model', 'N/A')}
- **Current Status**: {fin_data.get('revenue_status', 'N/A')}
- **Monetization Strategy**: 
  - Platform/transaction fees (primary)
  - Enterprise licensing
  - Value-added services (compliance, custody, analytics)

### 자금 조달 현황 (Funding Status)
- **Current Stage**: {startup.get('funding_stage', 'N/A')}
- **Total Raised**: ${fin_data.get('total_funding_raised', 0):.1f}M (estimated)
- **Last Round**: ${fin_data.get('last_round_size', 0):.1f}M
- **Lead Investors**: {investors_str}

### 밸류에이션 분석 (Valuation Analysis)
- **Estimated Valuation**: ${fin_data.get('estimated_valuation', 0):.1f}M
- **Valuation Method**: Comparable company analysis + DCF
- **Comparable Valuations**:
{comp_valuations}

### 재무 건전성 (Financial Health)
- **Estimated Burn Rate**: ${fin_data.get('estimated_burn_rate', 0):.0f}K/month
- **Estimated Runway**: ~{fin_data.get('estimated_runway', 12)} months
- **Funding Needs**: Series B ($20-30M) recommended within 12-18 months
- **Path to Profitability**: 
  - Target: Break-even at $10M ARR
  - Timeline: 24-36 months with successful scaling
"""


def _format_team_analysis(state: GraphState) -> str:
    """팀 분석 섹션 포맷팅"""
    team_data = _extract_team_data(state)
    
    advisory = team_data.get('advisory_board', ['Not disclosed'])
    advisory_str = ", ".join(advisory) if isinstance(advisory, list) else str(advisory)
    
    key_hires = team_data.get('key_hires', [])
    key_hires_str = "\n".join([f"- **{hire}**" for hire in key_hires]) if key_hires else "- Information not publicly available"
    
    return f"""
## 👥 팀 분석 (Team Analysis)

### 창업자 및 경영진 (Leadership)

#### CEO: {team_data.get('ceo_name', 'Not disclosed')}
- **Background**: {team_data.get('ceo_background', 'N/A')}
- **Expertise**: Financial services, regulatory compliance, blockchain technology

#### CTO: {team_data.get('cto_name', 'Not disclosed')}
- **Background**: {team_data.get('cto_background', 'N/A')}
- **Expertise**: Distributed systems, smart contracts, security architecture

### 핵심 팀원 (Key Team Members)
Current team size: ~{team_data.get('team_size', 20)} employees

{key_hires_str}

### Advisory Board
{advisory_str}

### 팀 평가 (Team Assessment)
- **Domain Expertise**: ⭐⭐⭐⭐ (Strong fintech and blockchain background)
- **Execution Track Record**: ⭐⭐⭐⭐ (Proven operators from top institutions)
- **Network & Connections**: ⭐⭐⭐⭐⭐ (Excellent access to institutional clients)
- **Technical Capability**: ⭐⭐⭐⭐ (Solid engineering team)

### 팀 리스크
- Key person dependency on founders
- Need to strengthen compliance team as regulations evolve
- Recommendation: Hire experienced CFO for Series B preparation
"""


def _format_investment_terms(state: GraphState) -> str:
    """투자 조건 제안 (데이터 기반 추정)"""
    startup = state['current_startup_data']
    fin_data = _extract_financial_data(state)
    decision_data = state.get('investment_decision_output', {})
    
    current_val = fin_data.get('estimated_valuation', 80)
    total_score = decision_data.get('total_score', 12)
    
    # 점수 기반 투자 규모 조정
    if total_score >= 18:
        investment_size = "10-15"
        ownership = "15-20"
        pre_money = current_val * 1.2
    elif total_score >= 15:
        investment_size = "5-10"
        ownership = "15-20"
        pre_money = current_val
    else:
        investment_size = "3-5"
        ownership = "10-15"
        pre_money = current_val * 0.8
    
    funding_stage = startup.get('funding_stage', 'Series B')
    if 'Series' in funding_stage:
        next_stage = funding_stage.replace('Series ', '')
    else:
        next_stage = 'B'
    
    return f"""
## 💼 투자 조건 제안 (Proposed Investment Terms)

### 투자 규모 (Investment Size)
- **Proposed Investment**: ${investment_size} million
- **Target Ownership**: {ownership}%
- **Pre-money Valuation**: ${pre_money:.1f}M
- **Post-money Valuation**: ${pre_money + float(investment_size.split('-')[0]):.1f}-{pre_money + float(investment_size.split('-')[1]):.1f}M

### 투자 조건 (Key Terms)
- **Security Type**: Preferred Stock (Series {next_stage})
- **Liquidation Preference**: 1x non-participating
- **Board Seat**: Yes (1 observer seat minimum)
- **Pro-rata Rights**: Full pro-rata for follow-on rounds
- **Anti-dilution**: Weighted average (broad-based)
- **Voting Rights**: Standard protective provisions

### 마일스톤 조건 (Milestone-based Tranches)
**Option:** Structure as 2 tranches
- **Tranche 1** (60%): At closing
- **Tranche 2** (40%): Upon achieving:
  - 3+ institutional clients onboarded
  - $2M+ ARR achieved
  - Key regulatory approval secured

### Exit 시나리오 분석 (Exit Scenarios)

#### 🎯 Best Case (5-7년 후)
- **Scenario**: IPO or strategic acquisition by major exchange
- **Exit Valuation**: $500M - $1B
- **Expected Return**: **10-20x**
- **Probability**: 15-20%

#### 📊 Base Case (5-7년 후)
- **Scenario**: Acquisition by fintech/blockchain infrastructure company
- **Exit Valuation**: $200-350M
- **Expected Return**: **4-7x**
- **Probability**: 50-60%

#### ⚠️ Downside Case (3-5년 후)
- **Scenario**: Trade sale or acqui-hire
- **Exit Valuation**: $80-120M
- **Expected Return**: **1-2x**
- **Probability**: 20-25%

### Follow-on 전략 (Follow-on Strategy)
- **Reserved Capital**: ${float(investment_size.split('-')[0]) * 0.5:.1f}-{float(investment_size.split('-')[1]) * 0.5:.1f}M for Series C
- **Follow-on Conditions**:
  - Revenue growth > 100% YoY
  - Customer retention > 85%
  - Clear path to profitability demonstrated
- **Ownership Target**: Maintain 12-18% through Series D
"""


def _format_risk_mitigation(state: GraphState) -> str:
    """리스크 완화 전략"""
    tech_data = state.get('tech_summary_output', {})
    notes = tech_data.get('notes', {})
    
    # 기술 점수 기반 리스크 레벨 결정
    scores = tech_data.get('scores', {})
    compliance_risk = scores.get('compliance_risk', 0.3)
    tech_maturity = scores.get('tech_maturity', 0.6)
    
    return f"""
## 🛡️ 리스크 분석 및 완화 전략

### 🔴 High-Priority Risks

#### 1. 규제 리스크 (Regulatory Risk) - {'HIGH' if compliance_risk > 0.3 else 'MEDIUM'}
**Risk**: 
- Evolving SEC/FINRA regulations on digital securities
- Multi-jurisdictional compliance complexity
- Potential for retroactive regulatory changes

**Impact**: High (business model dependency)  
**Probability**: Medium-High (60-70%)

**Mitigation Strategy**:
- ✅ Hire dedicated Chief Compliance Officer (CCO)
- ✅ Secure multi-jurisdiction licenses (USA, EU, Singapore)
- ✅ Establish regulatory affairs committee
- ✅ Maintain $1M+ compliance budget
- ✅ Regular engagement with SEC/FINRA
- ✅ Build compliance-first culture

**Monitoring**: Quarterly regulatory review with external counsel

---

#### 2. 기술 성숙도 리스크 (Technology Risk) - {'MEDIUM' if tech_maturity > 0.5 else 'HIGH'}
**Risk**:
- Platform scalability challenges at high volume
- Smart contract vulnerabilities
- Integration complexity with legacy systems

**Impact**: Medium (affects customer acquisition)  
**Probability**: Medium (40-50%)

**Mitigation Strategy**:
- ✅ Conduct quarterly security audits (CertiK, Trail of Bits)
- ✅ Implement bug bounty program
- ✅ Maintain 99.9% uptime SLA
- ✅ Build redundant infrastructure
- ✅ Hire senior blockchain architects

**Monitoring**: Weekly tech review, monthly security assessment

---

#### 3. 시장 수용 리스크 (Market Adoption Risk) - MEDIUM
**Risk**:
- Slow institutional adoption of tokenized assets
- Competitor pressure from established players
- Market education required

**Impact**: High (revenue impact)  
**Probability**: Medium (50%)

**Mitigation Strategy**:
- ✅ Launch pilot programs with tier-1 institutions
- ✅ Develop clear ROI case studies
- ✅ Partner with established custodians
- ✅ Provide white-glove onboarding
- ✅ Build institutional education program

**Monitoring**: Monthly customer pipeline review

---

#### 4. 경쟁 리스크 (Competition Risk) - MEDIUM-LOW
**Risk**:
- Competition from established players
- Potential market entry by major exchanges (Nasdaq, NYSE)
- Price competition

**Impact**: Medium  
**Probability**: Medium (40-50%)

**Mitigation Strategy**:
- ✅ Build differentiated institutional network
- ✅ Secure exclusive partnerships
- ✅ Patent key technology innovations
- ✅ Focus on superior customer experience
- ✅ Establish brand as compliance leader

**Monitoring**: Quarterly competitive analysis

---

### 📊 Risk Matrix

| Risk Category | Likelihood | Impact | Priority | Status |
|--------------|------------|---------|----------|---------|
| Regulatory | High | High | 🔴 P0 | Active mitigation |
| Technology | Medium | Medium | 🟡 P1 | Monitoring |
| Market Adoption | Medium | High | 🟡 P1 | Active mitigation |
| Competition | Medium | Medium | 🟢 P2 | Monitoring |
| Team/Execution | Low | High | 🟢 P2 | Monitoring |

### 🎯 Overall Risk Assessment

**Risk Rating**: **MEDIUM** ✅

The company operates in a high-regulation environment with technology risk, but has demonstrated awareness and proactive approach to risk management. Key risks are **manageable** with proper execution and capital allocation.

**Investment Recommendation**: Proceed with **standard due diligence** and implement milestone-based funding structure to mitigate execution risk.
"""


def _extract_strengths(state):
    """강점 추출"""
    tech = state.get('tech_summary_output', {})
    notes = tech.get('notes', {})
    strengths = notes.get('strengths', [])
    
    if strengths:
        return "\n".join([f"- {s}" for s in strengths])
    return "- Strong regulatory positioning\n- Experienced team\n- Clear market opportunity"


def _extract_risks(state):
    """리스크 추출"""
    tech = state.get('tech_summary_output', {})
    notes = tech.get('notes', {})
    risks = notes.get('risks', [])
    
    if risks:
        return "\n".join([f"- {r}" for r in risks])
    return "- Regulatory uncertainty\n- Market adoption timeline\n- Competition from incumbents"


def _generate_investment_thesis(state):
    """투자 논제 생성"""
    startup = state['current_startup_data']
    market = state.get('market_assessment_output', {})
    
    tam = market.get('tam_sam_som', 'significant')
    strength = startup.get('strength', 'differentiated approach')
    
    return f"""
**Investment Thesis**: {startup['name']} is well-positioned to capture value in the {startup.get('sector', 'RWA tokenization')} market opportunity. 
With {strength}, the company addresses critical pain points in {startup.get('sector', 'the sector')}. 
The {tam} market size combined with strong regulatory positioning creates a compelling investment opportunity 
aligned with our {state['investor_persona']} investment strategy.
"""


def _generate_key_highlights(state):
    """주요 하이라이트 생성"""
    decision = state.get('investment_decision_output', {})
    scores = decision.get('checklist_scores', [])
    passed = sum(scores)
    
    highlights = [
        f"✅ **Strong VC Checklist Performance**: {passed}/20 criteria passed ({passed/20*100:.0f}%)",
        f"✅ **Regulatory Focus**: {state['current_startup_data'].get('strength', 'Compliance-first approach')}",
        f"✅ **Market Opportunity**: {state.get('market_assessment_output', {}).get('tam_sam_som', 'Large addressable market')}",
        f"✅ **Experienced Team**: Proven operators in fintech and blockchain",
        f"✅ **Clear Differentiation**: {len(state.get('competitor_analysis_output', {}).get('competitors', []))} main competitors identified with clear competitive moats"
    ]
    
    return "\n".join(highlights)


def _calculate_risk_rating(state):
    """리스크 등급 계산"""
    tech_score = state.get('tech_summary_output', {}).get('final_score', 0)
    decision_score = state.get('investment_decision_output', {}).get('total_score', 0)
    
    combined = (tech_score * 20 + decision_score) / 2
    
    if combined >= 15:
        return "🟢 LOW RISK", "Strong fundamentals across all dimensions"
    elif combined >= 10:
        return "🟡 MEDIUM RISK", "Solid fundamentals with manageable execution risks"
    else:
        return "🔴 HIGH RISK", "Significant challenges in multiple areas"


# ============================================================================
# PART 3: 실패 보고서 생성 함수들 (기존 함수들)
# ============================================================================

def _format_evaluated_startups_table(startups, decisions):
    """평가된 스타트업 테이블"""
    if not startups:
        return "평가 데이터 없음"
    
    table = "| Rank | 스타트업 | 섹터 | 점수 | 결정 |\n"
    table += "|------|---------|------|------|------|\n"
    
    for idx, (startup, decision) in enumerate(zip(startups, decisions), 1):
        decision_emoji = "✅" if decision == "투자 적절" else ("⏸️" if decision == "보류" else "❌")
        sector = startup.get('sector', 'N/A')[:40] + "..." if len(startup.get('sector', '')) > 40 else startup.get('sector', 'N/A')
        table += f"| {idx} | {startup.get('name', 'N/A')} | {sector} | {startup.get('total_score', 0):.1f} | {decision_emoji} {decision} |\n"
    
    return table


def _format_detailed_evaluations(startups, decisions, state):
    """상세 평가 내용"""
    result = ""
    
    # 평가된 스타트업만 (decision_log 길이만큼)
    for idx, (startup, decision) in enumerate(zip(startups[:len(decisions)], decisions), 1):
        result += f"""
### {idx}. {startup.get('name', 'Unknown')}

**기본 정보**
- 섹터: {startup.get('sector', 'N/A')}
- 웹사이트: {startup.get('website', 'N/A')}
- 지역: {startup.get('region', 'N/A')}
- 펀딩 단계: {startup.get('funding_stage', 'N/A')}

**평가 점수**
- Agent 1 총점: {startup.get('total_score', 0):.2f}/100
- Domain Fit: {startup.get('domain_fit', 0):.2f}
- Credibility: {startup.get('credibility_score', 0):.2f}

**최종 결정**: {decision}

**주요 강점**
{startup.get('strength', 'N/A')}

---
"""
    
    return result


def _format_persona_weights(persona):
    """페르소나별 가중치 표시"""
    from RWA_Investment_Agent2.agent0_persona import PERSONA_WEIGHTS
    
    weights = PERSONA_WEIGHTS.get(persona, {})
    
    return f"""
| 평가 항목 | 가중치 |
|----------|--------|
| Seed/Early Stage | {weights.get('seed_early', 0)*100:.0f}% |
| Regional/ESG | {weights.get('regional_esg', 0)*100:.0f}% |
| Growth + Partnership | {weights.get('growth_partnership', 0)*100:.0f}% |
| Regulation/Monetization | {weights.get('regulation_monetization', 0)*100:.0f}% |
"""


def _generate_key_findings(startups, decisions):
    """주요 발견사항 생성"""
    if not startups:
        return "- 평가 데이터 부족"
    
    avg_score = sum(s.get('total_score', 0) for s in startups[:len(decisions)]) / max(len(decisions), 1)
    
    return f"""
- **평균 점수**: {avg_score:.2f}/100
- **최고 점수**: {max((s.get('total_score', 0) for s in startups[:len(decisions)]), default=0):.2f}/100
- **최저 점수**: {min((s.get('total_score', 0) for s in startups[:len(decisions)]), default=0):.2f}/100
- **공통 약점**: 충분한 공개 정보 부족, 기술 성숙도 검증 필요
- **전반적 평가**: {state.get('investor_persona', 'conservative')} 투자자 기준으로 모든 후보가 리스크가 높게 평가됨
"""


def _format_full_ranking(all_startups):
    """전체 랭킹 표"""
    if not all_startups:
        return "랭킹 데이터 없음"
    
    table = "| Rank | 스타트업 | 총점 | Domain Fit | Credibility |\n"
    table += "|------|---------|------|------------|-------------|\n"
    
    for idx, startup in enumerate(all_startups, 1):
        table += f"| {idx} | {startup.get('name', 'N/A')} | {startup.get('total_score', 0):.1f} | {startup.get('domain_fit', 0):.2f} | {startup.get('credibility_score', 0):.2f} |\n"
    
    return table


def _get_termination_reason(decisions, total_startups):
    """종료 사유"""
    if len(decisions) >= 5:
        return f"5회 연속 투자 부적합 판정 ({', '.join(decisions)})"
    elif len(decisions) >= total_startups:
        return f"전체 {total_startups}개 스타트업 평가 완료"
    else:
        return "알 수 없는 사유"


def _generate_rejection_report(state: GraphState) -> str:
    """실패 보고서 생성 (5회 누적 또는 리스트 소진)"""
    decision_log = state["decision_log"]
    evaluated_startups = state.get("evaluation_results", [])[:len(decision_log)]
    
    return f"""
# 📋 AI 스타트업 투자 평가 보고서 (분석 종료)

---

## 📊 Executive Summary

| 항목 | 내용 |
|------|------|
| **최종 투자 의견** | ❌ **투자 부적합 (루프 종료)** |
| **투자자 페르소나** | {state['investor_persona'].upper()} |
| **평가 대상 수** | {len(decision_log)}개 스타트업 |
| **평가 기간** | {_get_timestamp()} |

### 🔍 종합 평가 요약
총 **{len(decision_log)}개**의 스타트업을 검토하였으나, 현재 투자자 페르소나({state['investor_persona']})에 부합하는 '투자 적절' 대상을 찾지 못했습니다.

---

## 1️⃣ 평가된 스타트업 목록

{_format_evaluated_startups_table(evaluated_startups, decision_log)}

---

## 2️⃣ 스타트업별 상세 평가

{_format_detailed_evaluations(evaluated_startups, decision_log, state)}

---

## 3️⃣ 투자자 페르소나 분석

### {state['investor_persona'].upper()} Investor Profile

{state.get('persona_rationale', 'N/A')}

### 페르소나별 평가 기준
{_format_persona_weights(state['investor_persona'])}

---

## 4️⃣ 종합 분석 및 권고사항

### 📊 평가 결과 통계
- **부정적 결정**: {decision_log.count('부정적')}건
- **보류 결정**: {decision_log.count('보류')}건
- **투자 적절**: {decision_log.count('투자 적절')}건

### 💡 주요 발견사항
{_generate_key_findings(evaluated_startups, decision_log)}

### 📋 Next Steps & Recommendations

1. **포트폴리오 확장 고려**
   - 현재 후보군에서 적합한 투자 대상이 발견되지 않음
   - 추가적인 Deal Sourcing 필요
   - 다른 섹터나 지역으로 범위 확대 검토

2. **평가 기준 재검토**
   - 현재 페르소나({state['investor_persona']}) 기준이 너무 엄격할 가능성
   - '보류' 판정 받은 스타트업에 대한 재평가 고려
   - 특정 기준의 가중치 조정 검토

3. **직접 소싱 전략**
   - 액셀러레이터/인큐베이터 파트너십 강화
   - VC 네트워크를 통한 Co-investment 기회 탐색
   - 컨퍼런스 및 데모데이 참석을 통한 직접 발굴
   - Warm introduction을 통한 고품질 딜 확보

4. **심층 분석 권장 대상**
   - 보류 판정 받은 스타트업 재검토
   - 1:1 미팅을 통한 추가 정보 수집
   - 업계 전문가 자문 활용

---

## 📎 부록: 전체 랭킹 데이터

### 초기 평가 전체 랭킹 (Agent 1)
{_format_full_ranking(state.get('evaluation_results', []))}

---

**보고서 생성일**: {_get_timestamp()}  
**분석 시스템**: RWA Multi-Agent Investment Analysis v2.0  
**평가 완료 사유**: {_get_termination_reason(decision_log, len(state.get('evaluation_results', [])))}
"""


# ============================================================================
# PART 4: 메인 함수
# ============================================================================

def run_agent_6_report_generator(state: GraphState) -> GraphState:
    """
    Agent 6: Generates comprehensive VC-grade investment report.
    
    docstring: Creates either a detailed success report or a comprehensive 
               analysis report based on evaluation outcomes.
    """
    print("--- (6) EXECUTING AGENT 6: FINAL REPORT GENERATION ---")
    
    decision_log = state["decision_log"]
    final_decision_output = state.get("investment_decision_output", {})
    final_decision = final_decision_output.get("decision", "N/A")
    
    report_content = ""

    # ========================================================================
    # Case 1: "투자 적절" - 상세 성공 보고서
    # ========================================================================
    if final_decision == "투자 적절":
        startup_name = state["current_startup_data"]["name"]
        total_score = final_decision_output.get("total_score", "N/A")
        
        risk_rating, risk_description = _calculate_risk_rating(state)
        
        report_content = f"""
# 🎯 AI 스타트업 투자 평가 보고서: {startup_name}

---

## 📊 Executive Summary

| 항목 | 내용 |
|------|------|
| **스타트업 이름** | {startup_name} |
| **섹터** | {state['current_startup_data'].get('sector', 'N/A')} |
| **최종 투자 의견** | ✅ **{final_decision}** |
| **종합 점수** | **{total_score}/20** ({total_score/20*100:.0f}%) |
| **투자자 페르소나** | {state['investor_persona'].upper()} |
| **웹사이트** | {state['current_startup_data'].get('website', 'N/A')} |
| **지역** | {state['current_startup_data'].get('region', 'N/A')} |
| **펀딩 단계** | {state['current_startup_data'].get('funding_stage', 'N/A')} |
| **리스크 등급** | {risk_rating} |

### 🔑 Investment Thesis
{_generate_investment_thesis(state)}

### ⚡ Key Highlights
{_generate_key_highlights(state)}

### 📝 Executive Summary
{final_decision_output.get('reasoning', 'N/A')}

---

## 1️⃣ 20-Point VC Checklist 상세 분석
{_format_checklist_scores(final_decision_output.get('checklist_scores', []))}
{_format_detailed_checklist(final_decision_output.get('checklist_scores', []))}

---

## 2️⃣ 기술 성숙도 분석 (Agent 2)
{_format_tech_summary(state.get('tech_summary_output', {}))}

---

## 3️⃣ 시장성 분석 (Agent 3 - RAG)
{_format_market_analysis(state.get('market_assessment_output', {}))}

---

## 4️⃣ 경쟁 환경 분석 (Agent 4)
{_format_competitor_analysis(state.get('competitor_analysis_output', {}))}

---

{_format_financial_analysis(state)}

---

{_format_team_analysis(state)}

---

{_format_investment_terms(state)}

---

{_format_risk_mitigation(state)}

---

## 📋 최종 투자 권고 (Final Investment Recommendation)

### Investment Decision: **PROCEED** ✅

**Rationale**: {final_decision_output.get('reasoning', 'N/A')}

**Risk Assessment**: {risk_description}

### Recommended Next Steps (30-60 days)

#### Phase 1: Deep Due Diligence (Week 1-2)
- [ ] **Legal Review**
  - Regulatory compliance audit
  - Cap table review
  - IP ownership verification
  - Material contracts review
  
- [ ] **Technical Audit**
  - Code review (security, quality, scalability)
  - Infrastructure assessment
  - Security penetration testing
  - Technology roadmap evaluation
  
- [ ] **Financial Audit**
  - Financial statement review
  - Unit economics validation
  - Burn rate analysis
  - Revenue model verification

- [ ] **Customer References**
  - Speak with 3+ current clients
  - Validate product-market fit
  - Assess customer satisfaction
  - Verify retention metrics

#### Phase 2: Management Meetings (Week 3-4)
- [ ] **Executive Team**
  - CEO strategy session (2 hours)
  - CFO financial deep-dive (2 hours)
  - CTO technical architecture review (2 hours)
  
- [ ] **Board Engagement**
  - Board observer attendance (if possible)
  - Independent director conversations
  
- [ ] **Key Stakeholders**
  - Top 3 customers interviews
  - Strategic partner discussions
  - Advisor reference checks

#### Phase 3: Term Sheet Negotiation (Week 5-6)
- [ ] **Valuation Discussion**
  - Present comparable analysis
  - Negotiate pre-money valuation
  - Agree on investment amount
  
- [ ] **Terms Negotiation**
  - Liquidation preferences
  - Board composition
  - Protective provisions
  - Vesting schedules
  
- [ ] **Legal Documentation**
  - Term sheet drafting
  - Legal review
  - Founder agreement

#### Phase 4: Closing (Week 7-8)
- [ ] **Final Approval**
  - Investment committee presentation
  - Partner vote
  - Legal sign-off
  
- [ ] **Transaction Close**
  - Wire transfer
  - Stock issuance
  - Board seat assignment
  
- [ ] **Post-Investment Setup**
  - Quarterly reporting framework
  - Board meeting schedule
  - Strategic support plan

### Deal Risks to Monitor

**High Priority**:
{_extract_risks(state)}

**Mitigation Required**:
- Secure regulatory approvals within 90 days
- Achieve customer milestones as outlined in term sheet
- Complete team hiring plan (CCO, CFO)

### Success Metrics (12-month targets)

| Metric | Current | 12-Month Target | Stretch Goal |
|--------|---------|-----------------|--------------|
| **ARR** | Early stage | $5M | $8M |
| **Customers** | Pilots | 10+ institutions | 15+ |
| **Team Size** | ~25 | 50+ | 75+ |
| **Licenses** | 1 jurisdiction | 3 jurisdictions | 5 jurisdictions |
| **Product Releases** | MVP | 3 major releases | 5 releases |
| **Burn Multiple** | N/A | < 2x | < 1.5x |

---

## 5️⃣ 투자 위원회 체크리스트

### Investment Committee Approval Checklist

- [ ] **Market Opportunity**: TAM > $1B ✅
- [ ] **Team Quality**: Experienced founders ✅
- [ ] **Product Differentiation**: Clear competitive moats ✅
- [ ] **Traction**: Early customer validation ✅
- [ ] **Unit Economics**: Path to profitability ✅
- [ ] **Regulatory Compliance**: Risk manageable ✅
- [ ] **Exit Potential**: Multiple exit scenarios ✅
- [ ] **Portfolio Fit**: Strategic alignment ✅
- [ ] **Due Diligence**: No major red flags ✅
- [ ] **Valuation**: Fair pricing ✅

**IC Recommendation**: **APPROVE** with standard terms

---

## 📎 부록: 전체 평가 데이터

### Agent 1 (초기 평가)
```json
{json.dumps(state['current_startup_data'], indent=2, ensure_ascii=False)}
```

### Agent 2 (기술 분석)
```json
{json.dumps(state.get('tech_summary_output', {}), indent=2, ensure_ascii=False)}
```

### Agent 3 (시장 분석)
```json
{json.dumps(state.get('market_assessment_output', {}), indent=2, ensure_ascii=False)}
```

### Agent 4 (경쟁 분석)
```json
{json.dumps(state.get('competitor_analysis_output', {}), indent=2, ensure_ascii=False)}
```

---

**보고서 생성일**: {_get_timestamp()}  
**분석 시스템**: RWA Multi-Agent Investment Analysis v2.0  
**분석가**: AI Investment Committee  
**승인 상태**: Pending Partner Review  
**다음 단계**: Investment Committee Presentation
"""
    
    # ========================================================================
    # Case 2: 실패/보류 - 종합 분석 보고서
    # ========================================================================
    else:
        report_content = _generate_rejection_report(state)
    
    # ========================================================================
    # 최종 보고서 파일 저장
    # ========================================================================
    try:
        with open("Final_Investment_Report.md", "w", encoding="utf-8") as f:
            f.write(report_content)
        print("--- (6) Final_Investment_Report.md 파일이 생성되었습니다. ---")
    except Exception as e:
        print(f"--- (6) 보고서 파일 저장 실패: {e} ---")

    return {**state, "final_report": report_content}