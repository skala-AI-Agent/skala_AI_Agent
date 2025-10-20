# FILE: control_flow.py
# (루프 및 조건부 분기 로직) - 방어적 코딩 추가

from typing import Literal
from graph_state import GraphState

def select_next_startup(state: GraphState) -> GraphState:
    """Selects the next startup from the ranking list to evaluate."""
    current_index = state["current_startup_index"] + 1
    
    if current_index >= len(state["evaluation_results"]):
        print("--- (CTRL) 더 이상 분석할 스타트업이 없습니다. 루프를 종료합니다. ---")
        return {**state, "current_startup_index": -1} 
        
    current_startup = state["evaluation_results"][current_index]
    print(f"--- (CTRL) 다음 스타트업(Rank {current_index + 1})으로 이동: {current_startup['name']} ---")
    
    return {
        **state,
        "current_startup_index": current_index,
        "current_startup_data": current_startup,
    }


def should_loop_or_stop(state: GraphState) -> Literal["generate_report", "select_next"]:
    """
    Determines the next step based on the investment decision and loop count.
    
    docstring: Checks the decision from Agent 5 with safe key access.
    """
    # 안전한 키 접근
    decision_output = state.get("investment_decision_output", {})
    decision = decision_output.get("decision", "부정적")
    
    # 1. "투자 적절" (성공) -> 즉시 보고서 생성 후 종료
    if decision == "투자 적절":
        print("--- (COND) 결정: '투자 적절'. 보고서를 생성하고 종료합니다. ---")
        return "generate_report"
    
    # 2. "보류" 또는 "부정적"
    decision_log = state.get("decision_log", [])
    hold_reject_count = len(decision_log)
    
    # 5회 누적 (실패) -> 보고서 생성 후 종료
    if hold_reject_count >= 5:
        print(f"--- (COND) 결정: '{decision}'. 5회 누적({hold_reject_count}회)되어 종료합니다. ---")
        return "generate_report"
        
    # 3. 5회 미만 -> 다음 스타트업 선택 로직으로 이동
    print(f"--- (COND) 결정: '{decision}'. 5회 미만({hold_reject_count}회). 다음 스타트업을 확인합니다. ---")
    return "select_next"


def check_remaining_startups(state: GraphState) -> Literal["generate_report", "loop_to_agent_2"]:
    """
    Checks if there are more startups left after 'select_next_startup'.
    
    docstring: Checks the index to route to Agent 2 or the report.
    """
    if state["current_startup_index"] == -1: 
        print("--- (COND) 모든 스타트업 분석 완료. 최종 보고서로 이동합니다. ---")
        return "generate_report"
    else:
        return "loop_to_agent_2"