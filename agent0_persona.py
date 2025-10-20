# FILE: agent0.py
# (Agent 0: Persona Assessment)

from typing import Dict, Any
from langchain_core.messages import AIMessage, HumanMessage
from graph_state import GraphState # 공유 상태 import

# --- Agent 0 Constants ---
PERSONA_WEIGHTS = {
    "aggressive": {
        "seed_early": 0.40, "regional_esg": 0.15,
        "growth_partnership": 0.35, "regulation_monetization": 0.10
    },
    "conservative": {
        "seed_early": 0.10, "regional_esg": 0.30,
        "growth_partnership": 0.20, "regulation_monetization": 0.40
    }
}

def run_agent_0_persona(state: GraphState) -> GraphState:
    """
    Agent 0: Assesses VC investor's investment persona via CLI input.
    
    docstring: Asks the user 5 questions to determine their investment persona.
    """
    
    questions = [
        "1. Do you pursue high returns even with high risk? (1-5)",
        "2. How much experience do you have investing in early-stage (Seed/Series A) startups? (1-5)",
        "3. How important is a stable revenue model and cash flow? (1-5)",
        "4. How much do you consider ESG (Environmental, Social, Governance) factors in investment decisions? (1-5)",
        "5. Do you prefer rapid growth or stable growth? (1: Stable, 5: Rapid)"
    ]
    
    print("\n" + "="*70)
    print("🏦 VC INVESTMENT PERSONA ASSESSMENT (AGENT 0)")
    print("="*70)
    print("\nPlease answer the following questions (Scale 1-5):\n")
    
    answers = {}
    for question in questions:
        print(question)
        while True:
            try:
                answer = int(input("Answer: "))
                if 1 <= answer <= 5:
                    answers[question] = answer
                    break
                else:
                    print("Please enter a number between 1-5.")
            except ValueError:
                print("Please enter a number.")
    
    # 페르소나 결정 로직
    risk_score = answers[questions[0]]
    experience_score = answers[questions[1]]
    stability_score = answers[questions[2]]
    esg_score = answers[questions[3]]
    growth_score = answers[questions[4]]
    
    aggressive_score = (risk_score + experience_score + growth_score) / 3
    conservative_score = (stability_score + esg_score + (6 - growth_score)) / 3
    
    if aggressive_score > conservative_score:
        persona = "aggressive"
        weights = PERSONA_WEIGHTS["aggressive"]
        rationale = f"[INVESTOR PERSONA ANALYSIS: AGGRESSIVE INVESTOR]\n"
    else:
        persona = "conservative"
        weights = PERSONA_WEIGHTS["conservative"]
        rationale = f"[INVESTOR PERSONA ANALYSIS: CONSERVATIVE INVESTOR]\n"
    
    # (간결성을 위해 상세 근거 문구는 생략)
    print("\n" + "="*70)
    print(rationale.strip())
    print(f"✅ 페르소나: {persona.upper()}")
    print("="*70 + "\n")
    
    # 상태 업데이트
    return {
        **state,
        "investor_persona": persona,
        "persona_rationale": rationale,
        "decision_log": [], # 의사결정 로그 초기화
    }