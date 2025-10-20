# FILE: main.py
# (메인 그래프 빌더 및 실행기)

import os
from langgraph.graph import StateGraph, END

# --- 모든 구성요소 Import ---
from graph_state import GraphState
from config import llm, llm_mini, web_search # (필요시)
from agent0 import run_agent_0_persona
from agent1 import run_agent_1_search
from agent2 import build_agent2_graph # Agent 2는 그래프 빌더를 import
from agent3 import run_agent_3_market_rag
from agent4 import run_agent_4_competitor_analysis
from agent5 import run_agent_5_decision
from agent6 import run_agent_6_report_generator
from control_flow import select_next_startup, should_loop_or_stop, check_remaining_startups

# --- Agent 2 서브그래프 미리 컴파일 ---
agent2_app = build_agent2_graph()
print("✅ Agent 2 (TechSummary) 서브그래프가 컴파일되었습니다.")

# --- Agent 2 래퍼(Wrapper) 노드 ---
# 메인 그래프는 Agent 2의 서브그래프를 호출할 래퍼 노드가 필요합니다.
def run_agent_2_tech_summary_wrapper(state: GraphState) -> GraphState:
    """
    Wrapper node to execute the compiled Agent 2 sub-graph.
    
    docstring: This node formats the input for the Agent 2 sub-graph,
               invokes it, and places the output back into the main GraphState.
    """
    current_startup = state["current_startup_data"]
    startup_name = current_startup["name"]
    print(f"--- (2) EXECUTING AGENT 2: TECH SUMMARY for {startup_name} ---")

    # Agent 1의 출력을 Agent 2의 입력 형식으로 포맷팅
    agent2_input = {
        "name": current_startup["name"],
        "website": current_startup["website"],
        "segment": current_startup["sector"],
        "region": current_startup["region"],
        "funding_stage": current_startup["funding_stage"],
        "domain_fit": current_startup.get("domain_fit", 0.5),
        "credibility_score": current_startup.get("credibility_score", 0.5),
        "final_score": current_startup.get("final_score", 0.5),
        "reason": f"Selected by Agent 1 (Rank {state['current_startup_index'] + 1})"
    }
    
    # 컴파일된 Agent 2 그래프 실행
    agent2_result_state = agent2_app.invoke(
        {"startup_json": agent2_input}, 
        {"recursion_limit": 10} # Agent 2 내부 루프 방지
    )
    
    return {
        **state,
        "tech_summary_output": agent2_result_state.get("output_payload", {})
    }


# --- 메인 그래프 빌드 ---
def build_main_graph():
    """
    Builds and compiles the complete multi-agent workflow.
    
    docstring: Imports all agent nodes and control flow nodes,
               then wires them together into the main StateGraph.
    """
    workflow = StateGraph(GraphState)

    # 1. 에이전트 노드 추가
    workflow.add_node("agent_0_persona", run_agent_0_persona)
    workflow.add_node("agent_1_search", run_agent_1_search)
    workflow.add_node("agent_2_tech", run_agent_2_tech_summary_wrapper) # 래퍼 노드 사용
    workflow.add_node("agent_3_market", run_agent_3_market_rag)
    workflow.add_node("agent_4_competitor", run_agent_4_competitor_analysis)
    workflow.add_node("agent_5_decision", run_agent_5_decision)
    workflow.add_node("agent_6_report", run_agent_6_report_generator)
    
    # 2. 루프 제어 노드 추가
    workflow.add_node("select_next_startup", select_next_startup)

    # 3. 엣지 연결
    workflow.set_entry_point("agent_0_persona")
    workflow.add_edge("agent_0_persona", "agent_1_search")
    workflow.add_edge("agent_1_search", "agent_2_tech") # 1순위 스타트업으로 분석 시작
    
    # 심층 분석 파이프라인 (2 -> 3 -> 4 -> 5)
    workflow.add_edge("agent_2_tech", "agent_3_market")
    workflow.add_edge("agent_3_market", "agent_4_competitor")
    workflow.add_edge("agent_4_competitor", "agent_5_decision")

    # 4. 조건부 분기 (핵심 로직)
    workflow.add_conditional_edges(
        "agent_5_decision",
        should_loop_or_stop,
        {
            "generate_report": "agent_6_report", # (성공 또는 5회 실패 시)
            "select_next": "select_next_startup" # (다음 루프 준비)
        }
    )
    
    # 5. 다음 스타트업 선택 후 분기
    workflow.add_conditional_edges(
        "select_next_startup",
        check_remaining_startups,
        {
            "generate_report": "agent_6_report", # (스타트업 소진 시)
            "loop_to_agent_2": "agent_2_tech"   # (Agent 2부터 다시 시작)
        }
    )

    workflow.add_edge("agent_6_report", END)
    
    return workflow.compile()

# --- 그래프 실행 ---
if __name__ == "__main__":
    print("🚀 Building RWA Multi-Agent Investment Graph (Modular)...")

    if not os.path.exists("startups.json"):
        print("="*70)
        print("🚨 Error: 'startups.json' 파일이 없습니다.")
        print("프로젝트 디렉토리에 'startups.json' 파일을 생성한 후 다시 실행해주세요.")
        print("="*70)
    else:
        app = build_main_graph()
        
        print("\n🏃‍♂️ Running Graph...")
        print("Agent 0 (페르소나 진단)이 사용자 입력을 기다립니다.")
        
        initial_state = {} # 초기 상태는 비워둡니다.
        
        # 스트리밍 실행
        for event in app.stream(initial_state, {"recursion_limit": 50}):
            (node, state) = event.popitem()
            print(f"--- Finished Node: {node} ---")
            if "final_report" in state and state["final_report"]:
                print("🏁 워크플로우가 완료되었습니다. Final_Investment_Report.md를 확인하세요.")

        print("\n✅ Main graph execution complete.")