# FILE: agent5.py
# (Agent 5: Investment Decision) - 완전 수정

import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers.json import JsonOutputParser

from graph_state import GraphState
from config import llm, VC_CHECKLIST


# === Helper Functions (함수 정의를 맨 위로 이동) ===

def _summarize_strengths(scores, checklist):
    """강점 요약 (PASS 항목)"""
    strengths = [checklist[i].split(":")[0].replace(f"{i+1}. ", "") 
                 for i, score in enumerate(scores) if score == 1]
    return ", ".join(strengths[:3]) if strengths else "None identified"


def _summarize_weaknesses(scores, checklist):
    """약점 요약 (FAIL 항목)"""
    weaknesses = [checklist[i].split(":")[0].replace(f"{i+1}. ", "") 
                  for i, score in enumerate(scores) if score == 0]
    return ", ".join(weaknesses[:3]) if weaknesses else "None identified"


# === Main Function ===

def run_agent_5_decision(state: GraphState) -> GraphState:
    """
    Agent 5: Makes the final investment decision using the 20-Point VC Checklist.
    
    docstring: Improved evaluation logic with proper error handling.
    """
    startup_name = state["current_startup_data"]["name"]
    print(f"--- (5) EXECUTING AGENT 5: INVESTMENT DECISION for {startup_name} ---")

    # 기본값 설정 (오류 발생 시에도 상태 반환 가능하도록)
    default_output = {
        "total_score": 0,
        "decision": "보류",
        "reasoning": "Evaluation incomplete due to technical error.",
        "checklist_scores": [0] * 20
    }

    try:
        # 모든 에이전트 데이터 취합
        full_context = f"""
        ### Startup Overview (Agent 1)
        {json.dumps(state['current_startup_data'], indent=2, ensure_ascii=False)}
        
        ### Technical Analysis (Agent 2)
        {json.dumps(state.get('tech_summary_output', {}), indent=2, ensure_ascii=False)}
        
        ### Market Assessment (Agent 3)
        {json.dumps(state.get('market_assessment_output', {}), indent=2, ensure_ascii=False)}
        
        ### Competitive Landscape (Agent 4)
        {json.dumps(state.get('competitor_analysis_output', {}), indent=2, ensure_ascii=False)}
        """
        
        checklist_prompt = "\n".join([f"{i}. {q}" for i, q in enumerate(VC_CHECKLIST, 1)])
        
        prompt = ChatPromptTemplate.from_template(
            """
            You are a senior VC partner evaluating an early-stage RWA (Real-World Asset) startup.
            
            **CRITICAL EVALUATION GUIDELINES:**
            1. For early-stage companies, LACK OF PUBLIC DATA ≠ FAILURE
            2. Score based on POTENTIAL and INDICATORS, not just proven metrics
            3. If Agent 2 shows tech_maturity > 0.5, consider Question 6 as PASS (1)
            4. If Agent 2 shows credibility > 0.6, consider Question 16 as PASS (1)
            5. If Agent 2 shows compliance_risk < 0.35, consider Question 18 as PASS (1)
            6. If Agent 2 shows ecosystem > 0.6, consider Question 13 as PASS (1)
            7. For RWA sector, regulatory awareness is critical but perfection is not expected
            8. Strong fundamentals (market, team, tech) should outweigh missing traction data
            
            **Your Task:**
            Answer 0 (No/Weak) or 1 (Yes/Strong) for each of the 20 questions.
            **Be reasonably optimistic for promising early-stage startups.**
            
            ### Complete Data Context ###
            {context}
            
            ### VC 20-Point Checklist ###
            {checklist}
            
            **Output Format (JSON only):**
            {{
                "scores": [1, 0, 1, ..., 1],
                "reasoning": "Concise 2-3 sentence evaluation summary."
            }}
            """
        )
        
        chain = prompt | llm | JsonOutputParser()
        
        response_json = chain.invoke({"context": full_context, "checklist": checklist_prompt})
        scores = response_json.get("scores", [0]*20)
        
        # 점수 검증 및 보정
        if len(scores) != 20:
            print(f"    ⚠️ 점수 개수 오류 ({len(scores)}개). 20개로 보정.")
            scores = scores[:20] + [0] * (20 - len(scores))
        
        total_score = sum(scores)
        reasoning = response_json.get("reasoning", "")
        
        # 의사결정 로직
        if total_score >= 15:  # 75% 이상
            decision = "투자 적절"
        elif total_score >= 12:  # 60% 이상
            decision = "보류"
        else:
            decision = "부정적"
            
        print(f"--- (5) 결정: {decision} (점수: {total_score}/20) ---")
        
        # 상세 분석 출력 (헬퍼 함수 사용)
        if total_score >= 12:
            try:
                strengths_summary = _summarize_strengths(scores, VC_CHECKLIST)
                print(f"    💡 Key Strengths: {strengths_summary}")
            except Exception as e:
                print(f"    ⚠️ 강점 요약 실패: {e}")
        
        if total_score < 15:
            try:
                weaknesses_summary = _summarize_weaknesses(scores, VC_CHECKLIST)
                print(f"    ⚠️ Areas of Concern: {weaknesses_summary}")
            except Exception as e:
                print(f"    ⚠️ 약점 요약 실패: {e}")

        output = {
            "total_score": total_score,
            "decision": decision,
            "reasoning": reasoning,
            "checklist_scores": scores
        }

    except Exception as e:
        print(f"--- (5) Decision Error: {e} ---")
        import traceback
        traceback.print_exc()
        
        # 오류 발생 시에도 기본 출력 사용
        output = default_output
    
    # 의사결정 로그에 현재 결정 추가
    new_log = state.get("decision_log", []) + [output["decision"]]

    return {
        **state,
        "investment_decision_output": output,
        "decision_log": new_log
    }