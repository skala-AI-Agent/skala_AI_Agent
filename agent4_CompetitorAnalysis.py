# FILE: agent4.py
# (Agent 4: Competitor Analysis)

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers.json import JsonOutputParser

# 공유 자원 및 상태 import
from graph_state import GraphState
from config import llm, simple_web_search  # 수정

def run_agent_4_competitor_analysis(state: GraphState) -> GraphState:
    """Agent 4: Performs competitor analysis using web search."""
    startup_name = state["current_startup_data"]["name"]
    segment = state["current_startup_data"]["sector"]
    print(f"--- (4) EXECUTING AGENT 4: COMPETITOR ANALYSIS for {startup_name} ---")

    search_query = f"main competitors for {startup_name} in {segment}"
    search_results = simple_web_search(search_query, max_results=5)  # 수정
    context = "\n".join([res.get("content", "") for res in search_results])

    prompt = ChatPromptTemplate.from_template("""
You are a strategy consultant. Identify 2-3 main competitors for '{startup_name}' based on context.
Provide a brief SWOT (Strengths, Weaknesses) analysis for each competitor relative to {startup_name}.
Return only JSON.
Context: {context}
{{
    "competitors": [
        {{"name": "Competitor A", "swot": "Strength: ..., Weakness: ..."}},
        {{"name": "Competitor B", "swot": "Strength: ..., Weakness: ..."}}
    ]
}}
    """)
    
    chain = prompt | llm | JsonOutputParser()
    try:
        output = chain.invoke({"startup_name": startup_name, "context": context})
    except Exception as e:
        print(f"--- (4) Competitor Analysis Error: {e} ---")
        output = {"error": str(e)}

    return {**state, "competitor_analysis_output": output}