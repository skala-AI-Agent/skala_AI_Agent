# FILE: agent1.py
# (Agent 1: Startup Search & Ranking) - search_query 정의 추가

import json
import re
import os
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

# 공유 자원 및 상태 import
from graph_state import GraphState
from config import llm_mini, simple_web_search  # web_search 대신
from agent0 import PERSONA_WEIGHTS # Agent 0의 가중치 사용

# --- Agent 1 Constants ---
EVALUATION_CRITERIA = {
    "seed_early": {"name": "Seed/Early Stage", "description": "초기 단계 혁신성 및 잠재력"},
    "regional_esg": {"name": "Regional/ESG", "description": "지역 영향력 및 ESG 관련성"},
    "growth_partnership": {"name": "Growth + Partnership", "description": "성장률, 잠재력, 파트너십"},
    "regulation_monetization": {"name": "Regulation/Monetization", "description": "규제 적응성, 수익 모델"}
}

# --- 프롬프트 템플릿 ---
EVAL_TEMPLATE_STRING = """
You are a VC analyst. Evaluate the startup (0-100) based on criteria. Return JSON only.
Criteria: {criteria_json}

Context:
{context}

Respond with *only* the JSON object, nothing else.
Example:
{{
    "seed_early": {{"score": 0, "rationale": "..."}},
    "regional_esg": {{"score": 0, "rationale": "..."}},
    "growth_partnership": {{"score": 0, "rationale": "..."}},
    "regulation_monetization": {{"score": 0, "rationale": "..."}}
}}
"""
eval_prompt = ChatPromptTemplate.from_template(EVAL_TEMPLATE_STRING)
criteria_json_str = json.dumps(EVALUATION_CRITERIA, indent=2, ensure_ascii=False)


def _agent1_extract_additional_info(startup_name: str, search_results: list) -> dict:
    """Helper function for Agent 1 to extract structured info from search."""
    if not isinstance(search_results, list):
        print(f"      정보 추출 건너뜀: search_results가 리스트가 아님 (Type: {type(search_results)})")
        return {"website": "Unknown", "region": "Unknown", "funding_stage": "Unknown"}

    search_context = "\n".join([
        (res.get('content', '') if isinstance(res, dict) else str(res))
        for res in search_results
    ])

    extraction_prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""
You are a data extraction expert. Extract website (https://...), region (USA, Asia...),
and funding_stage (Seed, Series A...) from the search results.
If info is unavailable, infer reasonably. Return JSON only.
{ "website": "...", "region": "...", "funding_stage": "..." }
        """),
        HumanMessage(content=f"Company: {startup_name}\nSearch Results:\n{search_context}\n\nExtract info.")
    ])

    try:
        response = llm_mini.invoke(extraction_prompt.format_messages())
        content = response.content.strip()
        if content.startswith("```"):
            content = re.sub(r"```(json)?", "", content).strip()
        return json.loads(content)
    except Exception as e:
        print(f"      정보 추출 실패: {str(e)}")
        return {"website": "Unknown", "region": "Unknown", "funding_stage": "Unknown"}

# run_agent_1_search 함수에서 검색 부분만 수정
def run_agent_1_search(state: GraphState) -> GraphState:
    """Agent 1: Searches and ranks startups based on persona."""
    print("\n" + "="*70)
    print("🔍 STARTUP SEARCH & EVALUATION (AGENT 1)")
    print("="*70 + "\n")

    persona = state["investor_persona"]
    weights = PERSONA_WEIGHTS[persona]

    try:
        with open('startups.json', 'r', encoding='utf-8') as f:
            startup_list = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("startups.json 파일이 없습니다. 프로젝트 루트에 생성해주세요.")

    print(f"✅ 페르소나: {persona.upper()}. {len(startup_list)}개 스타트업 평가 시작.")

    evaluation_results = []

    for idx, startup in enumerate(startup_list, 1):
        startup_name = startup['name']
        print(f"📊 [{idx}/{len(startup_list)}] 평가 중: {startup_name}")

        search_context = "Search unavailable."
        additional_info = {"website": "Unknown", "region": "Unknown", "funding_stage": "Unknown"}
        search_results_list = []

        search_query = f"{startup_name} blockchain tokenization official website funding"

        try:
            # simple_web_search 사용
            search_results = simple_web_search(search_query, max_results=5)
            
            if isinstance(search_results, list) and search_results:
                search_results_list = search_results
                search_context = "\n".join([
                    (res.get('content', '') if isinstance(res, dict) else str(res))[:200]
                    for res in search_results
                ])
            else:
                search_context = "Limited search results."

            additional_info = _agent1_extract_additional_info(startup_name, search_results_list)

        except Exception as e:
            print(f"    ⚠️ 검색 또는 처리 실패: {type(e).__name__}: {str(e)}")

        combined_context = f"Info: {startup['strength']}\nSearch: {search_context}"

        content = ""
        try:
            messages = eval_prompt.format_messages(
                criteria_json=criteria_json_str,
                context=combined_context
            )

            response = llm_mini.invoke(messages)
            content = response.content.strip()

            if content.startswith("```"):
                content = re.sub(r"```(json)?", "", content).strip()

            scores_data = json.loads(content)

            total_score = sum(
                scores_data[criterion]["score"] * weights[criterion]
                for criterion in weights.keys()
            )

            domain_fit = (scores_data["seed_early"]["score"] + scores_data["growth_partnership"]["score"]) / 200
            credibility_score = (scores_data["regulation_monetization"]["score"] + scores_data["regional_esg"]["score"]) / 200

            evaluation_results.append({
                "name": startup_name,
                "sector": startup['sector'],
                "strength": startup['strength'],
                **additional_info,
                "scores": scores_data,
                "total_score": round(total_score, 2),
                "domain_fit": round(domain_fit, 2),
                "credibility_score": round(credibility_score, 2),
                "final_score": round(total_score / 100, 2),
            })
            print(f"    ✓ 총점: {total_score:.2f}/100")

        except Exception as e:
            print(f"    ⚠️ 평가 실패: {str(e)} | Raw: {content[:100]}...")

    if not evaluation_results:
        raise Exception("성공적으로 평가된 스타트업이 없습니다.")

    evaluation_results.sort(key=lambda x: x["total_score"], reverse=True)

    print("\n" + "="*70)
    print("📋 전체 랭킹 (AGENT 1)")
    for i, res in enumerate(evaluation_results):
        print(f"  {i+1:2d}. {res['name']:20s} {res['total_score']:6.2f} pts")
    print("="*70 + "\n")

    current_index = 0
    current_startup = evaluation_results[current_index]

    print(f"--- (1) 1순위 스타트업 선정: {current_startup['name']} ---")

    return {
        **state,
        "evaluation_results": evaluation_results,
        "current_startup_index": current_index,
        "current_startup_data": current_startup,
    }